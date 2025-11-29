from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from schema import weather_schema

def get_spark_session():
    # Cassandra configs commented out for HDFS-only run
    return SparkSession.builder \
        .appName("WeatherHDFSWrite") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
        .getOrCreate()

def process_batch(batch_df, batch_id):
    print(f"Processing Batch ID: {batch_id} with {batch_df.count()} records")
    
    if batch_df.count() > 0:
        # 1. Write to HDFS (Parquet Format)
        # Using /bronze/weather_raw_data as requested in the snippet.
        # If you are building a medallion architecture, this is your Bronze layer.
        print("Writing to HDFS...")
        batch_df.write \
            .mode("append") \
            .partitionBy("location_id") \
            .parquet("hdfs://namenode:9000/bronze/weather_raw_data")

def main():
    spark = get_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    # 1. Read from Kafka
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka1:29092,kafka2:29092,kafka3:29092") \
        .option("subscribe", "weather-events") \
        .option("startingOffsets", "earliest") \
        .load()

    # 2. Parse JSON Payload
    raw_parsed_df = kafka_df.select(
        from_json(col("value").cast("string"), weather_schema).alias("data")
    ).select("data.*")

    # 3. Clean Column Names

    clean_df = raw_parsed_df.select(
        col("location_id"),
        col("latitude"),
        col("longitude"),
        col("elevation"),
        col("utc_offset_seconds"),
        col("timezone"),
        col("timezone_abbreviation").alias("timezone_abbr"),
        col("time").alias("event_time"),
        
        # Atmospheric
        col("temperature_2m").alias("temp_2m_c"),
        col("relative_humidity_2m").alias("rel_humidity_2m_pct"),
        col("dew_point_2m").alias("dew_point_2m_c"),
        col("apparent_temperature").alias("apparent_temp_c"),
        col("precipitation").alias("precip_mm"),
        col("rain").alias("rain_mm"),
        col("snowfall").alias("snowfall_cm"),
        col("snow_depth").alias("snow_depth_m"),
        col("weather_code").alias("weather_code"),
        col("pressure_msl").alias("pressure_msl_hpa"),
        col("surface_pressure").alias("surface_pressure_hpa"),
        
        # Cloud Cover
        col("cloud_cover").alias("cloud_cover_pct"),
        col("cloud_cover_low").alias("cloud_cover_low_pct"),
        col("cloud_cover_mid").alias("cloud_cover_mid_pct"),
        col("cloud_cover_high").alias("cloud_cover_high_pct"),
        
        # Wind
        col("wind_speed_10m").alias("wind_speed_10m_kmh"),
        col("wind_speed_100m").alias("wind_speed_100m_kmh"),
        col("wind_direction_10m").alias("wind_dir_10m_deg"),
        col("wind_direction_100m").alias("wind_dir_100m_deg"),
        col("wind_gusts_10m").alias("wind_gusts_10m_kmh"),
        
        # Soil Temp
        col("soil_temperature_0_to_7cm").alias("soil_temp_0_7cm_c"),
        col("soil_temperature_7_to_28cm").alias("soil_temp_7_28cm_c"),
        col("soil_temperature_28_to_100cm").alias("soil_temp_28_100cm_c"),
        col("soil_temperature_100_to_255cm").alias("soil_temp_100_255cm_c"),
        
        # Soil Moisture
        col("soil_moisture_0_to_7cm").alias("soil_moist_0_7cm"),
        col("soil_moisture_7_to_28cm").alias("soil_moist_7_28cm"),
        col("soil_moisture_28_to_100cm").alias("soil_moist_28_100cm"),
        col("soil_moisture_100_to_255cm").alias("soil_moist_100_255cm")
    )

    # 4. Start Streaming Query
    query = clean_df.writeStream \
        .foreachBatch(process_batch) \
        .option("checkpointLocation", "hdfs://namenode:9000/checkpoints") \
        .trigger(processingTime="10 seconds") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()