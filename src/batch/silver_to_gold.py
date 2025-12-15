import sys
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, to_date, avg, min, max, sum, count, 
    round, broadcast, lit, when, trunc, 
    dayofyear, month, sin, cos, lag
)
from pyspark.sql.window import Window

def main():
    spark = SparkSession.builder \
        .appName("SilverToGold") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")

    print("--- READING SILVER LAYER ---")
    fact_df = spark.read.parquet("/weather/silver/fact_weather")
    dim_df = spark.read.parquet("/weather/silver/dim_location")

    # 1. Join Fact and Dimension
    # We broadcast dim_df because it is small (52 rows)
    full_df = fact_df.join(broadcast(dim_df), "location_id") \
                     .withColumn("date", to_date(col("event_time")))

    full_df.cache()

    # =========================================================
    # PART B: AGGREGATIONS (Daily, Weekly, Monthly)
    # =========================================================
    
    # Helper function to generate standard metrics for any time grouping
    def write_aggregation(df, group_cols, output_path):
        agg_df = df.groupBy(*group_cols).agg(
            # --- Temperature Metrics ---
            round(avg("temperature_2m"), 2).alias("avg_temp_c"),
            round(max("temperature_2m"), 2).alias("max_temp_c"),
            round(min("temperature_2m"), 2).alias("min_temp_c"),
            round(avg("apparent_temperature"), 2).alias("avg_feels_like_c"),
            round(avg("dew_point_2m"), 2).alias("avg_dew_point_c"),
            
            # --- Precipitation Metrics ---
            round(sum("precipitation"), 2).alias("total_precip_mm"),
            round(sum("rain"), 2).alias("total_rain_mm"),
            round(sum("snowfall"), 2).alias("total_snow_cm"),
            round(max("snow_depth"), 2).alias("max_snow_depth_m"),
            
            # --- Wind Metrics ---
            round(max("wind_gusts_10m"), 2).alias("max_wind_gust_kmh"),
            round(avg("wind_speed_10m"), 2).alias("avg_wind_speed_10m_kmh"),
            round(avg("wind_speed_100m"), 2).alias("avg_wind_speed_100m_kmh"),
            
            # --- Atmosphere ---
            round(avg("relative_humidity_2m"), 2).alias("avg_humidity"),
            round(avg("pressure_msl"), 2).alias("avg_pressure_msl_hpa"),
            round(avg("surface_pressure"), 2).alias("avg_surface_pressure_hpa"),
            
            # --- Cloud Cover ---
            round(avg("cloud_cover"), 2).alias("avg_cloud_cover_pct"),
            round(avg("cloud_cover_low"), 2).alias("avg_cloud_low_pct"),
            round(avg("cloud_cover_mid"), 2).alias("avg_cloud_mid_pct"),
            round(avg("cloud_cover_high"), 2).alias("avg_cloud_high_pct"),

            # --- Soil Temperature ---
            round(avg("soil_temperature_0_to_7cm"), 2).alias("avg_soil_temp_0_7cm_c"),
            round(avg("soil_temperature_7_to_28cm"), 2).alias("avg_soil_temp_7_28cm_c"),
            round(avg("soil_temperature_28_to_100cm"), 2).alias("avg_soil_temp_28_100cm_c"),
            round(avg("soil_temperature_100_to_255cm"), 2).alias("avg_soil_temp_100_255cm_c"),

            # --- Soil Moisture ---
            round(avg("soil_moisture_0_to_7cm"), 2).alias("avg_soil_moist_0_7cm"),
            round(avg("soil_moisture_7_to_28cm"), 2).alias("avg_soil_moist_7_28cm"),
            round(avg("soil_moisture_28_to_100cm"), 2).alias("avg_soil_moist_28_100cm"),
            round(avg("soil_moisture_100_to_255cm"), 2).alias("avg_soil_moist_100_255cm"),
            
            # --- Metadata ---
            count("event_time").alias("hours_recorded")
        )
        agg_df.write.mode("overwrite").parquet(output_path)
        print(f" -> Written {output_path}")
        return agg_df

    print("--- BUILDING AGGREGATIONS ---")
    
    # 1. Daily Summary
    daily_df = write_aggregation(
        full_df, 
        ["location_id", "date", "timezone"], 
        "/weather/gold/daily_summary"
    )

    # 2. Weekly Summary (Truncate date to Monday of that week)
    write_aggregation(
        full_df.withColumn("week_start", trunc(col("date"), "week")), 
        ["location_id", "week_start", "timezone"], 
        "/weather/gold/weekly_summary"
    )

    # 3. Monthly Summary (Truncate date to 1st of that month)
    write_aggregation(
        full_df.withColumn("month_start", trunc(col("date"), "month")), 
        ["location_id", "month_start", "timezone"], 
        "/weather/gold/monthly_summary"
    )

    # =========================================================
    # PART C: ML FEATURE ENGINEERING
    # =========================================================
    print("--- BUILDING: ML FEATURES ---")

    # We start from the DAILY summary we just created
    w_loc = Window.partitionBy("location_id").orderBy("date")
    w_rolling_7d = w_loc.rowsBetween(-6, 0)
    w_rolling_30d = w_loc.rowsBetween(-29, 0)

    # 1. Cyclical Time Features (Seasonality)
    ml_features_df = daily_df \
        .withColumn("day_of_year", dayofyear("date")) \
        .withColumn("doy_sin", sin(2 * 3.14159 * col("day_of_year") / 365)) \
        .withColumn("doy_cos", cos(2 * 3.14159 * col("day_of_year") / 365))

    # 2. Lags & Rolling Averages (Trends)
    # Added Pressure to key metrics since we calculate it now
    key_metrics = ["avg_temp_c", "total_precip_mm", "avg_pressure_msl_hpa"]
    
    for metric in key_metrics:
        # Check to ensure column exists before processing
        if metric in ml_features_df.columns:
            ml_features_df = ml_features_df \
                .withColumn(f"lag_1d_{metric}", lag(metric, 1).over(w_loc)) \
                .withColumn(f"rolling_7d_{metric}", avg(metric).over(w_rolling_7d)) \
                .withColumn(f"rolling_30d_{metric}", avg(metric).over(w_rolling_30d))

    ml_features_df.write.mode("overwrite").parquet("/weather/gold/ml_features")
    print(" -> Written /weather/gold/ml_features")

    full_df.unpersist()
    spark.stop()

if __name__ == "__main__":
    main()