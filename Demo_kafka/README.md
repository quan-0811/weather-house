# Kafka Demos - Setup & Run Guide

## Prerequisites

1. **Kafka installed** (via Homebrew on macOS):
   ```bash
   brew install kafka
   ```

2. **Python kafka-python library**:
   ```bash
   pip install kafka-python
   ```

3. **Kafka & ZooKeeper running**:
   ```bash
   # Terminal 1 - ZooKeeper
   zookeeper-server-start /opt/homebrew/etc/kafka/zookeeper.properties
   
   # Terminal 2 - Kafka Broker
   kafka-server-start /opt/homebrew/etc/kafka/server.properties
   ```

## Demo 1: CLI Basics

Run the script to create a topic:
```bash
bash demo1_cli.sh
```

Then follow on-screen instructions to test producer/consumer via CLI.

## Demo 2: Python Weather Producer & Consumer

**Step 1:** Start the consumer (Terminal 1):
```bash
python3 demo2_consumer.py
```

**Step 2:** Start the producer (Terminal 2):
```bash
python3 demo2_producer.py
```

You'll see simulated weather data flowing from producer to consumer in real-time!

## Demo 3: Consumer Group Load Balancing

**Step 1:** Start 2-3 consumer instances (separate terminals):
```bash
# Terminal 1
python3 demo3_consumer_group.py

# Terminal 2
python3 demo3_consumer_group.py

# Terminal 3
python3 demo3_consumer_group.py
```

**Step 2:** Start the producer (Terminal 4):
```bash
python3 demo2_producer.py
```

Observe how Kafka distributes partitions across consumer instances. Each partition is consumed by exactly one consumer in the group!

## Clean Up

Stop all consumers (Ctrl+C), then delete test topics:
```bash
kafka-topics --bootstrap-server localhost:9092 --delete --topic weather-test
kafka-topics --bootstrap-server localhost:9092 --delete --topic weather-readings
```
