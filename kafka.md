# Apache Kafka - Quick Overview & Hands-On

## What is Kafka?

Apache Kafka is a **distributed event streaming platform** for high-throughput, fault-tolerant, real-time data pipelines. It acts as a central nervous system connecting producers (data sources) to consumers (applications, analytics, ML pipelines).

**Key Properties:**
- **High throughput/low latency**: Millions of events/sec via sequential disk I/O, batching, compression
- **Durability**: Messages replicated across brokers, written to disk
- **Scalability**: Horizontal scaling via partitions and broker clusters
- **Replayability**: Unlike message queues, Kafka retains data for configured periods

## Core Architecture

```
Producers → Topic (Partitions 0,1,2...) → Consumer Groups
              ↓
         Broker Cluster (with replication)
              ↓
         ZooKeeper/KRaft (coordination)
```

**Components:**
- **Producer**: Publishes events to topics
- **Consumer**: Subscribes and reads from topics
- **Topic**: Logical event stream (e.g., `weather-readings`)
- **Partition**: Shard of a topic for parallelism; ordered within partition
- **Offset**: Monotonic ID per message in a partition
- **Broker**: Kafka server storing data
- **Consumer Group**: Load-balanced consumers; each partition assigned to exactly one consumer in group
- **Replication**: Each partition has leader + followers (ISRs) for fault tolerance

**Key Concepts:**
- Messages with **no key** → round-robin across partitions
- Messages with **key** → same key → same partition (ordering guarantee)
- **At-least-once** delivery (default): idempotent consumers handle duplicates
- **Retention**: Time/size-based; enables replay for backfills, debugging, retraining

## Use Case in WeaHouse Project

In our Kappa-architecture weather platform:
1. **IoT sensors → Kafka** (`weather-readings` topic, partitioned by location)
2. **Kafka → Spark Structured Streaming** (real-time processing)
3. **Spark → Cassandra** (low-latency queries) + **HDFS** (historical analytics)
4. **Replay capability**: Reprocess data from Kafka or HDFS Raw zone

## Installation (macOS)

```bash
# Install Kafka via Homebrew
brew install kafka

# Verify
kafka-topics --version
```

## Running Kafka Locally

**Terminal 1 - Start ZooKeeper:**
```bash
zookeeper-server-start /opt/homebrew/etc/kafka/zookeeper.properties
```

**Terminal 2 - Start Kafka Broker:**
```bash
kafka-server-start /opt/homebrew/etc/kafka/server.properties
```

*(Keep both running; Kafka runs on `localhost:9092`)*

## Demo Overview

Three hands-on demos in `Demo_kafka/`:

### Demo 1: CLI Basics (`demo1_cli.sh`)
Create topics, produce/consume via command line

### Demo 2: Python Weather Producer & Consumer
- `demo2_producer.py`: Simulates IoT weather sensors
- `demo2_consumer.py`: Processes weather events

### Demo 3: Consumer Group Load Balancing (`demo3_consumer_group.py`)
Demonstrates partition assignment across multiple consumers

## Running the Demos

```bash
cd Demo_kafka

# Demo 1: CLI operations
bash demo1_cli.sh

# Demo 2: Python producer/consumer
# Terminal 1 (consumer):
python3 demo2_consumer.py
# Terminal 2 (producer):
python3 demo2_producer.py

# Demo 3: Consumer group (open 3 terminals, run same command):
python3 demo3_consumer_group.py
# Terminal 4 (producer):
python3 demo2_producer.py
```

## Common Commands

```bash
# List topics
kafka-topics --bootstrap-server localhost:9092 --list

# Create topic with 3 partitions
kafka-topics --bootstrap-server localhost:9092 \
  --create --topic weather-data --partitions 3 --replication-factor 1

# Describe topic
kafka-topics --bootstrap-server localhost:9092 --describe --topic weather-data

# Console producer
kafka-console-producer --bootstrap-server localhost:9092 --topic weather-data

# Console consumer (from beginning)
kafka-console-consumer --bootstrap-server localhost:9092 \
  --topic weather-data --from-beginning

# Consumer groups
kafka-consumer-groups --bootstrap-server localhost:9092 --list
kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group my-group
```

## References

- [Apache Kafka Docs](https://kafka.apache.org/documentation/)
- [FreeCodeCamp Kafka Handbook](https://www.freecodecamp.org/news/apache-kafka-handbook/)
- [Confluent Developer](https://developer.confluent.io/)
