#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Ensure we are running from the project root directory
cd "$(dirname "$0")/.."

echo "=================================================="
echo "   Starting Weather House Data Pipeline"
echo "=================================================="

# 1. Start Infrastructure
echo "[1/4] Starting Docker containers (Kafka, ZK, HDFS, Spark)..."
docker-compose up -d

echo "      Waiting 30 seconds for services to stabilize..."
sleep 30

# 2. Create Kafka Topic
echo "[2/4] Creating Kafka topic 'weather-events'..."
# FIX: Use kafka1:29092 (internal) instead of localhost:9092 (external)
# so the container can resolve the other brokers correctly.
docker exec kafka1 kafka-topics --create --if-not-exists \
    --topic weather-events \
    --bootstrap-server kafka1:29092 \
    --partitions 3 \
    --replication-factor 3 || true

# 3. Submit Spark Streaming Job
echo "[3/4] Deploying code and submitting Spark Streaming job..."

# FIX: Use '-d' (Detached) instead of '-it' (Interactive).
# This sends the job to the background so the script can continue.
docker exec -d -u 0 spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --conf spark.cores.max=1\
  --conf spark.executor.memory=512m \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  --py-files /opt/spark/src/streaming/schema.py \
  /opt/spark/src/streaming/weather_streaming.py

echo "      Spark job submitted in background."
echo "      Waiting 10 seconds for initialization..."
sleep 10

# VALIDATION: Print the last 10 lines of logs to ensure it didn't crash immediately
echo "      --- SPARK CONTAINER LOGS (Start) ---"
docker logs spark-master --tail 10
echo "      --- SPARK CONTAINER LOGS (End) ---"

# 4. Run Producer
echo "[4/4] Starting Weather Producer (Local Python)..."
echo "      The producer will now send data to Kafka."
echo "      Press Ctrl+C to stop the producer."
python src/producer/weather_producer.py