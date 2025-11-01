from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import random, json, pandas as pd

def extract_weather_data():
    data = {
        "temperature": random.uniform(20, 35),
        "humidity": random.uniform(40, 80),
        "timestamp": datetime.now().isoformat()
    }
    with open("data/sample_weather.json", "w") as f:
        json.dump(data, f)
    print("Extracted data:", data)

def transform_weather_data():
    with open("data/sample_weather.json", "r") as f:
        data = json.load(f)
    df = pd.DataFrame([data])
    df["feels_like"] = df["temperature"] - ((100 - df["humidity"]) / 20)
    df.to_csv("data/transformed_weather.csv", index=False)
    print("Transformed data saved.")

def load_to_storage():
    print("Pretend: Uploading transformed_weather.csv to storage...")
    print("Done.")

with DAG(
    dag_id="weather_data_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@hourly",
    catchup=False,
    tags=["weather", "demo"],
) as dag:

    extract = PythonOperator(
        task_id="extract_weather_data",
        python_callable=extract_weather_data
    )
    transform = PythonOperator(
        task_id="transform_weather_data",
        python_callable=transform_weather_data
    )
    load = PythonOperator(
        task_id="load_to_storage",
        python_callable=load_to_storage
    )

    extract >> transform >> load
