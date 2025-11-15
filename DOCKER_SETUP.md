# Docker Setup Documentation

## Overview

This document describes the Docker setup for the Weather House project, implementing a Kappa Architecture data pipeline.

## Architecture

```
Data → Kafka (3 brokers) → Spark Structured Streaming → HDFS / Cassandra
                                                          ↓
                                                    Superset (from Cassandra)
                                                          ↓
HDFS: Bronze → Silver → Gold (via Spark batch jobs scheduled by Airflow)
```

## Components

### 1. Zookeeper
- **Purpose**: Coordination service for Kafka cluster
- **Ports**: 2181 (client), 2888 (peer), 3888 (election)
- **Volumes**: `zookeeper-data`

### 2. Kafka (3 Brokers)
- **Purpose**: Distributed streaming platform
- **Brokers**: kafka-1 (9092), kafka-2 (9093), kafka-3 (9094)
- **Topics**: 
  - `weather-events` (3 partitions, replication factor 3)
  - `weather-aggregates` (3 partitions, replication factor 3)
  - `weather-alerts` (3 partitions, replication factor 3)
- **Volumes**: `kafka-data-1`, `kafka-data-2`, `kafka-data-3`

### 3. Spark Cluster
- **Master**: spark-master (Web UI: 18080, RPC: 7077)
- **Workers**: spark-worker-1, spark-worker-2, spark-worker-3 (Web UI: 8081)
- **Purpose**: Distributed processing for streaming and batch jobs

### 4. HDFS Cluster
- **NameNode**: hdfs-namenode (RPC: 9000, Web UI: 9870)
- **Secondary NameNode**: hdfs-secondarynamenode (Web UI: 9868)
- **DataNodes**: hdfs-datanode-1, hdfs-datanode-2, hdfs-datanode-3 (Web UI: 9864)
- **Purpose**: Distributed file system for bronze/silver/gold layers
- **Volumes**: `hdfs-namenode-data`, `hdfs-datanode-data-1/2/3`, `hdfs-secondarynamenode-data`

### 5. Cassandra
- **Purpose**: NoSQL database for real-time queries
- **Ports**: 9042 (CQL), 7000 (gossip)
- **Keyspace**: `weather_ks`
- **Tables**: `weather_events`, `weather_aggregates`, `weather_alerts`
- **Volume**: `cassandra-data`

### 6. Airflow
- **Webserver**: airflow-webserver (Port: 8080)
- **Scheduler**: airflow-scheduler
- **Purpose**: Workflow orchestration for batch ETL jobs
- **Database**: PostgreSQL (postgres-airflow)
- **Default credentials**: admin / admin

### 7. Superset
- **Purpose**: Business intelligence and visualization
- **Port**: 8088
- **Database**: PostgreSQL (postgres-superset)
- **Default credentials**: admin / admin (change on first login)

### 8. Producers (3 instances)
- **Purpose**: Ingest weather data and publish to Kafka
- **Instances**: producer-1, producer-2, producer-3
- **Partitions**: Each producer can write to different partitions

### 9. Consumers (3 instances)
- **Purpose**: Consume from Kafka for monitoring/debugging
- **Instances**: consumer-1, consumer-2, consumer-3
- **Group**: `weather-consumers` (partitions distributed across consumers)

### 10. Supporting Services
- **PostgreSQL (Airflow)**: Port 5432
- **PostgreSQL (Superset)**: Port 5433 (host)
- **Redis**: Port 6379

## Port Summary

| Service | Port | Description |
|---------|------|-------------|
| Zookeeper | 2181 | Client port |
| Kafka-1 | 9092 | Broker 1 |
| Kafka-2 | 9093 | Broker 2 |
| Kafka-3 | 9094 | Broker 3 |
| Spark Master | 18080 | Web UI |
| Spark Master | 7077 | RPC |
| HDFS NameNode | 9870 | Web UI |
| HDFS NameNode | 9000 | RPC |
| Cassandra | 9042 | CQL |
| Airflow | 8080 | Web UI |
| Superset | 8088 | Web UI |
| PostgreSQL (Airflow) | 5432 | Database |
| PostgreSQL (Superset) | 5433 | Database (host) |
| Redis | 6379 | Cache |

## Usage

### Start All Services
```bash
docker-compose up -d
```

### Stop All Services
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f [service-name]
```

### Access Web UIs
- **Airflow**: http://localhost:8080 (admin/admin)
- **Superset**: http://localhost:8088 (admin/admin)
- **Spark Master**: http://localhost:18080
- **HDFS NameNode**: http://localhost:9870
- **Kafka**: Use kafka-console-consumer/producer tools

### Build Individual Services
```bash
docker-compose build [service-name]
```

## Data Flow

1. **Producers** fetch weather data and publish to Kafka topics
2. **Spark Structured Streaming** consumes from Kafka and writes to:
   - **Cassandra** (for real-time queries)
   - **HDFS Bronze layer** (raw data)
3. **Airflow** schedules Spark batch jobs:
   - Bronze → Silver (cleaned data)
   - Silver → Gold (aggregated data)
4. **Superset** queries Cassandra for visualization

## Notes

- All Dockerfiles include extensive comments explaining each configuration
- Build context is set to project root for all services
- Health checks are configured for all services
- Services have proper dependencies and startup order
- Volumes are used for persistent data storage
- Network isolation via custom Docker network

## Troubleshooting

1. **Port conflicts**: Check if ports are already in use
2. **Health check failures**: Wait for services to fully start (check logs)
3. **Kafka topics not created**: Check kafka-topics container logs
4. **HDFS not accessible**: Ensure NameNode is healthy before starting DataNodes
5. **Cassandra connection issues**: Wait for Cassandra to fully start (120s startup period)

## File Structure

```
weather-house/
├── zookeeper/
│   └── Dockerfile
├── kafka/
│   ├── Dockerfile
│   └── create-topics.sh
├── spark/
│   ├── Dockerfile
│   └── requirements.txt
├── hdfs/
│   ├── Dockerfile
│   └── conf/
│       ├── core-site.xml
│       └── hdfs-site.xml
├── cassandra/
│   ├── Dockerfile
│   └── init.cql
├── airflow/
│   └── Dockerfile
├── superset/
│   └── Dockerfile
├── ingestion/
│   ├── Dockerfile
│   └── requirements.txt
├── src/
│   └── streaming/
│       └── Dockerfile
└── docker-compose.yml
```

