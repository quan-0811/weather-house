"""
Silver to Gold Layer Transformation
Complex transformations: aggregations, feature engineering, time-series analysis
Prepares data for machine learning and long-term storage
"""
import openmeteo_requests
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
from pyspark.sql import SparkSession, Window
from pyspark.sql.functions import (
    col, avg, min as sql_min, max as sql_max, sum as sql_sum, count, stddev,
    lag, lead, expr, when, coalesce, lit, round as sql_round,
    percentile_approx, countDistinct, first, last,
    unix_timestamp, row_number, abs as sql_abs, variance,
    dayofyear, weekofyear, quarter, date_format, to_timestamp, hour
)
from pyspark.sql.types import StructType, StructField, DoubleType, TimestampType, StringType
from pyspark.sql.functions import year, month, dayofmonth
import pandas as pd
import openmeteo_requests
import requests_cache
from retry_requests import retry
from datetime import datetime, timedelta

# ============================================================================
# SPARK SESSION
# ============================================================================
print("Initializing Spark Session...")
spark = SparkSession.builder \
    .appName("Silver_to_Gold_Transformation") \
    .master("local[*]") \
    .config("spark.executor.memory", "2g") \
    .config("spark.driver.memory", "2g") \
    .config("spark.sql.shuffle.partitions", "12") \
    .config("spark.ui.enabled", "false") \
    .config("spark.ui.showConsoleProgress", "false") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
print("✓ Spark session created successfully!")

# ============================================================================
# CONFIGURATION
# ============================================================================
SILVER_INPUT_PATH = r"C:\Users\LENOVO\Documents\BigData\silver"
GOLD_OUTPUT_PATH = r"C:\Users\LENOVO\Documents\BigData\gold"

print(f"\n[{datetime.now()}] Starting Silver to Gold Transformation...")

# ============================================================================
# SETUP OPEN-METEO API CLIENT
# ============================================================================
print("\n[Setup] Initializing Open-Meteo API client...")
cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)
print("✓ Open-Meteo API client ready")

# ============================================================================
# READ SILVER DATA
# ============================================================================
try:
    print(f"\nReading from: {SILVER_INPUT_PATH}")
    df_silver = spark.read.parquet(SILVER_INPUT_PATH)
    record_count = df_silver.count()
    print(f"✓ Silver records loaded: {record_count:,}")
    
    if record_count == 0:
        print("ERROR: No records found in silver layer!")
        spark.stop()
        sys.exit(1)
        
except Exception as e:
    print(f"ERROR reading silver data: {e}")
    spark.stop()
    sys.exit(1)

# ============================================================================
# ENRICH WITH OPEN-METEO API DATA (New York stations only)
# ============================================================================
print("\n[Enrichment] Enriching data with Open-Meteo API for New York stations...")

# Filter for New York stations (latitude ~40-42, longitude ~-74 to -73)
df_ny = df_silver.filter(
    (col("station_latitude") >= 40.0) & (col("station_latitude") <= 42.0) &
    (col("station_longitude") >= -75.0) & (col("station_longitude") <= -73.0)
)

if df_ny.count() > 0:
    print(f"  Found {df_ny.count():,} New York records to enrich")
    
    # Get date range from data
    date_stats = df_ny.select(
        sql_min("timestamp").alias("min_date"),
        sql_max("timestamp").alias("max_date")
    ).collect()[0]
    min_date = date_stats[0]  # Access by index
    max_date = date_stats[1]  # Access by index
    
    print(f"  Date range: {min_date} to {max_date}")
    
    # Get unique station coordinates
    stations = df_ny.select(
        "station_id", "station_latitude", "station_longitude"
    ).distinct().collect()
    
    print(f"  Found {len(stations)} unique New York stations")
    
    # Collect API data for each station
    api_data_list = []
    
    max_stations = min(5, len(stations))
    for i, station in enumerate(stations[:max_stations]):
        station_id = station["station_id"]
        lat = float(station["station_latitude"])
        lon = float(station["station_longitude"])
        
        print(f"  [{i+1}/{max_stations}] Fetching data for station {station_id} at ({lat:.4f}, {lon:.4f})...")
        
        try:
            url = "https://archive-api.open-meteo.com/v1/archive"
            params = {
                "latitude": float(lat),
                "longitude": float(lon),
                "start_date": min_date.strftime("%Y-%m-%d"),
                "end_date": max_date.strftime("%Y-%m-%d"),
                "hourly": [
                    "temperature_2m", "dew_point_2m",
                    "relative_humidity_2m", "pressure_msl",
                    "wind_speed_10m", "wind_gusts_10m", "wind_direction_10m",
                    "precipitation", "rain", "snowfall", "cloud_cover",
                    "weather_code", "visibility"
                ],
            }
            
            responses = openmeteo.weather_api(url, params=params)
            response = responses[0]
            
            # Process hourly data
            hourly = response.Hourly()
            hourly_data = {"date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"
            )}
            
            # Extract only variables that exist in silver layer (order matches API params)
            var_idx = 0
            hourly_data["temperature_2m"] = hourly.Variables(var_idx).ValuesAsNumpy()
            var_idx += 1
            hourly_data["dew_point_2m"] = hourly.Variables(var_idx).ValuesAsNumpy()
            var_idx += 1
            hourly_data["relative_humidity_2m"] = hourly.Variables(var_idx).ValuesAsNumpy()
            var_idx += 1
            hourly_data["pressure_msl"] = hourly.Variables(var_idx).ValuesAsNumpy()
            var_idx += 1
            hourly_data["wind_speed_10m"] = hourly.Variables(var_idx).ValuesAsNumpy()
            var_idx += 1
            hourly_data["wind_gusts_10m"] = hourly.Variables(var_idx).ValuesAsNumpy()
            var_idx += 1
            hourly_data["wind_direction_10m"] = hourly.Variables(var_idx).ValuesAsNumpy()
            var_idx += 1
            hourly_data["precipitation"] = hourly.Variables(var_idx).ValuesAsNumpy()
            var_idx += 1
            hourly_data["rain"] = hourly.Variables(var_idx).ValuesAsNumpy()
            var_idx += 1
            hourly_data["snowfall"] = hourly.Variables(var_idx).ValuesAsNumpy()
            var_idx += 1
            hourly_data["cloud_cover"] = hourly.Variables(var_idx).ValuesAsNumpy()
            var_idx += 1
            hourly_data["weather_code"] = hourly.Variables(var_idx).ValuesAsNumpy()
            var_idx += 1
            hourly_data["visibility"] = hourly.Variables(var_idx).ValuesAsNumpy()
            
            # Add station_id
            hourly_data["station_id"] = station_id
            
            # Convert to DataFrame
            api_df = pd.DataFrame(data=hourly_data)
            api_data_list.append(api_df)
            
            print(f"    ✓ Fetched {len(api_df)} records")
            
        except Exception as e:
            print(f"    ✗ Error fetching data for station {station_id}: {e}")
            continue
    
    # Combine all API data
    if api_data_list:
        print(f"\n  Combining API data from {len(api_data_list)} stations...")
        combined_api_df = pd.concat(api_data_list, ignore_index=True)
        
        # Convert to Spark DataFrame (only fields that exist in silver layer)
        api_schema = StructType([
            StructField("date", TimestampType(), True),
            StructField("temperature_2m", DoubleType(), True),
            StructField("dew_point_2m", DoubleType(), True),
            StructField("relative_humidity_2m", DoubleType(), True),
            StructField("pressure_msl", DoubleType(), True),
            StructField("wind_speed_10m", DoubleType(), True),
            StructField("wind_gusts_10m", DoubleType(), True),
            StructField("wind_direction_10m", DoubleType(), True),
            StructField("precipitation", DoubleType(), True),
            StructField("rain", DoubleType(), True),
            StructField("snowfall", DoubleType(), True),
            StructField("cloud_cover", DoubleType(), True),
            StructField("weather_code", DoubleType(), True),
            StructField("visibility", DoubleType(), True),
            StructField("station_id", StringType(), True),
        ])
        
        df_api = spark.createDataFrame(combined_api_df, schema=api_schema)
        
        # Rename date to timestamp and add hour
        df_api = df_api \
            .withColumnRenamed("date", "api_timestamp") \
            .withColumn("api_year", year(col("api_timestamp"))) \
            .withColumn("api_month", month(col("api_timestamp"))) \
            .withColumn("api_day", dayofmonth(col("api_timestamp"))) \
            .withColumn("api_hour", hour(col("api_timestamp")))
        
        # Join with silver data on station_id, year, month, day, hour
        print("  Joining API data with silver data...")
        df_silver = df_silver \
            .join(
                df_api.select(
                    "station_id", "api_year", "api_month", "api_day", "api_hour",
                    col("temperature_2m").alias("api_temperature_2m"),
                    col("dew_point_2m").alias("api_dewpoint_2m"),
                    col("relative_humidity_2m").alias("api_relative_humidity_2m"),
                    col("pressure_msl").alias("api_pressure_msl"),
                    col("wind_speed_10m").alias("api_wind_speed_10m"),
                    col("wind_gusts_10m").alias("api_wind_gusts_10m"),
                    col("wind_direction_10m").alias("api_wind_direction_10m"),
                    col("precipitation").alias("api_precipitation"),
                    col("rain").alias("api_rain"),
                    col("snowfall").alias("api_snowfall"),
                    col("cloud_cover").alias("api_cloud_cover"),
                    col("weather_code").alias("api_weather_code"),
                    col("visibility").alias("api_visibility")
                ),
                (df_silver["station_id"] == df_api["station_id"]) &
                (df_silver["year"] == df_api["api_year"]) &
                (df_silver["month"] == df_api["api_month"]) &
                (df_silver["day"] == df_api["api_day"]) &
                (df_silver["hour"] == df_api["api_hour"]),
                "left"
            )
        
        # Fill missing values with API data where available (ONLY fill gaps, don't add new fields)
        # Note: Open-Meteo API returns wind speed in km/h (same as silver), so no conversion needed
        print("  Filling missing values with API data...")
        df_silver = df_silver \
            .withColumn("temperature_2m", coalesce(col("temperature_2m"), col("api_temperature_2m"))) \
            .withColumn("dewpoint_2m", coalesce(col("dewpoint_2m"), col("api_dewpoint_2m"))) \
            .withColumn("relative_humidity_2m", coalesce(col("relative_humidity_2m"), col("api_relative_humidity_2m"))) \
            .withColumn("pressure_msl", coalesce(col("pressure_msl"), col("api_pressure_msl"))) \
            .withColumn("wind_speed_10m", coalesce(col("wind_speed_10m"), col("api_wind_speed_10m"))) \
            .withColumn("wind_gusts_10m", coalesce(col("wind_gusts_10m"), col("api_wind_gusts_10m"))) \
            .withColumn("wind_direction_10m", coalesce(col("wind_direction_10m"), col("api_wind_direction_10m"))) \
            .withColumn("precipitation", coalesce(col("precipitation"), col("api_precipitation"))) \
            .withColumn("rain", coalesce(col("rain"), col("api_rain"))) \
            .withColumn("snowfall", coalesce(col("snowfall"), col("api_snowfall"))) \
            .withColumn("cloud_cover", coalesce(col("cloud_cover"), col("api_cloud_cover"))) \
            .withColumn("weather_code", coalesce(col("weather_code"), col("api_weather_code"))) \
            .withColumn("visibility_km", coalesce(col("visibility_km"), col("api_visibility") / 1000.0))
        
        # Create derived attributes from existing data (no new API fields)
        print("  Creating derived attributes from existing data...")
        df_silver = df_silver \
            .withColumn("temperature_dewpoint_spread",
                col("temperature_2m") - col("dewpoint_2m")) \
            .withColumn("heat_index",
                when(
                    (col("temperature_2m") > 27) & (col("relative_humidity_2m") > 40),
                    col("temperature_2m") + 0.5555 * (col("relative_humidity_2m") / 100.0 * 6.11 * 
                        expr("exp(5417.7530 * ((1/273.16) - (1/(273.15 + temperature_2m))))") - 10)
                ).otherwise(col("temperature_2m"))) \
            .withColumn("wind_chill",
                when(
                    (col("temperature_2m") < 10) & (col("wind_speed_10m") > 4.8),
                    13.12 + 0.6215 * col("temperature_2m") - 
                    11.37 * expr("power(wind_speed_10m, 0.16)") +
                    0.3965 * col("temperature_2m") * expr("power(wind_speed_10m, 0.16)")
                ).otherwise(col("temperature_2m"))) \
            .withColumn("feels_like_temperature",
                coalesce(col("heat_index"), col("wind_chill"), col("temperature_2m"))) \
            .withColumn("precipitation_intensity",
                when(col("precipitation") > 0, col("precipitation")).otherwise(lit(0.0))) \
            .withColumn("is_raining",
                when(col("precipitation") > 0.1, lit(1)).otherwise(lit(0))) \
            .withColumn("is_snowing",
                when(col("snowfall") > 0.1, lit(1)).otherwise(lit(0)))
        
        print("✓ Data enrichment complete - missing values filled from API")
    else:
        print("  No API data retrieved, continuing with original silver data")
else:
    print("  No New York stations found, skipping API enrichment")

# ============================================================================
# PART 1: HOURLY AGGREGATES
# ============================================================================
print("\n[Part 1] Creating hourly aggregates...")

df_hourly = df_silver.groupBy(
    "station_id", "station_name", "station_region",
    "station_latitude", "station_longitude", "station_elevation", "station_timezone",
    "year", "month", "day", "hour", "season"
).agg(
    # Temperature metrics
    avg("temperature_2m").alias("avg_temperature_2m"),
    sql_min("temperature_2m").alias("min_temperature_2m"),
    sql_max("temperature_2m").alias("max_temperature_2m"),
    stddev("temperature_2m").alias("std_temperature_2m"),
    variance("temperature_2m").alias("var_temperature_2m"),
    
    # Humidity metrics
    avg("relative_humidity_2m").alias("avg_humidity_2m"),
    sql_min("relative_humidity_2m").alias("min_humidity_2m"),
    sql_max("relative_humidity_2m").alias("max_humidity_2m"),
    
    # Dewpoint metrics
    avg("dewpoint_2m").alias("avg_dewpoint_2m"),
    sql_min("dewpoint_2m").alias("min_dewpoint_2m"),
    sql_max("dewpoint_2m").alias("max_dewpoint_2m"),
    
    # Pressure metrics
    avg("pressure_msl").alias("avg_pressure_msl"),
    sql_min("pressure_msl").alias("min_pressure_msl"),
    sql_max("pressure_msl").alias("max_pressure_msl"),
    stddev("pressure_msl").alias("std_pressure_msl"),
    
    # Wind metrics
    avg("wind_speed_10m").alias("avg_wind_speed_10m"),
    sql_max("wind_speed_10m").alias("max_wind_speed_10m"),
    sql_min("wind_speed_10m").alias("min_wind_speed_10m"),
    sql_max("wind_gusts_10m").alias("max_wind_gusts_10m"),
    avg("wind_direction_10m").alias("avg_wind_direction_10m"),
    stddev("wind_direction_10m").alias("std_wind_direction_10m"),
    
    # Precipitation metrics
    sql_sum("precipitation").alias("total_precipitation"),
    sql_max("precipitation").alias("max_precipitation_intensity"),
    sql_sum("rain").alias("total_rain"),
    sql_sum("snowfall").alias("total_snowfall"),
    count(when(col("precipitation") > 0, 1)).alias("precipitation_events"),
    count(when(col("precipitation") > 2.5, 1)).alias("heavy_precipitation_events"),
    
    # Visibility and cloud metrics
    avg("visibility_km").alias("avg_visibility_km"),
    sql_min("visibility_km").alias("min_visibility_km"),
    avg("cloud_cover").alias("avg_cloud_cover"),
    sql_max("cloud_cover").alias("max_cloud_cover"),
    
    # Data quality
    avg("data_completeness").alias("avg_data_completeness"),
    count("*").alias("observation_count")
)

# Calculate derived metrics
df_hourly = df_hourly \
    .withColumn("temperature_range", col("max_temperature_2m") - col("min_temperature_2m")) \
    .withColumn("pressure_range", col("max_pressure_msl") - col("min_pressure_msl")) \
    .withColumn("humidity_range", col("max_humidity_2m") - col("min_humidity_2m")) \
    .withColumn("wind_speed_range", col("max_wind_speed_10m") - col("min_wind_speed_10m"))

print(f"✓ Hourly aggregates created: {df_hourly.count():,} records")

# ============================================================================
# PART 2: TIME-SERIES FEATURES (LAG/LEAD)
# ============================================================================
print("\n[Part 2] Computing time-series features...")

window_spec = Window.partitionBy("station_id").orderBy("year", "month", "day", "hour")

df_hourly = df_hourly \
    .withColumn("prev_hour_temp", lag("avg_temperature_2m", 1).over(window_spec)) \
    .withColumn("next_hour_temp", lead("avg_temperature_2m", 1).over(window_spec)) \
    .withColumn("prev_hour_pressure", lag("avg_pressure_msl", 1).over(window_spec)) \
    .withColumn("next_hour_pressure", lead("avg_pressure_msl", 1).over(window_spec)) \
    .withColumn("prev_hour_wind", lag("avg_wind_speed_10m", 1).over(window_spec)) \
    .withColumn("prev_hour_humidity", lag("avg_humidity_2m", 1).over(window_spec)) \
    .withColumn("prev_hour_precip", lag("total_precipitation", 1).over(window_spec))

# Calculate trends
df_hourly = df_hourly \
    .withColumn(
        "temperature_trend",
        when(col("prev_hour_temp").isNull(), lit("unknown"))
        .when(col("avg_temperature_2m") > col("prev_hour_temp") + 1.0, lit("rising"))
        .when(col("avg_temperature_2m") < col("prev_hour_temp") - 1.0, lit("falling"))
        .otherwise(lit("stable"))
    ) \
    .withColumn(
        "pressure_trend",
        when(col("prev_hour_pressure").isNull(), lit("unknown"))
        .when(col("avg_pressure_msl") > col("prev_hour_pressure") + 1.0, lit("rising"))
        .when(col("avg_pressure_msl") < col("prev_hour_pressure") - 1.0, lit("falling"))
        .otherwise(lit("stable"))
    ) \
    .withColumn(
        "temperature_change_rate",
        when(col("prev_hour_temp").isNotNull(),
             col("avg_temperature_2m") - col("prev_hour_temp"))
        .otherwise(None)
    ) \
    .withColumn(
        "pressure_change_rate",
        when(col("prev_hour_pressure").isNotNull(),
             col("avg_pressure_msl") - col("prev_hour_pressure"))
        .otherwise(None)
    ) \
    .withColumn(
        "wind_change_rate",
        when(col("prev_hour_wind").isNotNull(),
             col("avg_wind_speed_10m") - col("prev_hour_wind"))
        .otherwise(None)
    )

print("✓ Time-series features computed")

# ============================================================================
# PART 3: ROLLING WINDOW FEATURES
# ============================================================================
print("\n[Part 3] Computing rolling window features...")

window_3h = Window.partitionBy("station_id").orderBy("year", "month", "day", "hour").rowsBetween(-2, 0)
window_6h = Window.partitionBy("station_id").orderBy("year", "month", "day", "hour").rowsBetween(-5, 0)
window_12h = Window.partitionBy("station_id").orderBy("year", "month", "day", "hour").rowsBetween(-11, 0)
window_24h = Window.partitionBy("station_id").orderBy("year", "month", "day", "hour").rowsBetween(-23, 0)

df_hourly = df_hourly \
    .withColumn("temp_3h_avg", avg("avg_temperature_2m").over(window_3h)) \
    .withColumn("temp_3h_std", stddev("avg_temperature_2m").over(window_3h)) \
    .withColumn("precip_3h_total", sql_sum("total_precipitation").over(window_3h)) \
    .withColumn("wind_3h_max", sql_max("max_wind_speed_10m").over(window_3h)) \
    .withColumn("pressure_3h_avg", avg("avg_pressure_msl").over(window_3h)) \
    .withColumn("temp_6h_avg", avg("avg_temperature_2m").over(window_6h)) \
    .withColumn("temp_6h_std", stddev("avg_temperature_2m").over(window_6h)) \
    .withColumn("precip_6h_total", sql_sum("total_precipitation").over(window_6h)) \
    .withColumn("pressure_6h_trend", 
        sql_max("avg_pressure_msl").over(window_6h) - sql_min("avg_pressure_msl").over(window_6h)) \
    .withColumn("temp_12h_avg", avg("avg_temperature_2m").over(window_12h)) \
    .withColumn("temp_12h_range", 
        sql_max("avg_temperature_2m").over(window_12h) - sql_min("avg_temperature_2m").over(window_12h)) \
    .withColumn("precip_12h_total", sql_sum("total_precipitation").over(window_12h)) \
    .withColumn("temp_24h_avg", avg("avg_temperature_2m").over(window_24h)) \
    .withColumn("temp_24h_range",
        sql_max("avg_temperature_2m").over(window_24h) - sql_min("avg_temperature_2m").over(window_24h)) \
    .withColumn("precip_24h_total", sql_sum("total_precipitation").over(window_24h))

print("✓ Rolling window features computed")

# ============================================================================
# PART 4: DAILY AGGREGATES
# ============================================================================
print("\n[Part 4] Creating daily aggregates...")

df_daily = df_silver.groupBy(
    "station_id", "station_name", "station_region",
    "station_latitude", "station_longitude", "station_elevation", "station_timezone",
    "year", "month", "day", "season"
).agg(
    # Temperature
    avg("temperature_2m").alias("daily_avg_temp"),
    sql_min("temperature_2m").alias("daily_min_temp"),
    sql_max("temperature_2m").alias("daily_max_temp"),
    stddev("temperature_2m").alias("daily_temp_std"),
    (sql_max("temperature_2m") - sql_min("temperature_2m")).alias("diurnal_temp_range"),
    
    # Humidity
    avg("relative_humidity_2m").alias("daily_avg_humidity"),
    sql_min("relative_humidity_2m").alias("daily_min_humidity"),
    sql_max("relative_humidity_2m").alias("daily_max_humidity"),
    
    # Dewpoint
    avg("dewpoint_2m").alias("daily_avg_dewpoint"),
    sql_min("dewpoint_2m").alias("daily_min_dewpoint"),
    sql_max("dewpoint_2m").alias("daily_max_dewpoint"),
    
    # Pressure
    avg("pressure_msl").alias("daily_avg_pressure"),
    sql_max("pressure_msl").alias("daily_max_pressure"),
    sql_min("pressure_msl").alias("daily_min_pressure"),
    stddev("pressure_msl").alias("daily_pressure_std"),
    
    # Wind
    avg("wind_speed_10m").alias("daily_avg_wind_speed"),
    sql_max("wind_speed_10m").alias("daily_max_wind_speed"),
    sql_max("wind_gusts_10m").alias("daily_max_wind_gust"),
    count(when(col("wind_speed_10m") > 30, 1)).alias("high_wind_hours"),
    count(when(col("wind_speed_10m") > 50, 1)).alias("extreme_wind_hours"),
    
    # Precipitation
    sql_sum("precipitation").alias("daily_total_precipitation"),
    sql_max("precipitation").alias("daily_max_precip_intensity"),
    sql_sum("rain").alias("daily_total_rain"),
    sql_sum("snowfall").alias("daily_total_snowfall"),
    count(when(col("precipitation") > 0, 1)).alias("precipitation_hours"),
    count(when(col("precipitation") > 2.5, 1)).alias("heavy_precip_hours"),
    
    # Visibility and Cloud
    avg("visibility_km").alias("daily_avg_visibility"),
    sql_min("visibility_km").alias("daily_min_visibility"),
    count(when(col("visibility_km") < 1.0, 1)).alias("fog_hours"),
    avg("cloud_cover").alias("daily_avg_cloud_cover"),
    
    # Data quality
    avg("data_completeness").alias("daily_data_completeness"),
    count("*").alias("daily_observation_count")
)

# Add daily event flags
df_daily = df_daily \
    .withColumn("extreme_temp_day",
        when((col("daily_max_temp") > 35) | (col("daily_min_temp") < -20), lit(1)).otherwise(lit(0))) \
    .withColumn("precipitation_day",
        when(col("daily_total_precipitation") > 0.1, lit(1)).otherwise(lit(0))) \
    .withColumn("heavy_precipitation_day",
        when(col("daily_total_precipitation") > 10.0, lit(1)).otherwise(lit(0))) \
    .withColumn("windy_day",
        when(col("daily_max_wind_speed") > 40, lit(1)).otherwise(lit(0))) \
    .withColumn("foggy_day",
        when(col("fog_hours") > 0, lit(1)).otherwise(lit(0)))

print(f"✓ Daily aggregates created: {df_daily.count():,} records")

# ============================================================================
# PART 5: MONTHLY AGGREGATES
# ============================================================================
print("\n[Part 5] Creating monthly aggregates...")

df_monthly = df_daily.groupBy(
    "station_id", "station_name", "station_region",
    "station_latitude", "station_longitude", "station_elevation", "station_timezone",
    "year", "month"
).agg(
    # Temperature
    avg("daily_avg_temp").alias("monthly_avg_temp"),
    sql_min("daily_min_temp").alias("monthly_min_temp"),
    sql_max("daily_max_temp").alias("monthly_max_temp"),
    avg("diurnal_temp_range").alias("monthly_avg_diurnal_range"),
    sql_max("diurnal_temp_range").alias("monthly_max_diurnal_range"),
    
    # Precipitation
    sql_sum("daily_total_precipitation").alias("monthly_total_precipitation"),
    avg("daily_total_precipitation").alias("monthly_avg_daily_precip"),
    sql_max("daily_total_precipitation").alias("monthly_max_daily_precip"),
    sql_sum("precipitation_day").alias("precipitation_days"),
    sql_sum("heavy_precipitation_day").alias("heavy_precipitation_days"),
    sql_sum("daily_total_rain").alias("monthly_total_rain"),
    sql_sum("daily_total_snowfall").alias("monthly_total_snowfall"),
    
    # Wind
    avg("daily_avg_wind_speed").alias("monthly_avg_wind_speed"),
    sql_max("daily_max_wind_gust").alias("monthly_max_wind_gust"),
    sql_sum("windy_day").alias("windy_days"),
    
    # Pressure
    avg("daily_avg_pressure").alias("monthly_avg_pressure"),
    stddev("daily_avg_pressure").alias("monthly_pressure_variability"),
    
    # Events
    sql_sum("extreme_temp_day").alias("extreme_temp_days"),
    sql_sum("foggy_day").alias("foggy_days"),
    sql_sum("fog_hours").alias("total_fog_hours"),
    
    # Data quality
    avg("daily_data_completeness").alias("monthly_data_completeness"),
    count("*").alias("days_in_month")
)

print(f"✓ Monthly aggregates created: {df_monthly.count():,} records")

# ============================================================================
# PART 6: ML FEATURE ENGINEERING
# ============================================================================
print("\n[Part 6] Engineering ML features...")

df_hourly_ml = df_hourly \
    .withColumn("hour_sin", expr("sin(2 * pi() * hour / 24)")) \
    .withColumn("hour_cos", expr("cos(2 * pi() * hour / 24)")) \
    .withColumn("month_sin", expr("sin(2 * pi() * month / 12)")) \
    .withColumn("month_cos", expr("cos(2 * pi() * month / 12)")) \
    .withColumn("day_of_year", dayofyear(expr("to_date(concat(year, '-', month, '-', day), 'yyyy-M-d')"))) \
    .withColumn("day_sin", expr("sin(2 * pi() * day_of_year / 365)")) \
    .withColumn("day_cos", expr("cos(2 * pi() * day_of_year / 365)")) \
    .withColumn("latitude_rad", expr("radians(station_latitude)")) \
    .withColumn("longitude_rad", expr("radians(station_longitude)")) \
    .withColumn("elevation_km", col("station_elevation") / 1000.0)

# Calculate heat index (feels-like temperature in hot conditions)
df_hourly_ml = df_hourly_ml.withColumn(
    "heat_index",
    when((col("avg_temperature_2m") > 27) & (col("avg_humidity_2m") > 40),
         col("avg_temperature_2m") + 
         0.5555 * (col("avg_humidity_2m") / 100.0 * 6.11 * 
                   expr("exp(5417.7530 * ((1/273.16) - (1/(273.15 + avg_temperature_2m))))") - 10))
    .otherwise(col("avg_temperature_2m"))
)

# Calculate wind chill (feels-like temperature in cold conditions)
df_hourly_ml = df_hourly_ml.withColumn(
    "wind_chill",
    when((col("avg_temperature_2m") < 10) & (col("avg_wind_speed_10m") > 4.8),
         13.12 + 0.6215 * col("avg_temperature_2m") - 
         11.37 * expr("power(avg_wind_speed_10m, 0.16)") +
         0.3965 * col("avg_temperature_2m") * expr("power(avg_wind_speed_10m, 0.16)"))
    .otherwise(col("avg_temperature_2m"))
)

# Calculate comfort index (0-100, higher is more comfortable)
df_hourly_ml = df_hourly_ml.withColumn(
    "comfort_index",
    when(
        100 - (sql_abs(col("avg_temperature_2m") - 20) * 2 +
               sql_abs(col("avg_humidity_2m") - 50) * 0.5 +
               when(col("avg_wind_speed_10m") > 30, 20).otherwise(0) +
               when(col("total_precipitation") > 0, 10).otherwise(0)) > 100,
        100
    ).when(
        100 - (sql_abs(col("avg_temperature_2m") - 20) * 2 +
               sql_abs(col("avg_humidity_2m") - 50) * 0.5 +
               when(col("avg_wind_speed_10m") > 30, 20).otherwise(0) +
               when(col("total_precipitation") > 0, 10).otherwise(0)) < 0,
        0
    ).otherwise(
        100 - (sql_abs(col("avg_temperature_2m") - 20) * 2 +
               sql_abs(col("avg_humidity_2m") - 50) * 0.5 +
               when(col("avg_wind_speed_10m") > 30, 20).otherwise(0) +
               when(col("total_precipitation") > 0, 10).otherwise(0))
    )
)

# Calculate temperature-humidity index
df_hourly_ml = df_hourly_ml.withColumn(
    "temperature_humidity_index",
    col("avg_temperature_2m") - 0.55 * (1 - col("avg_humidity_2m") / 100.0) * 
    (col("avg_temperature_2m") - 14.4)
)

print("✓ ML features created")

# ============================================================================
# PART 7: ANOMALY DETECTION FEATURES
# ============================================================================
print("\n[Part 7] Computing anomaly detection features...")

station_window = Window.partitionBy("station_id")

df_hourly_ml = df_hourly_ml \
    .withColumn("temp_p25", percentile_approx("avg_temperature_2m", 0.25).over(station_window)) \
    .withColumn("temp_p75", percentile_approx("avg_temperature_2m", 0.75).over(station_window)) \
    .withColumn("temp_p10", percentile_approx("avg_temperature_2m", 0.10).over(station_window)) \
    .withColumn("temp_p90", percentile_approx("avg_temperature_2m", 0.90).over(station_window)) \
    .withColumn("pressure_p25", percentile_approx("avg_pressure_msl", 0.25).over(station_window)) \
    .withColumn("pressure_p75", percentile_approx("avg_pressure_msl", 0.75).over(station_window)) \
    .withColumn("wind_p90", percentile_approx("max_wind_speed_10m", 0.90).over(station_window))

df_hourly_ml = df_hourly_ml \
    .withColumn("temp_iqr", col("temp_p75") - col("temp_p25")) \
    .withColumn("pressure_iqr", col("pressure_p75") - col("pressure_p25")) \
    .withColumn("temp_anomaly",
        when((col("avg_temperature_2m") < col("temp_p25") - 1.5 * col("temp_iqr")) |
             (col("avg_temperature_2m") > col("temp_p75") + 1.5 * col("temp_iqr")),
             lit(1)).otherwise(lit(0))) \
    .withColumn("pressure_anomaly",
        when((col("avg_pressure_msl") < col("pressure_p25") - 1.5 * col("pressure_iqr")) |
             (col("avg_pressure_msl") > col("pressure_p75") + 1.5 * col("pressure_iqr")),
             lit(1)).otherwise(lit(0))) \
    .withColumn("wind_anomaly",
        when(col("max_wind_speed_10m") > col("wind_p90"),
             lit(1)).otherwise(lit(0))) \
    .withColumn("extreme_temp",
        when((col("avg_temperature_2m") < col("temp_p10")) | 
             (col("avg_temperature_2m") > col("temp_p90")),
             lit(1)).otherwise(lit(0)))

print("✓ Anomaly detection features computed")

# ============================================================================
# STATISTICS AND OUTPUT
# ============================================================================
print("\n" + "="*70)
print("GOLD LAYER STATISTICS")
print("="*70)
print(f"Hourly Records: {df_hourly_ml.count():,}")
print(f"Daily Records: {df_daily.count():,}")
print(f"Monthly Records: {df_monthly.count():,}")

print("\n" + "="*70)
print("SAMPLE HOURLY AGGREGATES")
print("="*70)
df_hourly_ml.select(
    "station_name", "year", "month", "day", "hour",
    "avg_temperature_2m", "temperature_trend", "total_precipitation",
    "comfort_index", "temp_anomaly"
).show(5, truncate=False)

print("\n" + "="*70)
print("SAMPLE DAILY AGGREGATES")
print("="*70)
df_daily.select(
    "station_name", "year", "month", "day",
    "daily_avg_temp", "daily_total_precipitation",
    "precipitation_day", "extreme_temp_day"
).show(5, truncate=False)

# ============================================================================
# WRITE OUTPUTS
# ============================================================================
print(f"\n[{datetime.now()}] Writing Gold layer outputs...")

try:
    Path(GOLD_OUTPUT_PATH).mkdir(parents=True, exist_ok=True)
    
    print("Writing hourly aggregates...")
    df_hourly_ml.write \
        .mode("overwrite") \
        .partitionBy("year", "month") \
        .parquet(f"{GOLD_OUTPUT_PATH}/hourly_aggregates")
    print("✓ Hourly aggregates written")
    
    print("Writing daily aggregates...")
    df_daily.write \
        .mode("overwrite") \
        .partitionBy("year", "month") \
        .parquet(f"{GOLD_OUTPUT_PATH}/daily_aggregates")
    print("✓ Daily aggregates written")
    
    print("Writing monthly aggregates...")
    df_monthly.write \
        .mode("overwrite") \
        .partitionBy("year") \
        .parquet(f"{GOLD_OUTPUT_PATH}/monthly_aggregates")
    print("✓ Monthly aggregates written")
    
    print("\n" + "="*70)
    print("✓ SILVER TO GOLD TRANSFORMATION COMPLETE!")
    print("="*70)
    print(f"Output locations:")
    print(f"  - Hourly: {GOLD_OUTPUT_PATH}/hourly_aggregates")
    print(f"  - Daily: {GOLD_OUTPUT_PATH}/daily_aggregates")
    print(f"  - Monthly: {GOLD_OUTPUT_PATH}/monthly_aggregates")
    print(f"Completed at: {datetime.now()}")
    
except Exception as e:
    print(f"\n✗ ERROR writing data: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\nStopping Spark session...")
    spark.stop()
    print("✓ Spark session stopped successfully.")
    print("\nScript finished.")


