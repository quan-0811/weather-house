h DAG(
    dag_id="weather_data_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@hourly",
    catchup=False,
    tags=["weather", "demo"],)