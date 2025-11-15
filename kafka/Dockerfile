# =============================================================================
# APACHE KAFKA DOCKERFILE
# =============================================================================
# Purpose: Distributed streaming platform for real-time data ingestion
# Role: Receives weather data from producers, stores in topics, serves consumers
# Version: Apache Kafka 3.5.0 (with Zookeeper, not KRaft)
# Architecture: 3 brokers for high availability and fault tolerance
# =============================================================================

# Use official Kafka image as base
# This image contains Kafka binaries, Zookeeper client, and Java runtime
FROM apache/kafka:3.5.0

# -----------------------------------------------------------------------------
# Switch to Root for Configuration
# -----------------------------------------------------------------------------
# Kafka runs as kafka user, but we need root to modify config files
USER root

# -----------------------------------------------------------------------------
# Create Kafka Data and Log Directories
# -----------------------------------------------------------------------------
# /var/lib/kafka/data: Storage for Kafka log segments (actual message data)
#                      Each topic partition is stored as a log file here
# /var/lib/kafka/logs: Kafka application logs (not message data)
#                      Contains broker startup logs, errors, etc.
RUN mkdir -p /var/lib/kafka/data /var/lib/kafka/logs && \
    chown -R kafka:kafka /var/lib/kafka

# -----------------------------------------------------------------------------
# Copy Topic Creation Script
# -----------------------------------------------------------------------------
# This script creates Kafka topics on startup
# Topics: weather-events, weather-aggregates, weather-alerts
# Each topic has 3 partitions (for 3 producers/consumers) and replication factor 3
COPY create-topics.sh /usr/local/bin/create-topics.sh

# Make script executable
# chmod +x: Adds execute permission so the script can be run
RUN chmod +x /usr/local/bin/create-topics.sh && \
    chown kafka:kafka /usr/local/bin/create-topics.sh

# -----------------------------------------------------------------------------
# Environment Variables for Kafka Configuration
# -----------------------------------------------------------------------------
# KAFKA_BROKER_ID: Unique identifier for this Kafka broker (0, 1, 2 for 3 brokers)
#                  Must be unique across all brokers in the cluster
#                  Overridden in docker-compose.yml for each broker instance
ENV KAFKA_BROKER_ID=0

# KAFKA_ZOOKEEPER_CONNECT: Connection string to Zookeeper ensemble
#                          Format: host1:port1,host2:port2,...
#                          Kafka uses Zookeeper for:
#                          - Broker registration and discovery
#                          - Topic configuration storage
#                          - Leader election for partitions
#                          - Consumer group coordination
ENV KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181

# KAFKA_LISTENERS: Comma-separated list of listeners (protocol://host:port)
#                  Defines how clients connect to this broker
#                  PLAINTEXT: Unencrypted protocol (for internal Docker network)
#                  Format: PLAINTEXT://0.0.0.0:9092 (listen on all interfaces)
#                  Port 9092 is the default Kafka port
#                  Overridden in docker-compose.yml for each broker (9092, 9093, 9094)
ENV KAFKA_LISTENERS=PLAINTEXT://0.0.0.0:9092

# KAFKA_ADVERTISED_LISTENERS: How this broker advertises itself to clients
#                             Clients use this address to connect
#                             Must match the listener but with the external hostname
#                             Format: PLAINTEXT://broker-hostname:port
#                             Overridden in docker-compose.yml for each broker
ENV KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka-1:9092

# KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: Maps listener names to security protocols
#                                       PLAINTEXT:PLAINTEXT means use PLAINTEXT protocol
#                                       Required for PLAINTEXT listeners
ENV KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT

# KAFKA_INTER_BROKER_LISTENER_NAME: Name of listener used for broker-to-broker communication
#                                    Set to PLAINTEXT for unencrypted inter-broker communication
ENV KAFKA_INTER_BROKER_LISTENER_NAME=PLAINTEXT

# KAFKA_LOG_DIRS: Comma-separated list of directories where Kafka stores log files
#                 Each topic partition is stored as a log segment file
#                 Using /var/lib/kafka/data for persistent storage
ENV KAFKA_LOG_DIRS=/var/lib/kafka/data

# KAFKA_NUM_PARTITIONS: Default number of partitions for new topics
#                       Partitions allow parallel processing and scaling
#                       Set to 3 to match our 3 producers/consumers setup
ENV KAFKA_NUM_PARTITIONS=3

# KAFKA_DEFAULT_REPLICATION_FACTOR: Default replication factor for new topics
#                                    Replication factor = number of copies of each partition
#                                    Set to 3 so each partition exists on all 3 brokers
#                                    Provides fault tolerance (can lose 1 broker)
ENV KAFKA_DEFAULT_REPLICATION_FACTOR=3

# KAFKA_MIN_INSYNC_REPLICAS: Minimum number of in-sync replicas required for writes
#                            Producer writes wait for this many replicas to acknowledge
#                            Set to 2: writes succeed if at least 2 brokers have the data
#                            Prevents data loss if 1 broker fails
ENV KAFKA_MIN_INSYNC_REPLICAS=2

# KAFKA_AUTO_CREATE_TOPICS_ENABLE: Automatically create topics when first accessed
#                                   Set to false - we create topics explicitly via script
#                                   Better for production (explicit topic management)
ENV KAFKA_AUTO_CREATE_TOPICS_ENABLE=false

# KAFKA_DELETE_TOPIC_ENABLE: Allow topic deletion via admin tools
#                            Set to true for development/testing
#                            Can be set to false in production for safety
ENV KAFKA_DELETE_TOPIC_ENABLE=true

# KAFKA_LOG_RETENTION_HOURS: How long to retain log segments (default: 168 hours = 7 days)
#                            After this time, old segments are deleted
#                            Set to 168 (7 days) for weather data
ENV KAFKA_LOG_RETENTION_HOURS=168

# KAFKA_LOG_RETENTION_BYTES: Maximum size of log before deleting old segments
#                             Set to -1 (unlimited) - use time-based retention only
ENV KAFKA_LOG_RETENTION_BYTES=-1

# KAFKA_LOG_SEGMENT_BYTES: Size of each log segment file (default: 1GB)
#                          When a segment reaches this size, a new segment is created
#                          1073741824 bytes = 1GB
ENV KAFKA_LOG_SEGMENT_BYTES=1073741824

# KAFKA_LOG_RETENTION_CHECK_INTERVAL_MS: How often to check for log segments to delete
#                                         Default: 300000ms = 5 minutes
ENV KAFKA_LOG_RETENTION_CHECK_INTERVAL_MS=300000

# KAFKA_COMPRESSION_TYPE: Default compression for log segments
#                         'snappy': Fast compression, good balance of speed and size
#                         Reduces disk usage and network traffic
ENV KAFKA_COMPRESSION_TYPE=snappy

# KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: Replication factor for __consumer_offsets topic
#                                          This internal topic stores consumer group offsets
#                                          Set to 3 for high availability
ENV KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=3

# KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: Replication factor for transaction state
#                                                  Set to 3 for high availability
ENV KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=3

# KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: Minimum in-sync replicas for transaction state
#                                       Set to 2 for fault tolerance
ENV KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=2

# KAFKA_NUM_NETWORK_THREADS: Number of threads handling network requests
#                            Default: 8, good for moderate load
ENV KAFKA_NUM_NETWORK_THREADS=8

# KAFKA_NUM_IO_THREADS: Number of threads handling disk I/O
#                       Default: 8, good for moderate load
ENV KAFKA_NUM_IO_THREADS=8

# KAFKA_SOCKET_SEND_BUFFER_BYTES: Socket send buffer size (100KB)
#                                  Larger buffers improve throughput for high-volume producers
ENV KAFKA_SOCKET_SEND_BUFFER_BYTES=102400

# KAFKA_SOCKET_RECEIVE_BUFFER_BYTES: Socket receive buffer size (100KB)
#                                     Larger buffers improve throughput for high-volume consumers
ENV KAFKA_SOCKET_RECEIVE_BUFFER_BYTES=102400

# KAFKA_SOCKET_REQUEST_MAX_BYTES: Maximum size of a request (100MB)
#                                  Prevents large messages from overwhelming the broker
ENV KAFKA_SOCKET_REQUEST_MAX_BYTES=104857600

# KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: Delay before starting consumer group rebalancing
#                                          Default: 3000ms = 3 seconds
#                                          Allows time for all consumers to join before rebalancing
ENV KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS=3000

# KAFKA_HEAP_OPTS: Java heap size for Kafka broker JVM
#                  -Xmx: Maximum heap size (1GB)
#                  -Xms: Initial heap size (1GB)
#                  Set equal to avoid heap resizing overhead
ENV KAFKA_HEAP_OPTS="-Xmx1G -Xms1G"

# KAFKA_JVM_PERFORMANCE_OPTS: JVM performance tuning options
#                             -XX:+UseG1GC: Use G1 garbage collector (good for large heaps)
#                             -XX:MaxGCPauseMillis: Target max GC pause time (20ms)
#                             -XX:InitiatingHeapOccupancyPercent: Start GC at 45% heap usage
#                             -XX:+ExplicitGCInvokesConcurrent: Use concurrent GC for explicit GC calls
#                             -XX:MaxInlineLevel: Maximum method inlining depth
#                             -Djava.awt.headless: Disable GUI (headless mode for servers)
ENV KAFKA_JVM_PERFORMANCE_OPTS="-XX:+UseG1GC -XX:MaxGCPauseMillis=20 -XX:InitiatingHeapOccupancyPercent=45 -XX:+ExplicitGCInvokesConcurrent -XX:MaxInlineLevel=15 -Djava.awt.headless=true"

# -----------------------------------------------------------------------------
# Security: Switch to Non-Root User
# -----------------------------------------------------------------------------
# Run Kafka as 'kafka' user (provided by base image)
# This is a security best practice - don't run services as root
USER kafka

# -----------------------------------------------------------------------------
# Expose Ports
# -----------------------------------------------------------------------------
# 9092: Default Kafka broker port (overridden in docker-compose for each broker)
#        Clients (producers, consumers) connect here
# 9093, 9094: Additional ports for broker 2 and broker 3
EXPOSE 9092 9093 9094

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------
# Check if Kafka broker is responding on its listener port
# Uses kafka-broker-api-versions to verify broker is alive
# - interval: Check every 30 seconds
# - timeout: Wait 10 seconds for response
# - retries: Mark unhealthy after 3 consecutive failures
# - start-period: Grace period during startup (60 seconds - Kafka takes time to start)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD kafka-broker-api-versions --bootstrap-server localhost:9092 || exit 1

# -----------------------------------------------------------------------------
# Default Command
# -----------------------------------------------------------------------------
# The base image has an entrypoint that starts Kafka
# It reads environment variables and generates server.properties
# Kafka will:
# 1. Connect to Zookeeper
# 2. Register itself as a broker
# 3. Start listening on the configured port
# 4. Begin accepting producer/consumer connections
#
# Note: Topic creation script should be run separately (via docker-compose command or init container)

