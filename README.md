# WeaHouse 🌤️🏠
> **Capstone Project for IT4043E - Big Data Storage & Processing**
> **Hanoi University of Science and Technology (HUST)**

**WeaHouse** is an end-to-end Big Data pipeline designed to ingest, process, and visualize meteorological data in real-time. Built on the **Kappa Architecture**, it handles high-velocity sensor data for immediate dashboarding (Hot Path) while simultaneously archiving and refining data for long-term Machine Learning analysis (Cold Path).

## 🏗 Architecture

The system follows the **Kappa Architecture**, utilizing a unified log-based streaming platform (Kafka) to feed both real-time and batch layers.

1.  **Ingestion Layer:** Python-based producers simulate IoT weather sensors, sending JSON telemetry to **Apache Kafka**.
2.  **Speed Layer (Hot Path):** **Spark Structured Streaming** consumes data immediately, writing latest values to **Cassandra** for low-latency queries.
3.  **Batch Layer (Cold Path):** Spark archives raw data to **HDFS** (Bronze), cleans/deduplicates it (Silver), and aggregates it (Gold) for the ML pipeline.
4.  **Serving Layer:** A **Streamlit** dashboard visualizes real-time metrics and historical forecasts.
5.  **Orchestration:** **Apache Airflow** manages the daily ML model retraining and batch ETL jobs.

## 🛠 Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Ingestion** | Apache Kafka | Message Broker (3 Brokers, 3x Replication) |
| **Processing** | Apache Spark | Structured Streaming & MLlib (Random Forest) |
| **Storage (Data Lake)** | HDFS | Hadoop Distributed File System (Medallion Architecture) |
| **Storage (NoSQL)** | Cassandra | Time-series storage for real-time dashboard |
| **Orchestration** | Apache Airflow | DAG scheduling for ETL and Model Training |
| **Visualization** | Streamlit | Interactive Data Dashboard |
| **Containerization** | Docker | Docker Compose for infrastructure management |

## 📋 Prerequisites

Before running the project, ensure you have the following installed:

* **Docker Desktop** (configured with at least 16GB RAM free recommended)
* **Conda** (Anaconda or Miniconda)
* **Git**

---

## ⚙️ Installation & Setup

1. **Clone the repository**
```bash
git clone https://github.com/quan-0811/weather-house.git
cd weather-house
```

2. **Download data**
Data is uploaded by us at [Google Drive Data Link](https://drive.google.com/drive/folders/1dHQyCVHXg7G2Df2VbJHSi9wcNMJ_qFqv?usp=drive_link). Please download the data and place it under `data/final/` folder. The path to the data file should look like this: `data/final/final_data.csv`.



2. **Make Scripts Executable**
Give execute permissions to the helper scripts:
```bash
chmod +x scripts/*.sh
```

3. **Setup Python Environment**
Run the setup script. This will check for Conda, create the `weahouse_env` environment (Python 3.10), and install required libraries.
```bash
./scripts/setup_env.sh
```

4. **Activate Environment**
Once the setup script finishes, activate the environment:
```bash
conda activate weahouse_env
```

## 🚀 Running the Pipeline

We have provided a unified start script that automates the entire deployment process.

**Run the start script:**

```bash
./scripts/start.sh
```

**What this script does:**

1. Starts the Docker Infrastructure (Kafka, Zookeeper, HDFS, Spark, Cassandra).
2. Creates the Kafka topic `weather-events` with 3 partitions and 3x replication.
3. Initializes the Cassandra Keyspace and Table schema.
4. Submits the Spark Structured Streaming job to the cluster.
5. **Starts the Data Producer:** The script ends by running the local Python producer. You will see logs of data being sent in your terminal.

> **Note:** To stop the producer but keep the infrastructure running, press `Ctrl+C`.

## 🛑 Stopping the Pipeline

To shut down the system and clean up resources, run the stop script.

```bash
./scripts/stop.sh
```

> **Warning:** This script runs `docker-compose down -v`, which **removes all volumes**. Any data stored in HDFS or Cassandra will be deleted.

## 🌐 Accessing Interfaces

| Service | URL | Credentials (if any) |
| --- | --- | --- |
| **Weather Dashboard** | [http://localhost:8501](https://www.google.com/search?q=http://localhost:8501) | - |
| **Airflow UI** | [http://localhost:8082](https://www.google.com/search?q=http://localhost:8082) | `admin` / `admin` |
| **Spark Master** | [http://localhost:8081](https://www.google.com/search?q=http://localhost:8081) | - |
| **Kafka UI** | [http://localhost:8080](https://www.google.com/search?q=http://localhost:8080) | - |
| **HDFS NameNode** | [http://localhost:9870](https://www.google.com/search?q=http://localhost:9870) | - |