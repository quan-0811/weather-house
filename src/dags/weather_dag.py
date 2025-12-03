from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'weather_etl_pipeline',
    default_args=default_args,
    description='Periodic Weather ETL (Bronze -> Silver -> Gold)',
    schedule_interval='@hourly',   # Runs once every hour
    start_date=datetime(2023, 11, 30),
    catchup=False,
) as dag:

    # --- TASK 1: CLEANING & IMPUTATION (Silver Layer) ---
    silver_transformation = BashOperator(
        task_id='transform_silver',
        bash_command="""
        docker exec spark-master /opt/spark/bin/spark-submit \
        --master spark://spark-master:7077 \
        --conf spark.cores.max=2 \
        --conf spark.executor.memory=512m \
        --conf spark.driver.memory=512m \
        --deploy-mode client \
        --py-files /opt/spark/src/streaming/schema.py \
        /opt/spark/src/batch/bronze_to_silver.py
        """
    )

    # --- TASK 2: AGGREGATION (Gold Layer) ---
    gold_aggregation = BashOperator(
        task_id='aggregate_gold',
        bash_command="""
        docker exec spark-master /opt/spark/bin/spark-submit \
        --master spark://spark-master:7077 \
        --conf spark.cores.max=2 \
        --conf spark.executor.memory=512m \
        --conf spark.driver.memory=512m \
        --deploy-mode client \
        /opt/spark/src/batch/silver_to_gold.py
        """
    )

    # Define Workflow
    silver_transformation >> gold_aggregation