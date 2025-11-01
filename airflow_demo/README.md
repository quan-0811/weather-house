# Airflow Demo - Weather Data Pipeline ☁️

## Overview
This demo shows a simple **ETL pipeline** for weather data using **Apache Airflow**.
It mimics the architecture where Airflow schedules and manages data flow
(similar to the “data processing” and “workflow orchestration” layers).

---

## Prerequisites
- Python 3.9+
- Virtual environment (optional)
- Airflow 2.9+
- Visual Studio Code (recommended)

---

## Setup
```bash
# Clone repo
git clone 
cd Demo_Airflow

# Install dependencies
pip install -r requirements.txt

# Run Airflow
bash scripts/run_airflow.sh
```

Access Airflow UI at **http://localhost:8080**  
Login using username: `admin`, password: `admin`.

---

## DAG Description
1. **Extract**: Simulates collecting weather data (randomly generated).  
2. **Transform**: Cleans and adds a “feels_like” column.  
3. **Load**: Pretends to upload to a data warehouse or long-term storage.

---

## Folder Structure
```
Demo_Airflow/
│
├── README.md
├── dags/                  # Contains all DAGs
├── data/                  # Local data folder
├── scripts/               # Bash scripts
└── requirements.txt
```

---

## Demo Output
After running, check:
- `data/sample_weather.json`
- `data/transformed_weather.csv`
