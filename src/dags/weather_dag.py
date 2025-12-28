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
    description='Periodic Weather ETL (Bronze -> Silver -> Gold -> Forecast)',
    schedule_interval='*/20 * * * *',
    start_date=datetime(2023, 11, 30),
    catchup=False,
    tags=['spark', 'weather', 'etl']
) as dag:

    # 1. SILVER JOB
    silver_transformation = BashOperator(
        task_id='transform_silver',
        bash_command="""
        docker exec spark-master /opt/spark/bin/spark-submit \
        --master spark://spark-master:7077 \
        --deploy-mode client \
        --conf spark.cores.max=1 \
        --conf spark.executor.memory=1024m \
        --conf spark.driver.memory=512m \
        --py-files /opt/spark/src/streaming/schema.py \
        /opt/spark/src/batch/bronze_to_silver.py
        """
    )

    # 2. GOLD JOB
    gold_aggregation = BashOperator(
        task_id='aggregate_gold',
        bash_command="""
        docker exec spark-master /opt/spark/bin/spark-submit \
        --master spark://spark-master:7077 \
        --deploy-mode client \
        --conf spark.cores.max=1 \
        --conf spark.executor.memory=1024m \
        --conf spark.driver.memory=512m \
        /opt/spark/src/batch/silver_to_gold.py
        """
    )

    # 3. PREDICTION JOB
    predict_weather = BashOperator(
        task_id='predict_weather',
        bash_command="""
        docker exec -u 0 spark-master /opt/spark/bin/spark-submit \
        --master spark://spark-master:7077 \
        --deploy-mode client \
        --conf spark.cores.max=1 \
        --conf spark.executor.memory=1024m \
        --conf spark.driver.memory=512m \
        /opt/spark/src/ml/predict_weather.py
        """
    )
    
    silver_transformation >> gold_aggregation >> predict_weather