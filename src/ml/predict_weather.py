import sys
from functools import reduce
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, current_date, date_add, date_sub, max as max_, avg, sum, 
    to_date, count, round, dayofyear, sin, cos, lag, lit, expr, when
)
from pyspark.sql.window import Window
from pyspark.ml import PipelineModel

def main():
    spark = SparkSession.builder \
        .appName("Weather_Forecast_Display") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
        .config("spark.cassandra.connection.host", "cassandra") \
        .config("spark.cassandra.connection.port", "9042") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    print("\n==============================================")
    print("       WEATHER FORECAST: TODAY")
    print("==============================================\n")

    raw_df = spark.read \
        .format("org.apache.spark.sql.cassandra") \
        .options(table="raw_weather_data", keyspace="weather_house") \
        .load()

    recent_df = raw_df

    print(" -> Aggregating raw data...")
    daily_df = recent_df.withColumn("date", to_date(col("time"))) \
        .groupBy("location_id", "date").agg(
            round(avg("temperature_2m"), 2).alias("avg_temp_c"),
            round(sum("precipitation"), 2).alias("total_precip_mm"),
            round(avg("relative_humidity_2m"), 2).alias("avg_humidity"),
            round(avg("pressure_msl"), 2).alias("avg_pressure_msl_hpa")
        )

    w_loc = Window.partitionBy("location_id").orderBy("date")
    w_rolling_7d = w_loc.rowsBetween(-6, 0)
    
    features_df = daily_df \
        .withColumn("day_of_year", dayofyear("date")) \
        .withColumn("doy_sin", sin(2 * 3.14159 * col("day_of_year") / 365)) \
        .withColumn("doy_cos", cos(2 * 3.14159 * col("day_of_year") / 365)) \
        .withColumn("rolling_7d_avg_temp_c", avg("avg_temp_c").over(w_rolling_7d)) \
        .withColumn("rolling_7d_total_precip_mm", avg("total_precip_mm").over(w_rolling_7d))

    latest_dates = features_df.groupBy("location_id").agg(max_("date").alias("max_date"))
    target_input_dates = latest_dates.withColumn("input_date", date_sub(col("max_date"), 1))

    f_alias = features_df.alias("f")
    t_alias = target_input_dates.alias("t")
    
    current_weather = f_alias.join(t_alias, 
        (col("f.location_id") == col("t.location_id")) & 
        (col("f.date") == col("t.input_date"))
    ).select("f.*") 
    
    current_weather = current_weather.na.fill(0)
    current_weather.cache()

    active_stations = [row.location_id for row in current_weather.select("location_id").distinct().collect()]
    print(f" -> Found {len(active_stations)} stations with history. Predicting...")

    forecast_dfs = []

    for sid in active_stations:
        station_data = current_weather.filter(col("location_id") == sid)
        
        base_path = f"hdfs://namenode:9000/weather/models/station_{sid}"
        
        try:
            m_temp = PipelineModel.load(f"{base_path}/rf_temp_model")
            m_humid = PipelineModel.load(f"{base_path}/rf_humid_model")
            m_rain = PipelineModel.load(f"{base_path}/rf_rain_model")
            m_snow = PipelineModel.load(f"{base_path}/rf_snow_model")
            
            p1 = m_temp.transform(station_data).withColumnRenamed("prediction", "pred_temp")

            p1 = p1.drop("features", "rawPrediction", "probability")
            
            p2 = m_humid.transform(p1).withColumnRenamed("prediction", "pred_humid")
            p2 = p2.drop("features", "rawPrediction", "probability")
            
            p3 = m_rain.transform(p2).withColumnRenamed("prediction", "pred_rain_prob")
            p3 = p3.drop("features", "rawPrediction", "probability")
            
            final_pred = m_snow.transform(p3).withColumnRenamed("prediction", "pred_snow_prob")
            final_pred = final_pred.drop("features", "rawPrediction", "probability")
            
            forecast_dfs.append(final_pred)
            print(f"    [OK] Station {sid}: Predictions generated.")
        except Exception as e:
            print(f"⚠️ Failed to predict for Station {sid}: {e}")
            continue

    if not forecast_dfs:
        print("❌ No forecasts generated. (Check logs above for specific model loading errors)")
        return

    final_df = reduce(lambda df1, df2: df1.union(df2), forecast_dfs)

    forecast_df = final_df.select(
        col("location_id"),
        col("date").alias("based_on_date"),
        date_add(col("date"), 1).alias("forecast_date"),
        round(col("pred_temp"), 1).alias("pred_temp_c"),
        round(col("pred_humid"), 1).alias("pred_humidity"),
        when(col("pred_rain_prob") == 1.0, "YES").otherwise("NO").alias("pred_is_rain"),
        when(col("pred_snow_prob") == 1.0, "YES").otherwise("NO").alias("pred_is_snow")
    ).orderBy("location_id")

    output_path = "/weather/gold/weather_forecast"
    forecast_df.write.mode("overwrite").parquet(output_path)
    print(f" -> Forecasts saved to {output_path}")
    
    forecast_df.show(20, truncate=False)

if __name__ == "__main__":
    main()