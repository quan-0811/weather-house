import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, to_timestamp, last, when, lit, coalesce
)
from pyspark.sql.window import Window
from schema import weather_schema

# Columns that belong to the static metadata table
META_COLS = [
    "location_id", 
    "latitude", 
    "longitude", 
    "elevation", 
    "utc_offset_seconds", 
    "timezone", 
    "timezone_abbreviation"
]

PHYSICAL_LIMITS = [
    # Atmospheric
    ("temperature_2m", -95, 65),
    ("apparent_temperature", -100, 80),
    ("dew_point_2m", -95, 65),
    ("relative_humidity_2m", 0, 105),
    ("pressure_msl", 850, 1100),
    ("surface_pressure", 500, 1100),
    
    # Wind
    ("wind_speed_10m", 0, 450),
    ("wind_speed_100m", 0, 450),
    ("wind_gusts_10m", 0, 450),
    ("wind_direction_10m", 0, 360),
    ("wind_direction_100m", 0, 360),
    
    # Cloud
    ("cloud_cover", 0, 100),
    ("cloud_cover_low", 0, 100),
    ("cloud_cover_mid", 0, 100),
    ("cloud_cover_high", 0, 100),
    
    # Soil Temperature
    ("soil_temperature_0_to_7cm", -50, 75),
    ("soil_temperature_7_to_28cm", -40, 60),
    ("soil_temperature_28_to_100cm", -30, 50),
    ("soil_temperature_100_to_255cm", -20, 40),
    
    # Soil Moisture
    ("soil_moisture_0_to_7cm", -0.05, 1.05),
    ("soil_moisture_7_to_28cm", -0.05, 1.05),
    ("soil_moisture_28_to_100cm", -0.05, 1.05),
    ("soil_moisture_100_to_255cm", -0.05, 1.05),
    
    # Precip
    ("precipitation", 0, 400),
    ("rain", 0, 400),
    ("snowfall", 0, 500),
    ("snow_depth", 0, 10000)
]

def get_spark_session():
    return SparkSession.builder \
        .appName("WeatherHDFSWrite") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
        .config("spark.cassandra.connection.host", "cassandra") \
        .config("spark.cassandra.connection.port", "9042") \
        .config("spark.cores.max", "1") \
        .config("spark.executor.memory", "1G") \
        .config("spark.driver.memory", "512m") \
        .getOrCreate()

def process_batch(batch_df, batch_id):
    if batch_df.isEmpty():
        return

    print(f"Processing Batch ID: {batch_id} with {batch_df.count()} records")
    batch_df.cache()
    
    # 1. COLD PATH: Archive Raw Data to HDFS (Bronze Layer)
    print(" -> Writing to HDFS (Raw)...")
    batch_df.write \
        .mode("append") \
        .partitionBy("location_id") \
        .parquet("hdfs://namenode:9000/weather/bronze")

    # 2. HOT PATH TRANSFORMATION: Cleaning & Imputation
    processing_df = batch_df.dropDuplicates(["location_id", "time"])

    # Nullify Outliers
    for col_name, min_val, max_val in PHYSICAL_LIMITS:
        if col_name in processing_df.columns:
            processing_df = processing_df.withColumn(col_name, 
                when(
                    (col(col_name) < min_val) | (col(col_name) > max_val), 
                    lit(None) 
                ).otherwise(col(col_name))
            )

    # Apply LOCF (Last Observation Carried Forward)
    w = Window.partitionBy("location_id").orderBy("time")
    
    imputed_df = processing_df.withColumn("data_quality", lit("OK"))
    
    for col_name, _, _ in PHYSICAL_LIMITS:
        if col_name in imputed_df.columns:
            last_val = last(col(col_name), ignorenulls=True).over(w)
            
            # Update quality flag if we are about to impute
            imputed_df = imputed_df.withColumn("data_quality",
                when(col(col_name).isNull() & last_val.isNotNull(), lit("IMPUTED"))
                .otherwise(col("data_quality"))
            )
            
            # Fill the null
            imputed_df = imputed_df.withColumn(col_name, coalesce(col(col_name), last_val))

    # 3. HOT PATH WRITE: Cassandra (Serving Layer)
    print(" -> Writing to Cassandra...")
    try:
        cassandra_prep_df = imputed_df.withColumn("time", to_timestamp(col("time")))

        # --- Write 1: Static Metadata (Normalized Table) ---
        meta_df = cassandra_prep_df.select(*META_COLS).distinct()
        
        meta_df.write \
            .format("org.apache.spark.sql.cassandra") \
            .options(table="location_meta_data", keyspace="weather_house") \
            .mode("append") \
            .save()

        # --- Write 2: Time-Series Metrics (Simplified Table) ---
        cols_to_drop = [c for c in META_COLS if c != "location_id"]
        ts_df = cassandra_prep_df.drop(*cols_to_drop)

        ts_df.write \
            .format("org.apache.spark.sql.cassandra") \
            .options(table="raw_weather_data", keyspace="weather_house") \
            .mode("append") \
            .save()
            
    except Exception as e:
        print(f"Cassandra Error: {e}")
            
    batch_df.unpersist()

def main():
    spark = get_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    # Read from Kafka
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka1:29092,kafka2:29092,kafka3:29092") \
        .option("subscribe", "weather-events") \
        .option("startingOffsets", "earliest") \
        .load()

    # Parse JSON
    raw_parsed_df = kafka_df.select(
        from_json(col("value").cast("string"), weather_schema).alias("data")
    ).select("data.*")

    # Start Stream
    query = raw_parsed_df.writeStream \
        .foreachBatch(process_batch) \
        .option("checkpointLocation", "hdfs://namenode:9000/weather/checkpoints/streaming") \
        .trigger(processingTime="30 seconds") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()
