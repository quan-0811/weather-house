import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lead, when
from pyspark.sql.window import Window
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import RandomForestRegressor
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml import Pipeline

def main():
    spark = SparkSession.builder \
        .appName("Multi_Model_Station_Training") \
        .config("spark.hadoop.fs.defaultFS", "hdfs://namenode:9000") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("WARN")
    print("--- 1. LOADING DATA (Gold Layer) ---")
    
    try:
        df = spark.read.parquet("/weather/gold/ml_features")
    except Exception:
        print("Gold data not found. Please run the Silver-to-Gold job first.")
        return

    # Define the "Tomorrow" Window for Label generation
    w = Window.partitionBy("location_id").orderBy("date")

    # --- PREPARE TARGETS (LABELS) ---
    print(" -> Creating Target Labels...")
    train_df = df.withColumn("label_temp", lead("avg_temp_c", 1).over(w)) \
                 .withColumn("label_humid", lead("avg_humidity", 1).over(w)) \
                 .withColumn("label_rain", when(lead("total_precip_mm", 1).over(w) > 0.0, 1.0).otherwise(0.0)) \
                 .withColumn("label_snow", when(lead("total_snow_cm", 1).over(w) > 0.0, 1.0).otherwise(0.0))
    
    # --- ROBUSTNESS FIXES ---
    # 1. Fill null features with 0 instead of dropping them.
    #    (Fixes issue where first 7 days were dropped due to empty rolling averages)
    train_df = train_df.na.fill(0)

    # 2. Drop only rows where the LABEL is missing (the last day of data)
    train_df = train_df.na.drop(subset=["label_temp"])
    
    # Cache because we will iterate over this dataset many times
    train_df.cache()

    # --- FEATURE SELECTION ---
    feature_cols = [
        "doy_sin", "doy_cos",           # Seasonality
        "avg_pressure_msl_hpa",         # Pressure
        "avg_temp_c", "total_precip_mm", "avg_humidity", # Persistence
        "rolling_7d_avg_temp_c",        # Trends
        "rolling_7d_total_precip_mm"
    ]
    
    valid_cols = [c for c in feature_cols if c in train_df.columns]
    assembler = VectorAssembler(inputCols=valid_cols, outputCol="features")

    # --- STATION LOOP ---
    # Get list of unique stations
    stations = [row.location_id for row in train_df.select("location_id").distinct().collect()]
    print(f" -> Found {len(stations)} active stations. Starting localized training...")

    for sid in stations:
        # Filter data for just this station
        station_data = train_df.filter(col("location_id") == sid)
        
        # Skip if insufficient data for training
        # CHANGED: Lowered threshold from 10 to 2 to ensure it runs on small datasets
        if station_data.count() < 2:
            print(f"    Skipping Station {sid}: Not enough history ({station_data.count()} rows).")
            continue

        # Split Data (80% Train, 20% Test)
        train, test = station_data.randomSplit([0.8, 0.2], seed=42)

        # Helper to Train & Save specific to this station
        def train_and_save(model_type, label_col, model_name):
            if model_type == "regressor":
                rf = RandomForestRegressor(featuresCol="features", labelCol=label_col, numTrees=15, maxDepth=10)
            else:
                rf = RandomForestClassifier(featuresCol="features", labelCol=label_col, numTrees=15, maxDepth=10)
                
            pipeline = Pipeline(stages=[assembler, rf])
            model = pipeline.fit(train)
            
            # SAVE PATH includes the Station ID
            path = f"hdfs://namenode:9000/weather/models/station_{sid}/{model_name}"
            model.write().overwrite().save(path)

        # Train the 4 models for this specific station
        try:
            train_and_save("regressor", "label_temp", "rf_temp_model")
            train_and_save("regressor", "label_humid", "rf_humid_model")
            train_and_save("classifier", "label_rain", "rf_rain_model")
            train_and_save("classifier", "label_snow", "rf_snow_model")
            print(f"    [OK] Station {sid}: Models saved.")
        except Exception as e:
            print(f"    [FAIL] Station {sid}: {e}")

    print("\n--- GLOBAL TRAINING COMPLETE ---")
    train_df.unpersist()

if __name__ == "__main__":
    main()