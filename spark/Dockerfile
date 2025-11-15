# =============================================================================
# APACHE SPARK DOCKERFILE
# =============================================================================
# Purpose: Distributed processing engine for streaming and batch analytics
# Role: Processes data from Kafka, writes to Cassandra/HDFS, runs ML jobs
# Version: Apache Spark 3.5.0 (Bitnami image)
# =============================================================================

FROM bitnami/spark:3.5.0

# -----------------------------------------------------------------------------
# Switch to Root for Package Installation
# -----------------------------------------------------------------------------
USER root

# -----------------------------------------------------------------------------
# Install System Dependencies
# -----------------------------------------------------------------------------
# python3, python3-pip: For PySpark and Python-based jobs
# netcat-openbsd: For health checks and network debugging
# curl: For downloading external packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        netcat-openbsd \
        curl && \
    rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Install Python Dependencies for Spark Jobs
# -----------------------------------------------------------------------------
# requirements.txt should contain:
#   - pyspark==3.5.0 (already included in base image, but explicit is good)
#   - kafka-python (for Kafka integration)
#   - cassandra-driver (for Cassandra writes)
#   - pydantic (for data validation using weather_schema.py)
#   - pandas (for data manipulation)
#   - numpy (for numerical operations)
COPY requirements.txt /opt/spark/requirements.txt
RUN pip3 install --no-cache-dir -r /opt/spark/requirements.txt || true

# -----------------------------------------------------------------------------
# Download Spark Connector JARs
# -----------------------------------------------------------------------------
# These JARs enable Spark to connect to Kafka, Cassandra, and AWS S3

# Kafka-Spark connector (for reading/writing Kafka topics)
RUN curl -L -o /opt/bitnami/spark/jars/spark-sql-kafka-0-10_2.12-3.5.0.jar \
    https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.5.0/spark-sql-kafka-0-10_2.12-3.5.0.jar

# Cassandra-Spark connector (for writing to Cassandra)
RUN curl -L -o /opt/bitnami/spark/jars/spark-cassandra-connector_2.12-3.4.1.jar \
    https://repo1.maven.org/maven2/com/datastax/spark/spark-cassandra-connector_2.12/3.4.1/spark-cassandra-connector_2.12-3.4.1.jar

# Kafka clients library (required by Kafka connector)
RUN curl -L -o /opt/bitnami/spark/jars/kafka-clients-3.5.0.jar \
    https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.5.0/kafka-clients-3.5.0.jar

# Commons Pool (required by Kafka connector)
RUN curl -L -o /opt/bitnami/spark/jars/commons-pool2-2.11.1.jar \
    https://repo1.maven.org/maven2/org/apache/commons/commons-pool2/2.11.1/commons-pool2-2.11.1.jar

# Spark Token Provider (required by Kafka connector)
RUN curl -L -o /opt/bitnami/spark/jars/spark-token-provider-kafka-0-10_2.12-3.5.0.jar \
    https://repo1.maven.org/maven2/org/apache/spark/spark-token-provider-kafka-0-10_2.12/3.5.0/spark-token-provider-kafka-0-10_2.12-3.5.0.jar

# -----------------------------------------------------------------------------
# Create Application Directories
# -----------------------------------------------------------------------------
# /opt/spark-apps/jobs - Spark job scripts (streaming, batch, ML)
# /opt/spark-apps/scripts - Helper scripts (data quality, utils)
# /opt/spark-apps/checkpoints - Spark Structured Streaming checkpoints
RUN mkdir -p /opt/spark-apps/jobs \
             /opt/spark-apps/scripts \
             /opt/spark-apps/checkpoints

# -----------------------------------------------------------------------------
# Copy Spark Job Code and Schemas
# -----------------------------------------------------------------------------
# Note: These files will be copied from build context in docker-compose.yml
# The build context should be set to project root, so paths are relative to that
# src/streaming/ - Spark Structured Streaming jobs (Kafka → Cassandra/HDFS)
# src/batch/ - Batch processing jobs (Bronze → Silver → Gold)
# schemas/ - Data schemas (weather_schema.py) for validation
# These COPY commands assume build context is set to project root in docker-compose
# If building manually, use: docker build -f spark/Dockerfile -t spark:latest .
COPY src/streaming /opt/spark-apps/jobs/streaming
COPY src/batch /opt/spark-apps/jobs/batch
COPY schemas /opt/spark-apps/schemas

# Create scripts directory for utility functions
RUN mkdir -p /opt/spark-apps/scripts

# -----------------------------------------------------------------------------
# Set Environment Variables
# -----------------------------------------------------------------------------
# SPARK_HOME: Spark installation directory (already set by base image)
ENV SPARK_HOME=/opt/bitnami/spark

# SPARK_MASTER_URL: URL of Spark Master (overridden in docker-compose)
# Format: spark://spark-master:7077
ENV SPARK_MASTER_URL=spark://spark-master:7077

# Python path for Spark to find custom modules
ENV PYTHONPATH=/opt/spark-apps:$PYTHONPATH

# Spark defaults (can be overridden in spark-submit or docker-compose)
# SPARK_DRIVER_MEMORY: Memory for driver program (coordinates job)
# SPARK_EXECUTOR_MEMORY: Memory for each executor (processes data)
# SPARK_EXECUTOR_CORES: CPU cores per executor
ENV SPARK_DRIVER_MEMORY=1g \
    SPARK_EXECUTOR_MEMORY=1g \
    SPARK_EXECUTOR_CORES=1

# -----------------------------------------------------------------------------
# Set Permissions
# -----------------------------------------------------------------------------
# Bitnami Spark runs as user ID 1001
# Ensure all application directories are owned by this user
RUN chown -R 1001:1001 /opt/spark-apps

# -----------------------------------------------------------------------------
# Security: Switch to Non-Root User
# -----------------------------------------------------------------------------
# Run Spark as user 1001 (provided by Bitnami base image)
USER 1001

# -----------------------------------------------------------------------------
# Expose Ports
# -----------------------------------------------------------------------------
# Spark Master Ports:
# 8080 - Master Web UI (view cluster status, running applications)
# 7077 - Master RPC (workers and drivers connect here)
# 6066 - Master REST API (submit jobs via REST)
#
# Spark Worker Ports:
# 8081 - Worker Web UI (view worker status, executors)
# 7000 - Worker RPC (communication with master)
#
# Spark Application Ports:
# 4040 - Application Web UI (view job progress, stages, tasks)
# 4041-4043 - Additional application UIs (if multiple apps running)
EXPOSE 8080 7077 6066 8081 7000 4040 4041 4042 4043

# -----------------------------------------------------------------------------
# Health Check (Spark Master)
# -----------------------------------------------------------------------------
# Verifies Spark Master web UI is responding
# This indicates the master is running and accepting connections
# - interval: Check every 30 seconds
# - timeout: Wait 10 seconds for response
# - retries: Mark unhealthy after 3 consecutive failures
# - start-period: Grace period during startup (30 seconds)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=30s \
    CMD curl -f http://localhost:8080/ || exit 1

# -----------------------------------------------------------------------------
# Default Command
# -----------------------------------------------------------------------------
# This Dockerfile is used by BOTH Spark Master and Spark Worker
# The actual command is specified in docker-compose.yml:
#   - Spark Master: /opt/bitnami/scripts/spark/run.sh (SPARK_MODE=master)
#   - Spark Worker: /opt/bitnami/scripts/spark/run.sh (SPARK_MODE=worker)
#
# Bitnami's run.sh script handles:
# - Starting master or worker based on SPARK_MODE environment variable
# - Connecting worker to master via SPARK_MASTER_URL
# - Setting up logging and monitoring
#
# No CMD specified here - docker-compose.yml and SPARK_MODE control behavior
