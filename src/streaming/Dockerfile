# =============================================================================
# WEATHER DATA CONSUMER DOCKERFILE
# =============================================================================
# Purpose: Consume weather data from Kafka topics for monitoring and debugging
# Role: Reads messages from Kafka, validates schemas, logs/processes data
# Version: Python 3.11
# Architecture: 3 consumer instances (for 3 Kafka partitions)
# Note: This is different from Spark Structured Streaming (which also consumes Kafka)
#       This consumer is for monitoring, debugging, or simple processing
# =============================================================================

# Use official Python image as base
# python:3.11-slim - Lightweight Python 3.11 image
FROM python:3.11-slim

# -----------------------------------------------------------------------------
# Set Working Directory
# -----------------------------------------------------------------------------
WORKDIR /app

# -----------------------------------------------------------------------------
# Install System Dependencies
# -----------------------------------------------------------------------------
# gcc, g++: Compilers for building Python packages with C extensions
# libffi-dev: Development files for Foreign Function Interface
# libssl-dev: OpenSSL development files
# curl: For downloading and health checks
# netcat-openbsd: For network connectivity checks
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libffi-dev \
        libssl-dev \
        curl \
        netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Create Requirements File
# -----------------------------------------------------------------------------
# Create requirements.txt with necessary packages
# kafka-python: Kafka client library for consuming messages
# pydantic: Data validation library (for weather_schema.py)
# python-dateutil: Date/time parsing utilities
RUN echo "kafka-python==2.0.2" > requirements.txt && \
    echo "pydantic==2.5.0" >> requirements.txt && \
    echo "python-dateutil==2.8.2" >> requirements.txt

# -----------------------------------------------------------------------------
# Install Python Dependencies
# -----------------------------------------------------------------------------
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Copy Application Code
# -----------------------------------------------------------------------------
# Copy consumer source code from project
# src/streaming/ - Contains weather_consumer.py and related code
# schemas/ - Contains weather_schema.py for data validation
# Note: Build context should be project root, so paths are relative to that
COPY src/streaming /app/src/streaming
COPY schemas /app/schemas

# -----------------------------------------------------------------------------
# Set Python Path
# -----------------------------------------------------------------------------
ENV PYTHONPATH=/app:$PYTHONPATH

# -----------------------------------------------------------------------------
# Environment Variables for Consumer Configuration
# -----------------------------------------------------------------------------
# KAFKA_BOOTSTRAP_SERVERS: Comma-separated list of Kafka broker addresses
#                          Format: host1:port1,host2:port2,host3:port3
#                          Consumer connects to these brokers to consume messages
ENV KAFKA_BOOTSTRAP_SERVERS=kafka-1:9092,kafka-2:9093,kafka-3:9094

# KAFKA_TOPIC_EVENTS: Kafka topic name for weather events
#                     Consumer reads from this topic
ENV KAFKA_TOPIC_EVENTS=weather-events

# KAFKA_TOPIC_AGGREGATES: Kafka topic name for weather aggregates
#                         Consumer may read from this topic
ENV KAFKA_TOPIC_AGGREGATES=weather-aggregates

# KAFKA_TOPIC_ALERTS: Kafka topic name for weather alerts
#                     Consumer may read from this topic
ENV KAFKA_TOPIC_ALERTS=weather-alerts

# KAFKA_GROUP_ID: Consumer group identifier
#                 All consumers with same group_id share partitions
#                 Set to 'weather-consumers' - all 3 consumers in same group
#                 Kafka will distribute 3 partitions across 3 consumers (1 partition each)
ENV KAFKA_GROUP_ID=weather-consumers

# CONSUMER_ID: Unique identifier for this consumer instance
#              Used for logging and monitoring
#              Overridden in docker-compose.yml (consumer-1, consumer-2, consumer-3)
ENV CONSUMER_ID=consumer-1

# CONSUMER_AUTO_OFFSET_RESET: What to do when no offset is found
#                             earliest: Start from beginning of topic
#                             latest: Start from end of topic (only new messages)
#                             none: Throw exception if no offset found
ENV CONSUMER_AUTO_OFFSET_RESET=earliest

# CONSUMER_ENABLE_AUTO_COMMIT: Automatically commit offsets after consuming
#                              Set to true - Kafka tracks consumption progress
#                              Set to false for manual offset management (more control)
ENV CONSUMER_ENABLE_AUTO_COMMIT=true

# CONSUMER_AUTO_COMMIT_INTERVAL_MS: How often (milliseconds) to commit offsets
#                                   Set to 5000 (5 seconds)
ENV CONSUMER_AUTO_COMMIT_INTERVAL_MS=5000

# CONSUMER_MAX_POLL_RECORDS: Maximum number of records to fetch in one poll
#                            Set to 100 - fetch up to 100 messages at a time
#                            Larger values improve throughput but increase memory usage
ENV CONSUMER_MAX_POLL_RECORDS=100

# CONSUMER_FETCH_MIN_BYTES: Minimum bytes to fetch in one request
#                           Set to 1 - fetch even small messages immediately
#                           Larger values improve throughput but increase latency
ENV CONSUMER_FETCH_MIN_BYTES=1

# CONSUMER_FETCH_MAX_WAIT_MS: Maximum time (milliseconds) to wait for data
#                             Set to 500 (0.5 seconds)
#                             Waits up to this time to accumulate more data
ENV CONSUMER_FETCH_MAX_WAIT_MS=500

# LOG_LEVEL: Logging level for the consumer
#            INFO: Log informational messages and above
ENV LOG_LEVEL=INFO

# -----------------------------------------------------------------------------
# Expose Ports
# -----------------------------------------------------------------------------
# No ports need to be exposed - consumer only makes outbound connections

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------
# Check if consumer process is running
# - interval: Check every 30 seconds
# - timeout: Wait 10 seconds for response
# - retries: Mark unhealthy after 3 consecutive failures
# - start-period: Grace period during startup (30 seconds)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=30s \
    CMD ps aux | grep -v grep | grep "weather_consumer" || exit 1

# -----------------------------------------------------------------------------
# Default Command
# -----------------------------------------------------------------------------
# Run the weather consumer script
# python -u: Unbuffered output (logs appear immediately)
# src/streaming/weather_consumer.py: Main consumer script
# The script will:
#   1. Connect to Kafka brokers
#   2. Subscribe to Kafka topics
#   3. Consume messages from assigned partitions
#   4. Validate data against weather_schema.py
#   5. Process/log messages
#   6. Commit offsets
CMD ["python", "-u", "src/streaming/weather_consumer.py"]

