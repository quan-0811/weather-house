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
            .parquet("hdfs://namenode:9000/weather/bronze")

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

    # 3. No Column Renaming needed
    clean_df = raw_parsed_df

    # 4. Start Streaming Query
    query = clean_df.writeStream \
        .foreachBatch(process_batch) \
        .option("checkpointLocation", "hdfs://namenode:9000/weather/checkpoints/streaming") \
        .trigger(processingTime="10 seconds") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()