import sys
from functools import reduce
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, to_date, date_sub, date_add, max as max_, avg, sum, 
    round, dayofyear, sin, cos, lit, when, unix_timestamp
)
from pyspark.sql.window import Window
from pyspark.ml import PipelineModel

def main():
    # 1. Initialize Spark (No Cassandra config needed anymore)
    spark = SparkSession.builder \
        .appName("Weather_Forecast_Gold") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    print("\n==============================================")
    print("       WEATHER FORECAST: SILVER TO GOLD")
    print("==============================================\n")

    # 2. Read Silver Data (Fact Table)
    silver_df = spark.read.parquet("/weather/silver/fact_weather")

    # 3. Optimization: Filter for Recent Data Only
    print(" -> Determining extraction window...")
    
    # Get the absolute latest timestamp in the dataset
    max_ts = silver_df.agg(max_("event_time")).collect()[0][0]
    
    if not max_ts:
        print("❌ No data found in Silver layer.")
        return

    # Filter: Keep only data from (Max Date - 30 Days) onwards
    cutoff_ts = date_sub(lit(max_ts), 30)
    
    recent_df = silver_df.filter(col("event_time") >= cutoff_ts)
    print(f" -> Processing data from {cutoff_ts} to {max_ts}...")

    # 4. Daily Aggregation (Hourly -> Daily)
    daily_df = recent_df.withColumn("date", to_date(col("event_time"))) \
        .groupBy("location_id", "date").agg(
            round(avg("temperature_2m"), 2).alias("avg_temp_c"),
            round(sum("precipitation"), 2).alias("total_precip_mm"),
            round(avg("relative_humidity_2m"), 2).alias("avg_humidity"),
            round(avg("pressure_msl"), 2).alias("avg_pressure_msl_hpa")
        )

    # 5. Feature Engineering (Rolling Windows)
    w_loc = Window.partitionBy("location_id").orderBy("date")
    w_rolling_7d = w_loc.rowsBetween(-6, 0)
    
    features_df = daily_df \
        .withColumn("day_of_year", dayofyear("date")) \
        .withColumn("doy_sin", sin(2 * 3.14159 * col("day_of_year") / 365)) \
        .withColumn("doy_cos", cos(2 * 3.14159 * col("day_of_year") / 365)) \
        .withColumn("rolling_7d_avg_temp_c", avg("avg_temp_c").over(w_rolling_7d)) \
        .withColumn("rolling_7d_total_precip_mm", avg("total_precip_mm").over(w_rolling_7d))

    # 6. Select "Today's" Feature Vector for Prediction
    latest_dates = features_df.groupBy("location_id").agg(max_("date").alias("max_date"))
    
    # We select the row corresponding to the MOST RECENT complete day
    current_weather = features_df.join(latest_dates, 
        (features_df.location_id == latest_dates.location_id) & 
        (features_df.date == latest_dates.max_date)
    ).select(features_df["*"])
    
    current_weather = current_weather.na.fill(0)
    current_weather.cache()

    active_stations = [row.location_id for row in current_weather.select("location_id").distinct().collect()]
    print(f" -> Found {len(active_stations)} stations to forecast.")

    # 7. Model Inference Loop
    forecast_dfs = []

    for sid in active_stations:
        # Filter features for this specific station
        station_data = current_weather.filter(col("location_id") == sid)
        
        base_path = f"hdfs://namenode:9000/weather/models/station_{sid}"
        
        try:
            # Load Pre-trained Spark ML Models
            m_temp = PipelineModel.load(f"{base_path}/rf_temp_model")
            m_humid = PipelineModel.load(f"{base_path}/rf_humid_model")
            m_rain = PipelineModel.load(f"{base_path}/rf_rain_model")
            m_snow = PipelineModel.load(f"{base_path}/rf_snow_model")
            
            # Chain Predictions
            p1 = m_temp.transform(station_data).withColumnRenamed("prediction", "pred_temp").drop("features", "rawPrediction", "probability")
            p2 = m_humid.transform(p1).withColumnRenamed("prediction", "pred_humid").drop("features", "rawPrediction", "probability")
            p3 = m_rain.transform(p2).withColumnRenamed("prediction", "pred_rain_prob").drop("features", "rawPrediction", "probability")
            final_pred = m_snow.transform(p3).withColumnRenamed("prediction", "pred_snow_prob").drop("features", "rawPrediction", "probability")
            
            forecast_dfs.append(final_pred)
            # print(f"    [OK] Station {sid}") # Optional: Uncomment for verbosity
        except Exception as e:
            print(f"⚠️ Failed to predict for Station {sid}: {e}")
            continue

    if not forecast_dfs:
        print("❌ No forecasts generated.")
        return

    # 8. Combine and Save Results
    final_df = reduce(lambda df1, df2: df1.union(df2), forecast_dfs)

    forecast_output = final_df.select(
        col("location_id"),
        col("date").alias("based_on_date"),
        date_add(col("date"), 1).alias("forecast_date"), # Predict for tomorrow
        round(col("pred_temp"), 1).alias("pred_temp_c"),
        round(col("pred_humid"), 1).alias("pred_humidity"),
        when(col("pred_rain_prob") >= 0.5, "YES").otherwise("NO").alias("pred_is_rain"),
        when(col("pred_snow_prob") >= 0.5, "YES").otherwise("NO").alias("pred_is_snow")
    ).orderBy("location_id")

    # Save to Gold Layer
    output_path = "/weather/gold/weather_forecast"
    forecast_output.write.mode("overwrite").parquet(output_path)
    print(f" -> Forecasts saved to {output_path}")
    
    forecast_output.show(10, truncate=False)

if __name__ == "__main__":
    main()