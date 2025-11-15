# =============================================================================
# WEATHER DATA PRODUCER DOCKERFILE
# =============================================================================
# Purpose: Ingest weather data from external APIs and publish to Kafka
# Role: Fetches weather data, validates against schema, publishes to Kafka topics
# Version: Python 3.11
# Architecture: 3 producer instances (for 3 Kafka partitions)
# =============================================================================

# Use official Python image as base
# python:3.11-slim - Lightweight Python 3.11 image
# slim variant reduces image size by excluding unnecessary packages
FROM python:3.11-slim

# -----------------------------------------------------------------------------
# Set Working Directory
# -----------------------------------------------------------------------------
# All commands will run from /app directory
# This is where our application code will be located
WORKDIR /app

# -----------------------------------------------------------------------------
# Install System Dependencies
# -----------------------------------------------------------------------------
# gcc, g++: Compilers for building Python packages with C extensions
#           Some Python packages (like cryptography) require compilation
# libffi-dev: Development files for Foreign Function Interface
#             Required by some Python packages
# libssl-dev: OpenSSL development files
#             Required for secure connections (HTTPS, SSL/TLS)
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
# Copy Requirements File
# -----------------------------------------------------------------------------
# Copy requirements.txt first (Docker layer caching optimization)
# If requirements.txt doesn't change, Docker can reuse the pip install layer
# This speeds up subsequent builds
COPY requirements.txt /app/requirements.txt

# -----------------------------------------------------------------------------
# Install Python Dependencies
# -----------------------------------------------------------------------------
# Install all Python packages listed in requirements.txt
# --no-cache-dir: Don't cache pip downloads (reduces image size)
# These packages enable the producer to:
#   - Connect to Kafka (kafka-python)
#   - Validate data schemas (pydantic)
#   - Make HTTP requests to weather APIs (requests)
#   - Handle dates/times (python-dateutil)
#   - Process JSON data (json - built-in, but other packages may need it)
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Copy Application Code
# -----------------------------------------------------------------------------
# Copy producer source code from project
# src/producer/ - Contains weather_producer.py and related code
# data/ - Contains weather station data and fetch scripts
# schemas/ - Contains weather_schema.py for data validation
# Note: Build context should be project root, so paths are relative to that
COPY src/producer /app/src/producer
COPY data /app/data
COPY schemas /app/schemas

# -----------------------------------------------------------------------------
# Set Python Path
# -----------------------------------------------------------------------------
# Add /app to PYTHONPATH so Python can find our modules
# This allows imports like: from src.producer import weather_producer
ENV PYTHONPATH=/app:$PYTHONPATH

# -----------------------------------------------------------------------------
# Environment Variables for Producer Configuration
# -----------------------------------------------------------------------------
# KAFKA_BOOTSTRAP_SERVERS: Comma-separated list of Kafka broker addresses
#                          Format: host1:port1,host2:port2,host3:port3
#                          Producer connects to these brokers to publish messages
#                          Overridden in docker-compose.yml for each producer instance
ENV KAFKA_BOOTSTRAP_SERVERS=kafka-1:9092,kafka-2:9093,kafka-3:9094

# KAFKA_TOPIC_EVENTS: Kafka topic name for weather events
#                     Matches topic created in create-topics.sh
#                     Producer publishes raw weather data to this topic
ENV KAFKA_TOPIC_EVENTS=weather-events

# KAFKA_TOPIC_AGGREGATES: Kafka topic name for weather aggregates
#                         Producer may publish aggregated data here (if doing pre-aggregation)
ENV KAFKA_TOPIC_AGGREGATES=weather-aggregates

# KAFKA_TOPIC_ALERTS: Kafka topic name for weather alerts
#                     Producer may publish alerts here (if doing alert detection)
ENV KAFKA_TOPIC_ALERTS=weather-alerts

# PRODUCER_ID: Unique identifier for this producer instance
#              Used for logging and monitoring
#              Overridden in docker-compose.yml (producer-1, producer-2, producer-3)
ENV PRODUCER_ID=producer-1

# PRODUCER_INTERVAL_SECONDS: How often (in seconds) to fetch and publish data
#                            Set to 60 (1 minute) - fetch data every minute
#                            Adjust based on data source update frequency
ENV PRODUCER_INTERVAL_SECONDS=60

# PRODUCER_BATCH_SIZE: Number of messages to batch before sending to Kafka
#                      Set to 10 - send messages in batches of 10
#                      Improves throughput and reduces network overhead
ENV PRODUCER_BATCH_SIZE=10

# PRODUCER_ACKS: Kafka acknowledgment setting
#                all: Wait for all in-sync replicas to acknowledge (most reliable)
#                Alternatives: 1 (leader only), 0 (no acknowledgment)
ENV PRODUCER_ACKS=all

# PRODUCER_RETRIES: Number of retries for failed message sends
#                   Set to 3 - retry up to 3 times before giving up
ENV PRODUCER_RETRIES=3

# PRODUCER_MAX_IN_FLIGHT_REQUESTS: Maximum number of unacknowledged requests
#                                   Set to 5 for better throughput
#                                   Lower values improve ordering guarantees
ENV PRODUCER_MAX_IN_FLIGHT_REQUESTS=5

# PRODUCER_COMPRESSION_TYPE: Compression algorithm for messages
#                            snappy: Fast compression, good balance of speed and size
#                            Reduces network bandwidth and storage
ENV PRODUCER_COMPRESSION_TYPE=snappy

# WEATHER_API_URL: URL of weather data API
#                  Overridden in docker-compose.yml or set to actual API endpoint
#                  Example: https://api.open-meteo.com/v1/forecast
ENV WEATHER_API_URL=

# WEATHER_API_KEY: API key for weather data service (if required)
#                  Set via docker-compose.yml secrets or environment variables
#                  Keep sensitive - don't hardcode in Dockerfile
ENV WEATHER_API_KEY=

# LOG_LEVEL: Logging level for the producer
#            INFO: Log informational messages and above
#            Alternatives: DEBUG (verbose), WARNING, ERROR
ENV LOG_LEVEL=INFO

# -----------------------------------------------------------------------------
# Expose Ports
# -----------------------------------------------------------------------------
# No ports need to be exposed - producer only makes outbound connections
# Producer connects to Kafka brokers (no incoming connections)

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------
# Check if producer process is running
# Uses ps to check if Python process is alive
# - interval: Check every 30 seconds
# - timeout: Wait 10 seconds for response
# - retries: Mark unhealthy after 3 consecutive failures
# - start-period: Grace period during startup (30 seconds)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=30s \
    CMD ps aux | grep -v grep | grep "weather_producer" || exit 1

# -----------------------------------------------------------------------------
# Default Command
# -----------------------------------------------------------------------------
# Run the weather producer script
# python -u: Unbuffered output (logs appear immediately)
# src/producer/weather_producer.py: Main producer script
# The script will:
#   1. Connect to Kafka brokers
#   2. Fetch weather data from API
#   3. Validate data against weather_schema.py
#   4. Publish messages to Kafka topics
#   5. Repeat at configured interval
CMD ["python", "-u", "src/producer/weather_producer.py"]

