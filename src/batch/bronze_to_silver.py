import sys
import os

# --- PATH HACK (For Local Imports) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, last, first, when, lit, coalesce, unix_timestamp, 
    sin, cos, atan2, radians, degrees
)
from pyspark.sql.window import Window
from streaming.schema import weather_schema 

def main():
    spark = SparkSession.builder \
        .appName("BronzeToSilver_Simplified") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # 1. READ BRONZE STREAM
    bronze_df = spark.readStream \
        .schema(weather_schema) \
        .parquet("/weather/bronze")

    # --- CONFIGURATION: PHYSICAL LIMITS ---
    PHYSICAL_LIMITS = [
        ("temperature_2m", -95, 65),
        ("relative_humidity_2m", 0, 105),
        ("pressure_msl", 850, 1100),
        ("surface_pressure", 500, 1100),
        ("wind_speed_10m", 0, 450),
        ("wind_speed_100m", 0, 450),
        ("wind_gusts_10m", 0, 450),
        ("wind_direction_10m", 0, 360),
        ("wind_direction_100m", 0, 360),
        ("cloud_cover", 0, 100),
        ("cloud_cover_low", 0, 100),
        ("cloud_cover_mid", 0, 100),
        ("cloud_cover_high", 0, 100),
        ("soil_temperature_0_to_7cm", -50, 75),
        ("soil_temperature_7_to_28cm", -40, 60),
        ("soil_temperature_28_to_100cm", -30, 50),
        ("soil_temperature_100_to_255cm", -20, 40),
        ("soil_moisture_0_to_7cm", -0.05, 1.05),
        ("soil_moisture_7_to_28cm", -0.05, 1.05),
        ("soil_moisture_28_to_100cm", -0.05, 1.05),
        ("soil_moisture_100_to_255cm", -0.05, 1.05),
        ("precipitation", 0, 400),
        ("rain", 0, 400),
        ("snowfall", 0, 500),
        ("snow_depth", 0, 10000)
    ]

    def process_and_split(batch_df, batch_id):
        # Optimization: Check if batch is empty immediately
        if batch_df.isEmpty():
            return

        print(f"--- Processing Batch {batch_id} ---")
        batch_df.cache()

        # -----------------------------------------------
        # STEP 1: DEDUPLICATE & NULLIFY OUTLIERS
        # -----------------------------------------------
        # We do this in one pass to avoid multiple cache updates
        cleaned_df = batch_df.dropDuplicates(["location_id", "time"])
        
        # Apply Nullification Loop (Very fast, map-only operation)
        for col_name, min_val, max_val in PHYSICAL_LIMITS:
            if col_name in cleaned_df.columns:
                cleaned_df = cleaned_df.withColumn(col_name, 
                    when(
                        (col(col_name) < min_val) | (col(col_name) > max_val), 
                        lit(None)
                    ).otherwise(col(col_name))
                )

        # -----------------------------------------------
        # STEP 2: TEMPORAL IMPUTATION (Unified)
        # -----------------------------------------------
        # Prepare Time Columns
        df_with_ts = cleaned_df.withColumn("event_ts", col("time").cast("timestamp")) \
                               .withColumn("event_unix", unix_timestamp("event_ts")) \
                               .withColumn("imputed_flag", lit(False))

        # Define ONE Window for everything (Reduces Shuffles)
        w = Window.partitionBy("location_id").orderBy("event_ts")
        w_future = w.rowsBetween(0, Window.unboundedFollowing)
        
        # List of columns that behave linearly (Precipitation is now here too)
        linear_cols = [
            "temperature_2m", "dew_point_2m", "apparent_temperature",
            "relative_humidity_2m", "pressure_msl", "surface_pressure",
            "cloud_cover", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high",
            "wind_speed_10m", "wind_speed_100m", "wind_gusts_10m",
            "soil_temperature_0_to_7cm", "soil_temperature_7_to_28cm", 
            "soil_temperature_28_to_100cm", "soil_temperature_100_to_255cm",
            "soil_moisture_0_to_7cm", "soil_moisture_7_to_28cm", 
            "soil_moisture_28_to_100cm", "soil_moisture_100_to_255cm",
            "precipitation", "rain", "snowfall", "snow_depth"
        ]

        # [Logic: Universal Linear Interpolation]
        # We calculate Forward Fill and Backward Fill for ALL linear columns
        for c in linear_cols:
            ff_val = last(col(c), ignorenulls=True).over(w)
            bf_val = first(col(c), ignorenulls=True).over(w_future)
            
            # Times for weighting
            ff_time = last(when(col(c).isNotNull(), col("event_unix")), ignorenulls=True).over(w)
            bf_time = first(when(col(c).isNotNull(), col("event_unix")), ignorenulls=True).over(w_future)

            # Interpolate
            interpolated = when(col(c).isNotNull(), col(c)) \
                .otherwise(
                    when(ff_val.isNotNull() & bf_val.isNotNull() & (ff_time != bf_time),
                         ff_val + (col("event_unix") - ff_time) * (bf_val - ff_val) / (bf_time - ff_time)
                    ).otherwise(coalesce(ff_val, bf_val))
                )
            
            # Apply and Flag
            df_with_ts = df_with_ts.withColumn("imputed_flag", 
                when(col(c).isNull() & interpolated.isNotNull(), lit(True))
                .otherwise(col("imputed_flag"))
            ).withColumn(c, interpolated)

        # [Logic: Circular Interpolation for Wind Direction]
        for dir_col in ["wind_direction_10m", "wind_direction_100m"]:
            dir_was_null = col(dir_col).isNull()
            
            # Decompose to Vectors
            df_with_ts = df_with_ts.withColumn(f"{dir_col}_rad", radians(col(dir_col))) \
                                   .withColumn(f"{dir_col}_x", cos(col(f"{dir_col}_rad"))) \
                                   .withColumn(f"{dir_col}_y", sin(col(f"{dir_col}_rad")))

            # Interpolate Vectors
            for component in ["_x", "_y"]:
                comp_col = f"{dir_col}{component}"
                ff_val = last(col(comp_col), ignorenulls=True).over(w)
                bf_val = first(col(comp_col), ignorenulls=True).over(w_future)
                
                # Simple Coalesce/Average for vectors is usually sufficient for stability
                interpolated = coalesce(col(comp_col), ff_val, bf_val, lit(0.0))
                df_with_ts = df_with_ts.withColumn(comp_col, interpolated)

            # Recompose
            df_with_ts = df_with_ts.withColumn(dir_col, 
                (degrees(atan2(col(f"{dir_col}_y"), col(f"{dir_col}_x"))) + 360) % 360
            )
            
            df_with_ts = df_with_ts.withColumn("imputed_flag",
                when(dir_was_null & col(dir_col).isNotNull(), lit(True))
                .otherwise(col("imputed_flag"))
            ).drop(f"{dir_col}_rad", f"{dir_col}_x", f"{dir_col}_y")

        # -----------------------------------------------
        # STEP 3: SPLIT AND WRITE
        # -----------------------------------------------
        final_df = df_with_ts.withColumn("data_quality", 
            when(col("imputed_flag"), lit("IMPUTED")).otherwise(lit("OK"))
        )

        # --- Write Dimension ---
        dim_df = final_df.select(
            "location_id", "latitude", "longitude", "elevation", "timezone", "timezone_abbreviation"
        ).distinct()
        dim_df.write.mode("append").parquet("/weather/silver/dim_location")
        print(f" -> Updated Dimensions")

        # --- Write Fact ---
        fact_cols = [
            "location_id", col("time").alias("event_time"),
            "temperature_2m", "relative_humidity_2m", "dew_point_2m", "apparent_temperature",
            "precipitation", "rain", "snowfall", "snow_depth", "weather_code",
            "pressure_msl", "surface_pressure",
            "cloud_cover", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high",
            "wind_speed_10m", "wind_speed_100m", "wind_direction_10m", "wind_direction_100m", "wind_gusts_10m",
            "soil_temperature_0_to_7cm", "soil_temperature_7_to_28cm", 
            "soil_temperature_28_to_100cm", "soil_temperature_100_to_255cm",
            "soil_moisture_0_to_7cm", "soil_moisture_7_to_28cm", 
            "soil_moisture_28_to_100cm", "soil_moisture_100_to_255cm",
            "data_quality"
        ]
        
        fact_df = final_df.select(*fact_cols)
        fact_df.write.mode("append").partitionBy("location_id").parquet("/weather/silver/fact_weather")
        print(f" -> Updated Facts")
        
        batch_df.unpersist()

    query = bronze_df.writeStream \
        .foreachBatch(process_and_split) \
        .option("checkpointLocation", "/weather/checkpoints/silver_simplified") \
        .trigger(availableNow=True) \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()