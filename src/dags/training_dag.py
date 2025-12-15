from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'data-engineer',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
}

with DAG(
    'weather_model_training',
    default_args=default_args,
    description='Retrains the Weather Forecast Model (Daily)',
    schedule_interval='@daily', 
    start_date=datetime(2023, 11, 30),
    catchup=False,
    tags=['spark', 'mlops', 'training'],
) as dag:

    train_model = BashOperator(
        task_id='train_model',
        bash_command="""
        docker exec spark-master /opt/spark/bin/spark-submit \
        --master spark://spark-master:7077 \
        --deploy-mode client \
        --conf spark.cores.max=2 \
        --conf spark.executor.memory=1024m \
        --conf spark.driver.memory=1024m \
        /opt/spark/src/ml/train_model.py
        """
    )