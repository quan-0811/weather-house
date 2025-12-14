#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Ensure we are running from the project root directory
cd "$(dirname "$0")/.."

echo "=================================================="
echo "   Starting Weather House Data Pipeline"
echo "=================================================="

# 1. Start Infrastructure
echo "[1/5] Starting Docker containers (Kafka, ZK, HDFS, Spark, Cassandra)..."
docker-compose up -d

echo "      Waiting 30 seconds for services to stabilize..."
sleep 30

# 2. Create Kafka Topic
echo "[2/5] Creating Kafka topic 'weather-events'..."
docker exec kafka1 kafka-topics --create --if-not-exists \
    --topic weather-events \
    --bootstrap-server kafka1:29092 \
    --partitions 3 \
    --replication-factor 3 || true

# 2.5 Initialize Cassandra Schema (NEW STEP)
echo "[3/5] Initializing Cassandra Schema..."
docker cp scripts/schema.cql cassandra:/schema.cql

echo "      Waiting for Cassandra to accept connections..."
# Retry loop: Tries to connect every 2 seconds until successful
while ! docker exec cassandra cqlsh -e "DESCRIBE KEYSPACES" > /dev/null 2>&1; do
    sleep 2
done

echo "      Cassandra is UP. Applying schema..."
docker exec cassandra cqlsh -f /schema.cql
echo "      Cassandra schema created successfully."

# 3. Submit Spark Streaming Job
echo "[4/5] Deploying code and submitting Spark Streaming job..."

# FIX: Added 'com.datastax.spark:spark-cassandra-connector' to packages
docker exec -d -u 0 spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.cores.max=1 \
  --conf spark.executor.memory=1024m \
  --conf spark.driver.memory=512m \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,com.datastax.spark:spark-cassandra-connector_2.12:3.5.0 \
  --py-files /opt/spark/src/streaming/schema.py \
  /opt/spark/src/streaming/weather_streaming.py

echo "      Spark job submitted in background."
echo "      Waiting 15 seconds for initialization..."
sleep 15

# VALIDATION: Print logs to check for startup errors
echo "      --- SPARK CONTAINER LOGS (Start) ---"
docker logs spark-master --tail 10
echo "      --- SPARK CONTAINER LOGS (End) ---"

# 4. Run Producer
echo "[5/5] Starting Weather Producer (Local Python)..."
echo "      The producer will now send data to Kafka."
echo "      Press Ctrl+C to stop the producer."
python src/producer/weather_producer.py