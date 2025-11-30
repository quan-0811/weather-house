from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count

def main():
    spark = SparkSession.builder \
        .appName("VerifySilverLayer") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("ERROR")

    print("\nXXX VERIFYING DIMENSION TABLE (dim_location) XXX")
    try:
        dim_df = spark.read.parquet("/weather/silver/dim_location")
        print(f"Total Locations: {dim_df.count()}")
        dim_df.show(5, truncate=False)
    except Exception as e:
        print(f"Error reading dim_location: {e}")

    print("\nXXX VERIFYING FACT TABLE (fact_weather) XXX")
    try:
        fact_df = spark.read.parquet("/weather/silver/fact_weather")
        print(f"Total Fact Records: {fact_df.count()}")
        
        # 1. Check Data Quality Distribution
        print("\n--- Data Quality Breakdown ---")
        fact_df.groupBy("data_quality").count().show()

        # 2. Verify Imputation Logic (Show rows where imputation happened)
        # We look for rows where quality is 'IMPUTED'
        print("\n--- Sample Imputed Rows ---")
        imputed_sample = fact_df.filter(col("data_quality") == "IMPUTED")
        if imputed_sample.count() > 0:
            imputed_sample.select(
                "location_id", "event_time", "temperature_2m", "precipitation", "data_quality"
            ).show(5)
        else:
            print("No records were marked as IMPUTED (Input data might have been clean).")

    except Exception as e:
        print(f"Error reading fact_weather: {e}")

if __name__ == "__main__":
    main()