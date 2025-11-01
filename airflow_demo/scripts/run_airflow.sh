#!/bin/bash
# Simple script to initialize and run Airflow locally

export AIRFLOW_HOME=$(pwd)
pip install -r requirements.txt

# Initialize database
airflow db init

# Create user
airflow users create     --username admin     --firstname Admin     --lastname User     --role Admin     --email admin@example.com     --password admin

# Start webserver and scheduler
airflow webserver -p 8080 &
airflow scheduler
