#!/bin/bash

# Wait for all Kafka brokers to be ready
echo "Waiting for Kafka brokers to be ready..."
for port in 9092 9093 9094; do
  while ! nc -z localhost $port; do
    echo "Waiting for Kafka on port $port..."
    sleep 2
  done
  echo "Kafka broker on port $port is ready"
done

echo "All Kafka brokers are ready. Creating topics..."

# Create weather-events topic (8 partitions, replication factor 3)
kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 3 \
  --partitions 8 \
  --topic weather-events \
  --if-not-exists \
  --config retention.ms=604800000 \
  --config compression.type=snappy \
  --config min.insync.replicas=2

# Create weather-alerts topic (5 partitions, replication factor 3)
kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 3 \
  --partitions 5 \
  --topic weather-alerts \
  --if-not-exists \
  --config retention.ms=86400000 \
  --config min.insync.replicas=2

# Create weather-aggregates topic (8 partitions, replication factor 3)
kafka-topics --create \
  --bootstrap-server localhost:9092 \
  --replication-factor 3 \
  --partitions 8 \
  --topic weather-aggregates \
  --if-not-exists \
  --config retention.ms=604800000 \
  --config compression.type=snappy \
  --config min.insync.replicas=2

echo "Topics created successfully!"

# List topics with details
echo -e "\n=== Topic List ==="
kafka-topics --list --bootstrap-server localhost:9092

echo -e "\n=== Topic Details ==="
kafka-topics --describe --bootstrap-server localhost:9092
