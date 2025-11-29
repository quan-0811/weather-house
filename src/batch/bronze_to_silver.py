import sys
import os

# --- PATH HACK (For Local Imports) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, last, when, lit, coalesce
from pyspark.sql.window import Window
from streaming.schema import weather_schema 

def main():
    spark = SparkSession.builder \
        .appName("Refined_BronzeToSilver") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # 1. READ BRONZE STREAM
    bronze_df = spark.readStream \
        .schema(weather_schema) \
        .parquet("/weather/bronze")

    # ====================================================
    #      THE MICRO-BATCH LOGIC
    # ====================================================
    def process_and_split(batch_df, batch_id):
        print(f"--- Processing Batch {batch_id}: {batch_df.count()} rows ---")
        
        if batch_df.count() == 0:
            return

        # Cache the raw batch because we will read it multiple times
        batch_df.cache()

        # -----------------------------------------------
        # STEP A: IMPUTATION (Fill Forward)
        # -----------------------------------------------
        # "If temp is null, use the temp from the previous event"
        w_ff = Window.partitionBy("location_id").orderBy("event_time")

        # We create 'temp_clean' etc. using the last non-null value
        imputed_df = batch_df \
            .withColumn("temp_clean", last("temp_2m_c", ignorenulls=True).over(w_ff)) \
            .withColumn("humidity_clean", last("rel_humidity_2m_pct", ignorenulls=True).over(w_ff)) \
            .withColumn("rain_clean", coalesce(col("rain_mm"), lit(0.0))) # Assume 0 rain if null

        # -----------------------------------------------
        # STEP B: QUALITY TAGGING (Physics Checks)
        # -----------------------------------------------
        # We don't drop bad data, we label it 'ERR' or 'OK'
        
        # 1. Check for Critical Nulls (Data we can't save)
        #    If Location or Time is missing, we can't query it. Drop these.
        base_df = imputed_df \
            .filter(col("location_id").isNotNull()) \
            .filter(col("event_time").isNotNull())

        # 2. Check for Physics Errors (Data we save but flag)
        quality_df = base_df.withColumn("data_quality", 
            when(
                (col("temp_clean") > 60) | (col("temp_clean") < -60), 
                lit("ERR_TEMP_RANGE")
            ).when(
                (col("rain_clean") < 0), 
                lit("ERR_NEG_RAIN")
            ).when(
                col("temp_clean").isNull(),
                lit("ERR_MISSING_DATA") # If imputation failed (first row is null)
            ).otherwise(lit("OK"))
        )

        # -----------------------------------------------
        # STEP C: DEDUPLICATION
        # -----------------------------------------------
        # If ID and Time are identical, keep the first one
        deduped_df = quality_df.dropDuplicates(["location_id", "event_time"])

        # -----------------------------------------------
        # STEP D: SPLIT TO STAR SCHEMA
        # -----------------------------------------------

        # --- TABLE 1: DIMENSION (Context) ---
        # Extract unique static attributes
        dim_df = deduped_df.select(
            "location_id", 
            "latitude", 
            "longitude", 
            "elevation", 
            "timezone", 
            "timezone_abbr"
        ).distinct()

        dim_df.write \
            .mode("append") \
            .parquet("/silver/dim_location")
        
        print(f" -> Updated Dimensions ({dim_df.count()} rows)")

        # --- TABLE 2: FACT (Measurements) ---
        # Keep only measurements + Foreign Key + Quality Flag
        fact_df = deduped_df.select(
            "location_id", 
            "event_time", 
            "temp_clean", 
            "humidity_clean", 
            "rain_clean", 
            "wind_speed_10m_kmh", 
            "wind_dir_10m_deg",
            "data_quality"  # Critical for Gold filtering
        )

        fact_df.write \
            .mode("append") \
            .partitionBy("location_id") \
            .parquet("/silver/fact_weather")
        
        print(f" -> Updated Facts ({fact_df.count()} rows)")
        
        batch_df.unpersist()

    # ====================================================
    #      EXECUTION
    # ====================================================
    query = bronze_df.writeStream \
        .foreachBatch(process_and_split) \
        .option("checkpointLocation", "/checkpoints/silver_star_schema") \
        .trigger(availableNow=True) \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()