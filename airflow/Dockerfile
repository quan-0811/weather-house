# =============================================================================
# APACHE AIRFLOW DOCKERFILE
# =============================================================================
# Purpose: Workflow orchestration and scheduling for batch ETL jobs
# Role: Schedules and monitors Spark batch jobs (Bronze → Silver → Gold)
# Version: Apache Airflow 2.8.0 (Python 3.11)
# Architecture: Single Airflow instance with scheduler and webserver
# =============================================================================

# Use official Airflow image as base
# This image contains Airflow, Python, and all dependencies
# apache/airflow:2.8.0 - Latest stable version
FROM apache/airflow:2.8.0

# -----------------------------------------------------------------------------
# Switch to Root for Package Installation
# -----------------------------------------------------------------------------
# Airflow runs as airflow user, but we need root to install system packages
USER root

# -----------------------------------------------------------------------------
# Install System Dependencies
# -----------------------------------------------------------------------------
# gcc, g++: Compilers for building Python packages with C extensions
# libffi-dev: Development files for Foreign Function Interface (required by some Python packages)
# libssl-dev: OpenSSL development files (for secure connections)
# python3-dev: Python development headers (for building Python extensions)
# curl: For downloading and health checks
# netcat-openbsd: For network connectivity checks
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libffi-dev \
        libssl-dev \
        python3-dev \
        curl \
        netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Switch to Airflow User
# -----------------------------------------------------------------------------
# Switch back to airflow user for Python package installation
# This ensures packages are installed in the correct user's home directory
USER airflow

# -----------------------------------------------------------------------------
# Install Python Dependencies
# -----------------------------------------------------------------------------
# Install additional Python packages required for Airflow DAGs
# These packages enable Airflow to interact with our data pipeline components
#
# apache-airflow-providers-apache-spark: Spark provider for Airflow
#   Enables Airflow to submit Spark jobs, monitor Spark applications
#   Required for running Spark batch jobs from Airflow DAGs
#
# apache-airflow-providers-apache-hdfs: HDFS provider for Airflow
#   Enables Airflow to interact with HDFS (check files, create directories)
#   Required for HDFS operations in DAGs
#
# apache-airflow-providers-apache-kafka: Kafka provider for Airflow
#   Enables Airflow to interact with Kafka (check topics, produce/consume messages)
#   Required for Kafka operations in DAGs
#
# apache-airflow-providers-cassandra: Cassandra provider for Airflow
#   Enables Airflow to interact with Cassandra (run CQL queries)
#   Required for Cassandra operations in DAGs
#
# pydantic: Data validation library (for weather_schema.py)
#   Used in DAGs to validate data schemas
#
# kafka-python: Kafka client library
#   Used in DAGs to interact with Kafka topics
#
# cassandra-driver: Cassandra driver
#   Used in DAGs to interact with Cassandra database
RUN pip install --no-cache-dir \
    apache-airflow-providers-apache-spark \
    apache-airflow-providers-apache-hdfs \
    apache-airflow-providers-apache-kafka \
    apache-airflow-providers-cassandra \
    pydantic==2.5.0 \
    kafka-python==2.0.2 \
    cassandra-driver==3.29.0

# -----------------------------------------------------------------------------
# Copy Airflow DAGs
# -----------------------------------------------------------------------------
# Copy DAG files from project dags/ directory
# DAGs define the workflow: when to run Spark jobs, dependencies, schedules
# These will be placed in $AIRFLOW_HOME/dags (default: /opt/airflow/dags)
# The base image automatically loads DAGs from this directory
# Note: Build context should be project root, so path is relative to that
COPY dags /opt/airflow/dags

# -----------------------------------------------------------------------------
# Set Permissions
# -----------------------------------------------------------------------------
# Ensure DAGs directory is owned by airflow user
# Airflow needs read access to DAG files
RUN chown -R airflow:airflow /opt/airflow/dags

# -----------------------------------------------------------------------------
# Environment Variables for Airflow Configuration
# -----------------------------------------------------------------------------
# AIRFLOW_HOME: Airflow home directory (set by base image)
#               Default: /opt/airflow
#               Contains: dags/, logs/, config/, plugins/

# AIRFLOW__CORE__EXECUTOR: Executor type for running tasks
#                          LocalExecutor: Runs tasks in separate processes on same machine
#                          Good for single-machine deployments
#                          Alternatives: CeleryExecutor (distributed), KubernetesExecutor
ENV AIRFLOW__CORE__EXECUTOR=LocalExecutor

# AIRFLOW__CORE__PARALLELISM: Maximum number of tasks that can run simultaneously
#                              Set to 10 for moderate workloads
#                              Adjust based on available CPU cores
ENV AIRFLOW__CORE__PARALLELISM=10

# AIRFLOW__CORE__DAG_CONCURRENCY: Maximum number of tasks from same DAG that can run simultaneously
#                                  Set to 5 to limit resource usage per DAG
ENV AIRFLOW__CORE__DAG_CONCURRENCY=5

# AIRFLOW__CORE__MAX_ACTIVE_RUNS_PER_DAG: Maximum number of active DAG runs per DAG
#                                          Set to 3 to prevent too many concurrent runs
ENV AIRFLOW__CORE__MAX_ACTIVE_RUNS_PER_DAG=3

# AIRFLOW__CORE__LOAD_EXAMPLES: Load example DAGs on startup
#                                Set to false - we only want our custom DAGs
ENV AIRFLOW__CORE__LOAD_EXAMPLES=false

# AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: Pause new DAGs on creation
#                                             Set to false - start DAGs immediately
ENV AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION=false

# AIRFLOW__CORE__DAGBAG_IMPORT_TIMEOUT: Timeout (seconds) for importing DAG files
#                                       Set to 300 (5 minutes) for complex DAGs
ENV AIRFLOW__CORE__DAGBAG_IMPORT_TIMEOUT=300

# AIRFLOW__WEBSERVER__EXPOSE_CONFIG: Expose Airflow configuration in web UI
#                                    Set to true for debugging (set to false in production)
ENV AIRFLOW__WEBSERVER__EXPOSE_CONFIG=true

# AIRFLOW__WEBSERVER__SECRET_KEY: Secret key for Flask sessions
#                                  Set a random string for security
#                                  In production, use a strong random key
ENV AIRFLOW__WEBSERVER__SECRET_KEY=weather-house-airflow-secret-key-change-in-production

# AIRFLOW__API__AUTH_BACKEND: Authentication backend for Airflow API
#                             airflow.api.auth.backend.basic_auth: Basic authentication
#                             For production, use more secure options (OAuth, LDAP, etc.)
ENV AIRFLOW__API__AUTH_BACKEND=airflow.api.auth.backend.basic_auth

# AIRFLOW__CORE__FERNET_KEY: Fernet key for encrypting sensitive data
#                            Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"
#                            This is a placeholder - generate a real key for production
ENV AIRFLOW__CORE__FERNET_KEY=dummy-fernet-key-change-in-production

# AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: Database connection string for Airflow metadata
#                                      Uses PostgreSQL (provided by base image or external)
#                                      Format: postgresql+psycopg2://user:password@host:port/database
#                                      Overridden in docker-compose.yml to use external PostgreSQL
ENV AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow

# AIRFLOW__CELERY__BROKER_URL: Celery broker URL (for CeleryExecutor)
#                               Not used with LocalExecutor, but set for compatibility
ENV AIRFLOW__CELERY__BROKER_URL=redis://redis:6379/0

# AIRFLOW__CELERY__RESULT_BACKEND: Celery result backend (for CeleryExecutor)
#                                   Not used with LocalExecutor, but set for compatibility
ENV AIRFLOW__CELERY__RESULT_BACKEND=db+postgresql://airflow:airflow@postgres:5432/airflow

# AIRFLOW__LOGGING__LOGGING_LEVEL: Logging level for Airflow
#                                   INFO: Log informational messages and above
#                                   Alternatives: DEBUG (verbose), WARNING, ERROR
ENV AIRFLOW__LOGGING__LOGGING_LEVEL=INFO

# AIRFLOW__LOGGING__LOGGING_CONFIG_CLASS: Logging configuration class
#                                          Uses default Airflow logging configuration
ENV AIRFLOW__LOGGING__LOGGING_CONFIG_CLASS=airflow.config_templates.airflow_local_settings.LOGGING_CONFIG

# AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL: How often (seconds) to check for new DAGs
#                                             Set to 30 seconds for responsive DAG updates
ENV AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL=30

# -----------------------------------------------------------------------------
# Expose Ports
# -----------------------------------------------------------------------------
# 8080: Airflow Web UI port
#       Access Airflow UI at http://localhost:8080
#       Default credentials: airflow / airflow (change in production)
EXPOSE 8080

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------
# Check if Airflow webserver is responding
# - interval: Check every 30 seconds
# - timeout: Wait 10 seconds for response
# - retries: Mark unhealthy after 3 consecutive failures
# - start-period: Grace period during startup (120 seconds - Airflow takes time to initialize)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=120s \
    CMD curl -f http://localhost:8080/health || exit 1

# -----------------------------------------------------------------------------
# Default Command
# -----------------------------------------------------------------------------
# The base image has an entrypoint that:
# 1. Initializes Airflow database (if needed)
# 2. Creates admin user (if needed)
# 3. Starts Airflow components based on command
#
# In docker-compose.yml, we'll run:
#   - Airflow webserver: airflow webserver
#   - Airflow scheduler: airflow scheduler
#
# No CMD specified here - docker-compose.yml controls behavior

