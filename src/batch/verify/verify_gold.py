from pyspark.sql import SparkSession
from pyspark.sql.functions import col, min, max, count

def main():
    spark = SparkSession.builder \
        .appName("VerifyGold") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("ERROR")

    print("\n========================================")
    print("      GOLD LAYER VERIFICATION")
    print("========================================")

    # --- 1. CHECK DAILY SUMMARY ---
    print("\n[1] Checking Daily Summary...")
    try:
        df = spark.read.parquet("/weather/gold/daily_summary")
        print(f" -> Row Count: {df.count()}")
        print(" -> Sample Data:")
        df.select("date", "avg_temp_c", "max_temp_c", "min_temp_c", "total_precip_mm").show(5)
        
        # LOGIC CHECK: Max must be >= Min
        bad_rows = df.filter(col("max_temp_c") < col("min_temp_c")).count()
        if bad_rows == 0:
            print(" -> PASS: Logic Check (Max >= Min)")
        else:
            print(f" -> FAIL: Found {bad_rows} rows where Max < Min!")
    except Exception as e:
        print(f" -> FAIL: Could not read table. Error: {e}")

    # --- 2. CHECK WEEKLY SUMMARY ---
    print("\n[2] Checking Weekly Summary...")
    try:
        df = spark.read.parquet("/weather/gold/weekly_summary")
        print(f" -> Row Count: {df.count()}")
        df.select("week_start", "avg_temp_c", "hours_recorded").show(3)
    except:
        print(" -> FAIL: Could not read Weekly table.")

    # --- 3. CHECK ML FEATURES (Advanced) ---
    print("\n[3] Checking ML Features...")
    try:
        df = spark.read.parquet("/weather/gold/ml_features")
        print(f" -> Row Count: {df.count()}")
        
        print(" -> Checking Feature Engineering (Cyclical Time & Lags):")
        df.select("date", "day_of_year", "doy_sin", "avg_temp_c", "lag_1d_avg_temp_c").show(5)
        
        # LOGIC CHECK: Sine waves must be between -1 and 1
        bad_sin = df.filter((col("doy_sin") > 1) | (col("doy_sin") < -1)).count()
        if bad_sin == 0:
            print(" -> PASS: Math Check (Sine waves are valid)")
        else:
            print(" -> FAIL: Sine/Cosine calculation is wrong.")
            
    except Exception as e:
        print(f" -> FAIL: Could not read ML Features. Error: {e}")

if __name__ == "__main__":
    main()