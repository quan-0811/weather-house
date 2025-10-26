#!/bin/bash

echo "=========================================="
echo "DEMO 1: Kafka CLI Basic Operations"
echo "=========================================="
echo ""

echo "[Step 1] Creating topic 'weather-test' with 3 partitions..."
kafka-topics --bootstrap-server localhost:9092 \
  --create --topic weather-test --partitions 3 --replication-factor 1

echo ""
echo "[Step 2] Listing all topics..."
kafka-topics --bootstrap-server localhost:9092 --list

echo ""
echo "[Step 3] Describing topic 'weather-test'..."
kafka-topics --bootstrap-server localhost:9092 --describe --topic weather-test

echo ""
echo "=========================================="
echo "Now you can:"
echo "  1. Open another terminal and run the consumer:"
echo "     kafka-console-consumer --bootstrap-server localhost:9092 --topic weather-test --from-beginning"
echo ""
echo "  2. Then produce messages:"
echo "     kafka-console-producer --bootstrap-server localhost:9092 --topic weather-test"
echo ""
echo "  3. Type messages and press Enter. Consumer will receive them in real-time!"
echo "=========================================="
