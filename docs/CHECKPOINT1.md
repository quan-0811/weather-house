# Checkpoint 1: General Architecture Documentation

## 1. Summary
WeaHouse is a **Kappa-style** weather analytics platform. It ingests continuous sensor events, cleans and aggregates them **once** in a single streaming pipeline, serves **low-latency** queries for dashboards and alerts, and preserves **a durable historical store** for analytics and machine learning. Offline workloads (ETL, training, batch inference) run **over the same data** without introducing a second serving path.

## 2. Data Flow
![alt text](data-flow.png)
1. **Data Sources from IoT Sensors → Kafka**  
   Devices emit JSON weather readings (temperature, humidity, pressure, wind, rain). Events are published to a Kafka topic partitioned by region/location to scale and preserve per-location order.

2. **Kafka → Spark Structured Streaming (Speed/Processing Layer)**  
   Spark is the real-time processor. It validates schema, handles missing/outlier values, deduplicates late/duplicate events (with watermarking), and computes time-window aggregations and rolling features.

3. **Fan-out from Spark to two destinations**
   - **Cassandra:** Optimized for **real-time queries** by *location + time window* (dashboards, alerting).
   - **Long-Term Storage (HDFS):**  
     - **Raw Zone:** Verbatim events for audit and replay.  
     - **Curated/Silver:** Cleaned and feature-ready data.  
     - **Gold:** Analytics-ready datasets and model outputs.

4. **Offline Branch (Airflow over HDFS)**  
   - Schedules **Raw → Curated** ETL, file compaction, and quality checks.  
   - Orchestrates **model training/evaluation** (Spark MLlib) and **batch inference** that writes predictions to **Gold** (and optionally promotes selected aggregates/predictions to Cassandra for live views).

5. **Consumption & Visualization**  
   - **Real-time dashboards/alerts** read from **Cassandra**.  
   - **Historical BI & ad-hoc analysis** read from **Gold** in HDFS.  
   - End users access **Realtime View** (Cassandra) or **Batch View** (HDFS/Gold) as shown in the diagram.

6. **Platform**  
   - All services (Kafka, Spark jobs, Cassandra, HDFS, Airflow, dashboards) are deployed on **Kubernetes**.


## 3. Logical Layers & Responsibilities

### Ingestion Layer (Kafka)
- High-throughput, durable event log for weather telemetry.  
- Partitions by region/location for scale and locality; retention long enough to support **replays/backfills**.

### Speed / Processing Layer (Spark Structured Streaming)
- Single real-time code path (core of **Kappa**).  
- Functions: schema enforcement, data quality, deduplication, windowed aggregations, rolling features, optional real-time scoring.  
- Provides **exactly-once-like** behavior via checkpoints and idempotent writes.

### Serving Layer (Cassandra)
- Time-series store for **low-latency** queries and alerting.  
- Read patterns: last 1h/6h/24h per location; bounded ranges across days.  
- Chosen for write-heavy workloads, horizontal scale, and availability.

### Long-Term Storage (HDFS)
- **Raw → Curated → Gold** zones to separate concerns: auditability, clean/feature-ready data, and analytics-ready outputs (including model predictions).  
- Enables historical analysis, governance, and efficient batch processing.

### Orchestration (Airflow)
- Governs offline pipelines: curation, compaction, training, batch inference, and **reprocessing/backfills** (either by replaying Kafka within retention or recomputing from Raw).

### Visualization & Access (Grafana / Superset)
- **Live** views from Cassandra; **historical** views from Gold.  
- Clear separation avoids “merge” logic typical of Lambda.

## 4. Tech Stack

- **Messaging:** Apache Kafka  
- **Stream Processing:** Apache Spark Structured Streaming  
- **Serving Database:** Apache Cassandra  
- **Long-Term Storage:** Hadoop HDFS (Raw / Curated / Gold)  
- **Orchestration:** Apache Airflow (offline ETL/ML)  
- **Machine Learning:** Spark MLlib  
- **Dashboards/BI:** Grafana, Apache Superset  
- **Platform:** Kubernetes