"""
Bronze to Silver Layer Transformation
Simple transformations: data cleaning, parsing, validation, and standardization
Transforms raw ISD CSV data into clean, validated weather observations
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# ============================================================================
# ENVIRONMENT SETUP
# ============================================================================
def setup_spark_environment():
    """Setup Java, Spark, and Hadoop environment variables"""
    java_home = os.environ.get('JAVA_HOME')
    
    possible_paths = [
        r'C:\Java\jdk-11',
        r'C:\Java\jdk-*',
        r'C:\Program Files\Java\jdk-11*',
        r'C:\Program Files\Java\jdk-8*',
        r'C:\Program Files\Java\jdk1.8.0_*',
        r'C:\Program Files\Eclipse Adoptium\jdk-11*',
        r'C:\Program Files\OpenJDK\jdk-11*',
    ]
    
    import glob
    
    if java_home:
        java_exe = os.path.join(java_home, 'bin', 'java.exe')
        if not os.path.exists(java_exe):
            print(f"⚠ JAVA_HOME is set to {java_home} but java.exe not found there")
            java_home = None
    
    if not java_home:
        for pattern in possible_paths:
            matches = glob.glob(pattern)
            if matches:
                for match in matches:
                    java_exe = os.path.join(match, 'bin', 'java.exe')
                    if os.path.exists(java_exe):
                        java_home = match
                        os.environ['JAVA_HOME'] = java_home
                        print(f"✓ Found Java at: {java_home}")
                        break
                if java_home:
                    break
        
        if not java_home:
            print("\n" + "="*70)
            print("ERROR: Java not found!")
            print("="*70)
            print("\nPySpark requires Java 8 or 11. Please install Java.")
            sys.exit(1)
    else:
        print(f"✓ Using Java from: {java_home}")
    
    java_bin = os.path.join(java_home, 'bin')
    if java_bin not in os.environ.get('PATH', ''):
        os.environ['PATH'] = java_bin + os.pathsep + os.environ.get('PATH', '')

print("Setting up Spark environment...")
setup_spark_environment()

# ============================================================================
# IMPORTS
# ============================================================================
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, when, split, trim, to_timestamp, year, month, dayofmonth, hour,
    coalesce, lit, expr, regexp_replace, length, upper, lower
)
from pyspark.sql.types import DoubleType, IntegerType, StringType

# ============================================================================
# SPARK SESSION INITIALIZATION
# ============================================================================
print("Initializing Spark Session...")
spark = SparkSession.builder \
    .appName("Bronze_to_Silver_Transformation") \
    .master("local[*]") \
    .config("spark.executor.memory", "2g") \
    .config("spark.driver.memory", "2g") \
    .config("spark.sql.shuffle.partitions", "12") \
    .config("spark.driver.extraJavaOptions", "-Dio.netty.tryReflectionSetAccessible=true") \
    .config("spark.executor.extraJavaOptions", "-Dio.netty.tryReflectionSetAccessible=true") \
    .config("spark.ui.showConsoleProgress", "false") \
    .config("spark.sql.adaptive.enabled", "false") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "false") \
    .config("spark.cleaner.referenceTracking.cleanCheckpoints", "true") \
    .config("spark.local.dir", os.path.join(os.environ.get('TEMP', os.environ.get('TMP', 'C:\\Temp')), "spark-temp")) \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
print("✓ Spark session created successfully!")

# ============================================================================
# CONFIGURATION
# ============================================================================
BRONZE_INPUT_PATH = r"C:\Users\LENOVO\Documents\BigData\data"
SILVER_OUTPUT_PATH = r"C:\Users\LENOVO\Documents\BigData\silver"

print(f"\n[{datetime.now()}] Starting Bronze to Silver Transformation...")
print(f"Reading from: {BRONZE_INPUT_PATH}")

# ============================================================================
# STEP 1: READ RAW CSV FILES
# ============================================================================
print("\n[Step 1] Reading raw CSV files from bronze layer...")
try:
    # Read all CSV files from data directory
    # Use os.path.join for proper Windows path handling
    csv_pattern = os.path.join(BRONZE_INPUT_PATH, "*.csv")
    # Convert to forward slashes for Spark (works on Windows too)
    csv_pattern = csv_pattern.replace("\\", "/")
    
    df_bronze = spark.read \
        .option("header", "true") \
        .option("inferSchema", "false") \
        .option("quote", '"') \
        .option("escape", '"') \
        .csv(csv_pattern)
    
    bronze_count = df_bronze.count()
    print(f"✓ Bronze records loaded: {bronze_count:,}")
    
    # Print available columns for debugging
    print(f"Available columns: {', '.join(df_bronze.columns[:10])}... (total: {len(df_bronze.columns)})")
    
    if bronze_count == 0:
        print("ERROR: No records found in bronze layer!")
        spark.stop()
        sys.exit(1)
        
except Exception as e:
    print(f"ERROR reading bronze data: {e}")
    spark.stop()
    sys.exit(1)

# ============================================================================
# HELPER FUNCTION: Check if column exists
# ============================================================================
def column_exists(df, col_name):
    """Check if a column exists in the dataframe"""
    return col_name in df.columns

# ============================================================================
# STEP 2: CLEAN AND VALIDATE STATION METADATA
# ============================================================================
print("\n[Step 2] Cleaning and validating station metadata...")

df_silver = df_bronze \
    .withColumn("station_id", trim(col("STATION")).cast(StringType())) \
    .withColumn("station_name", trim(col("NAME")).cast(StringType())) \
    .withColumn("station_latitude", 
        when(col("LATITUDE").isNotNull() & (col("LATITUDE") != ""),
             col("LATITUDE").cast(DoubleType()))
        .otherwise(None)) \
    .withColumn("station_longitude",
        when(col("LONGITUDE").isNotNull() & (col("LONGITUDE") != ""),
             col("LONGITUDE").cast(DoubleType()))
        .otherwise(None)) \
    .withColumn("station_elevation",
        when(col("ELEVATION").isNotNull() & (col("ELEVATION") != ""),
             col("ELEVATION").cast(DoubleType()))
        .otherwise(None))
df_silver = df_silver \
    .withColumn("station_latitude",
        when((col("station_latitude") >= -90.0) & (col("station_latitude") <= 90.0),
             col("station_latitude"))
        .otherwise(None)) \
    .withColumn("station_longitude",
        when((col("station_longitude") >= -180.0) & (col("station_longitude") <= 180.0),
             col("station_longitude"))
        .otherwise(None))

# ============================================================================
# STEP 3: PARSE TIMESTAMP
# ============================================================================
print("\n[Step 3] Parsing timestamp...")

df_silver = df_silver \
    .withColumn("timestamp",
        when(col("DATE").isNotNull() & (col("DATE") != ""),
             to_timestamp(col("DATE"), "yyyy-MM-dd'T'HH:mm:ss"))
        .otherwise(None)) \
    .withColumn("year", year(col("timestamp"))) \
    .withColumn("month", month(col("timestamp"))) \
    .withColumn("day", dayofmonth(col("timestamp"))) \
    .withColumn("hour", hour(col("timestamp")))
df_silver = df_silver.filter(col("timestamp").isNotNull())

# ============================================================================
# STEP 4: DERIVE STATION REGION AND TIMEZONE
# ============================================================================
print("\n[Step 4] Deriving station region and timezone...")
df_silver = df_silver.withColumn(
    "station_region",
    when(col("station_name").contains(" US"), "north_america")
    .when(col("station_name").contains(" CA"), "north_america")
    .when(col("station_name").contains(" MX"), "north_america")
    .when(col("station_name").contains(" NY"), "northeast")
    .when(col("station_name").contains(" CA"), "west")
    .when(col("station_name").contains(" TX"), "south")
    .when(col("station_name").contains(" FL"), "southeast")
    .otherwise("unknown")
)
df_silver = df_silver.withColumn(
    "station_timezone",
    when(col("station_longitude").isNotNull(),
         (col("station_longitude") / 15.0).cast(IntegerType()))
    .otherwise(None)
)

# ============================================================================
# STEP 5: PARSE TEMPERATURE FIELDS
# ============================================================================
print("\n[Step 5] Parsing temperature fields...")
df_silver = df_silver \
    .withColumn("temperature_2m",
        when(
            col("TMP").isNotNull() & 
            (col("TMP") != "") &
            ~col("TMP").startswith("+9999") & 
            ~col("TMP").startswith("-9999") &
            ~col("TMP").contains("9999,9"),
            expr("CAST(REGEXP_EXTRACT(TMP, '^([+-]?\\d+)', 1) AS DOUBLE) / 10.0")
        ).otherwise(None)
    ) \
    .withColumn("dewpoint_2m",
        when(
            col("DEW").isNotNull() & 
            (col("DEW") != "") &
            ~col("DEW").startswith("+9999") & 
            ~col("DEW").startswith("-9999") &
            ~col("DEW").contains("9999,9"),
            expr("CAST(REGEXP_EXTRACT(DEW, '^([+-]?\\d+)', 1) AS DOUBLE) / 10.0")
        ).otherwise(None)
    )

# Validate temperature ranges (reasonable weather temperatures)
df_silver = df_silver \
    .withColumn("temperature_2m",
        when(
            (col("temperature_2m") >= -50.0) & (col("temperature_2m") <= 60.0),
            col("temperature_2m")
        ).otherwise(None)
    ) \
    .withColumn("dewpoint_2m",
        when(
            (col("dewpoint_2m") >= -50.0) & (col("dewpoint_2m") <= 60.0) &
            (col("dewpoint_2m") <= col("temperature_2m")),  # Dew point <= temperature
            col("dewpoint_2m")
        ).otherwise(None)
    )

# ============================================================================
# STEP 6: PARSE RELATIVE HUMIDITY
# ============================================================================
print("\n[Step 6] Parsing relative humidity...")
print("  Calculating relative humidity from temperature and dewpoint...")

# Calculate relative humidity from temperature and dewpoint using Magnus formula
# RH = 100 * exp((17.625 * Td) / (243.04 + Td)) / exp((17.625 * T) / (243.04 + T))
df_silver = df_silver.withColumn(
    "relative_humidity_2m",
    when(
        col("temperature_2m").isNotNull() & col("dewpoint_2m").isNotNull(),
        100.0 * expr("exp((17.625 * dewpoint_2m) / (243.04 + dewpoint_2m))") / 
               expr("exp((17.625 * temperature_2m) / (243.04 + temperature_2m))")
    ).otherwise(None)
)

# Validate humidity range (0-100%)
df_silver = df_silver.withColumn(
    "relative_humidity_2m",
    when(
        (col("relative_humidity_2m") >= 0.0) & (col("relative_humidity_2m") <= 100.0),
        col("relative_humidity_2m")
    ).otherwise(None)
)

# ============================================================================
# STEP 7: PARSE PRESSURE FIELDS
# ============================================================================
print("\n[Step 7] Parsing pressure fields...")
df_silver = df_silver.withColumn(
    "pressure_msl",
    when(
        col("SLP").isNotNull() & (col("SLP") != "") &
        ~col("SLP").startswith("99999") &
        (split(col("SLP"), ",")[0] != "99999"),
        split(col("SLP"), ",")[0].cast(DoubleType()) / 10.0
    ).otherwise(None)
)
df_silver = df_silver.withColumn(
    "pressure_msl",
    when(
        (col("pressure_msl") >= 850.0) & (col("pressure_msl") <= 1100.0),
        col("pressure_msl")
    ).otherwise(None)
)

# ============================================================================
# STEP 8: PARSE WIND DATA
# ============================================================================
print("\n[Step 8] Parsing wind data...")
df_silver = df_silver \
    .withColumn("wind_direction_10m",
        when(
            col("WND").isNotNull() & (col("WND") != "") &
            ~col("WND").contains("9,9,9,9999,9") &
            (split(col("WND"), ",")[0] != "999"),
            split(col("WND"), ",")[0].cast(IntegerType())
        ).otherwise(None)
    ) \
    .withColumn("wind_speed_10m",
        when(
            col("WND").isNotNull() & (col("WND") != "") &
            ~col("WND").contains("9,9,9,9999,9") &
            (split(col("WND"), ",")[3] != "9999"),
            split(col("WND"), ",")[3].cast(DoubleType()) * 3.6  # m/s to km/h
        ).otherwise(None)
    )
df_silver = df_silver.withColumn(
    "wind_direction_10m",
    when(
        (col("wind_direction_10m") >= 0) & (col("wind_direction_10m") <= 360),
        col("wind_direction_10m")
    ).otherwise(None)
)
df_silver = df_silver.withColumn(
    "wind_speed_10m",
    when(
        (col("wind_speed_10m") >= 0.0) & (col("wind_speed_10m") <= 200.0),
        col("wind_speed_10m")
    ).otherwise(None)
)

# Parse wind gusts from GA1, GA2, GA3: Format "30,5" -> 30 m/s -> 108 km/h
# Check which gust columns exist
gust_expr = None
for gust_col in ["GA1", "GA2", "GA3"]:
    if gust_col in df_bronze.columns:
        if gust_expr is None:
            gust_expr = when(
                col(gust_col).isNotNull() & (col(gust_col) != "") &
                ~col(gust_col).startswith("99") &
                (split(col(gust_col), ",")[0] != "99"),
                split(col(gust_col), ",")[0].cast(DoubleType()) * 3.6
            ).otherwise(None)
        else:
            gust_expr = coalesce(
                gust_expr,
                when(
                    col(gust_col).isNotNull() & (col(gust_col) != "") &
                    ~col(gust_col).startswith("99") &
                    (split(col(gust_col), ",")[0] != "99"),
                    split(col(gust_col), ",")[0].cast(DoubleType()) * 3.6
                ).otherwise(None)
            )

if gust_expr is not None:
    df_silver = df_silver.withColumn("wind_gusts_10m", gust_expr)
else:
    print("  No GA1/GA2/GA3 columns found, setting wind_gusts_10m to NULL")
    df_silver = df_silver.withColumn("wind_gusts_10m", lit(None).cast(DoubleType()))

# ============================================================================
# STEP 9: PARSE PRECIPITATION DATA
# ============================================================================
print("\n[Step 9] Parsing precipitation data...")

# Parse AA1: Format "01,00100,9,5" -> depth: 100/1000 inches -> 2.54 mm
df_silver = df_silver \
    .withColumn("precipitation",
        when(
            col("AA1").isNotNull() & (col("AA1") != "") &
            ~col("AA1").contains("99,99999") &
            (split(col("AA1"), ",")[0] != "99") &
            (split(col("AA1"), ",")[1] != "99999"),
            split(col("AA1"), ",")[1].cast(DoubleType()) / 1000.0 * 25.4 
        ).otherwise(None)
    ) \
    .withColumn("rain", col("precipitation"))
print("  Setting snowfall to NULL (will be filled from Open-Meteo API)")
df_silver = df_silver.withColumn("snowfall", lit(None).cast(DoubleType()))

# ============================================================================
# STEP 10: PARSE CLOUD COVER
# ============================================================================
print("\n[Step 10] Parsing cloud cover...")
print("  Setting cloud_cover to NULL (AI1/AI2/AJ1 removed, will be filled from Open-Meteo API)")
df_silver = df_silver.withColumn("cloud_cover", lit(None).cast(DoubleType()))

# ============================================================================
# STEP 11: PARSE VISIBILITY
# ============================================================================
print("\n[Step 11] Parsing visibility...")
df_silver = df_silver.withColumn(
    "visibility_km",
    when(
        col("VIS").isNotNull() & (col("VIS") != "") &
        ~col("VIS").contains("999999") &
        (split(col("VIS"), ",")[0] != "999999"),
        split(col("VIS"), ",")[0].cast(DoubleType()) / 1000.0  # meters to km
    ).otherwise(None)
)

# Validate visibility (0-200 km)
df_silver = df_silver.withColumn(
    "visibility_km",
    when(
        (col("visibility_km") >= 0.0) & (col("visibility_km") <= 200.0),
        col("visibility_km")
    ).otherwise(None)
)

# ============================================================================
# STEP 12: PARSE WEATHER CODE
# ============================================================================
print("\n[Step 12] Parsing weather code...")
weather_expr = None
for weather_col in ["KE1", "MW1", "MW2", "MW3"]:
    if weather_col in df_bronze.columns:
        if weather_expr is None:
            weather_expr = when(col(weather_col).isNotNull() & (col(weather_col) != ""), trim(col(weather_col))).otherwise(None)
        else:
            weather_expr = coalesce(
                weather_expr,
                when(col(weather_col).isNotNull() & (col(weather_col) != ""), trim(col(weather_col))).otherwise(None)
            )

if weather_expr is not None:
    df_silver = df_silver.withColumn("weather_code", weather_expr)
else:
    print("  No KE1/MW1-MW3 columns found, setting weather_code to NULL")
    df_silver = df_silver.withColumn("weather_code", lit(None).cast(StringType()))

# ============================================================================
# STEP 13: DATA QUALITY FILTERING
# ============================================================================
print("\n[Step 13] Applying data quality filters...")
df_silver = df_silver.filter(
    (col("QUALITY_CONTROL").like("V0%")) |
    (col("QUALITY_CONTROL").like("V1%")) |
    (col("QUALITY_CONTROL").like("V2%")) |
    (col("QUALITY_CONTROL").like("V3%"))
)
df_silver = df_silver.filter(
    col("temperature_2m").isNotNull() |
    col("pressure_msl").isNotNull() |
    col("wind_speed_10m").isNotNull() |
    col("precipitation").isNotNull()
)

# ============================================================================
# STEP 14: CALCULATE DATA COMPLETENESS
# ============================================================================
print("\n[Step 14] Calculating data completeness...")

df_silver = df_silver.withColumn(
    "data_completeness",
    (
        (when(col("temperature_2m").isNotNull(), 1).otherwise(0) +
         when(col("dewpoint_2m").isNotNull(), 1).otherwise(0) +
         when(col("relative_humidity_2m").isNotNull(), 1).otherwise(0) +
         when(col("pressure_msl").isNotNull(), 1).otherwise(0) +
         when(col("wind_speed_10m").isNotNull(), 1).otherwise(0) +
         when(col("wind_direction_10m").isNotNull(), 1).otherwise(0) +
         when(col("precipitation").isNotNull(), 1).otherwise(0) +
         when(col("visibility_km").isNotNull(), 1).otherwise(0) +
         when(col("cloud_cover").isNotNull(), 1).otherwise(0)) / 9.0 * 100.0
    )
)

# ============================================================================
# STEP 15: ADD SEASON AND TEMPORAL FEATURES
# ============================================================================
print("\n[Step 15] Adding temporal features...")

df_silver = df_silver.withColumn(
    "season",
    when(col("month").isin(12, 1, 2), "winter")
    .when(col("month").isin(3, 4, 5), "spring")
    .when(col("month").isin(6, 7, 8), "summer")
    .otherwise("autumn")
)

# ============================================================================
# STEP 16: SELECT FINAL SILVER COLUMNS
# ============================================================================
print("\n[Step 16] Selecting final silver columns...")

silver_columns = [
    "station_id", "station_name", "station_region", 
    "station_latitude", "station_longitude", "station_elevation", "station_timezone",
    "timestamp", "year", "month", "day", "hour", "season",
    "temperature_2m", "dewpoint_2m", "relative_humidity_2m",
    "pressure_msl", 
    "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m",
    "precipitation", "rain", "snowfall",
    "visibility_km", "cloud_cover",
    "weather_code",
    "data_completeness",
    "SOURCE", "REPORT_TYPE", "QUALITY_CONTROL"
]

df_silver_final = df_silver.select(*silver_columns)

# ============================================================================
# STATISTICS AND OUTPUT
# ============================================================================
print("\n" + "="*70)
print("SILVER LAYER STATISTICS")
print("="*70)

try:
    print("Counting total records...")
    silver_count = df_silver_final.count()
    print(f"Total Records: {silver_count:,}")
    
    if silver_count == 0:
        print("⚠ WARNING: No records found in silver layer!")
        print("Script will exit without writing data.")
        spark.stop()
        sys.exit(1)
    
    print("Calculating statistics...")
    avg_completeness = df_silver_final.agg({"data_completeness": "avg"}).collect()[0][0]
    if avg_completeness is not None:
        print(f"Average Data Completeness: {avg_completeness:.2f}%")
    else:
        print("Average Data Completeness: N/A")
    
    print("Counting records by field...")
    temp_count = df_silver_final.filter(col('temperature_2m').isNotNull()).count()
    wind_count = df_silver_final.filter(col('wind_speed_10m').isNotNull()).count()
    precip_count = df_silver_final.filter(col('precipitation').isNotNull()).count()
    pressure_count = df_silver_final.filter(col('pressure_msl').isNotNull()).count()
    
    print(f"Records with Temperature: {temp_count:,}")
    print(f"Records with Wind Data: {wind_count:,}")
    print(f"Records with Precipitation: {precip_count:,}")
    print(f"Records with Pressure: {pressure_count:,}")
    
    # Show sample (limit to avoid issues)
    print("\n" + "="*70)
    print("SAMPLE CLEANED RECORDS")
    print("="*70)
    try:
        df_silver_final.select(
            "station_name", "timestamp", "temperature_2m", "wind_speed_10m", 
            "precipitation", "data_completeness"
        ).show(10, truncate=False)
    except Exception as e:
        print(f"Could not display sample: {e}")
        print("Continuing with write operation...")
        
except Exception as e:
    print(f"⚠ ERROR calculating statistics: {e}")
    print("Continuing with write operation anyway...")
    import traceback
    traceback.print_exc()
    # Try to get count at least
    try:
        silver_count = df_silver_final.count()
    except:
        silver_count = 0
        print("Could not determine record count. Exiting.")
        spark.stop()
        sys.exit(1)

# Write to Parquet
print(f"\n[{datetime.now()}] Writing Silver layer to Parquet...")
write_success = False
try:
    # Ensure output directory exists
    output_dir = Path(SILVER_OUTPUT_PATH)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory prepared: {SILVER_OUTPUT_PATH}")
    
    # Cache the dataframe to avoid recomputation
    print("Caching final dataframe...")
    df_silver_final.cache()
    
    # Force materialization before write
    print("Materializing dataframe...")
    materialized_count = df_silver_final.count()
    print(f"Dataframe materialized: {materialized_count:,} records")
    
    # Write with explicit error handling
    print("Starting Parquet write operation...")
    df_silver_final.write \
        .mode("overwrite") \
        .option("compression", "snappy") \
        .partitionBy("year", "month") \
        .parquet(SILVER_OUTPUT_PATH)
    
    # Verify write by reading back a sample
    print("Verifying write operation...")
    verify_df = spark.read.parquet(SILVER_OUTPUT_PATH)
    verify_count = verify_df.count()
    print(f"Verification: {verify_count:,} records written successfully")
    
    if verify_count == materialized_count:
        write_success = True
        print("\n" + "="*70)
        print("✓ BRONZE TO SILVER TRANSFORMATION COMPLETE!")
        print("="*70)
        print(f"Output location: {SILVER_OUTPUT_PATH}")
        print(f"Total records processed: {silver_count:,}")
        print(f"Records written: {verify_count:,}")
        print(f"Completed at: {datetime.now()}")
    else:
        print(f"\n⚠ WARNING: Record count mismatch! Expected {materialized_count:,}, got {verify_count:,}")
        write_success = False
    
except Exception as e:
    print(f"\n✗ ERROR writing data: {e}")
    import traceback
    traceback.print_exc()
    write_success = False

finally:
    # Unpersist cached data
    try:
        df_silver_final.unpersist()
    except:
        pass
    
    # Stop Spark session gracefully
    print("\nStopping Spark session...")
    try:
        spark.stop()
        print("✓ Spark session stopped successfully.")
    except Exception as e:
        print(f"⚠ Warning during Spark shutdown: {e}")
    
    if write_success:
        print("\n✓ Script finished successfully!")
    else:
        print("\n✗ Script finished with errors. Please check the output above.")
        sys.exit(1)


