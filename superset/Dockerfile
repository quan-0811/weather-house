# =============================================================================
# APACHE SUPERSET DOCKERFILE
# =============================================================================
# Purpose: Business intelligence and data visualization platform
# Role: Visualizes weather data from Cassandra for analytics and dashboards
# Version: Apache Superset 3.0.0 (Python 3.11)
# Architecture: Single Superset instance with embedded database
# =============================================================================

# Use official Superset image as base
# This image contains Superset, Python, and all dependencies
# apache/superset:3.0.0 - Latest stable version
FROM apache/superset:3.0.0

# -----------------------------------------------------------------------------
# Switch to Root for Package Installation
# -----------------------------------------------------------------------------
# Superset runs as superset user, but we need root to install system packages
USER root

# -----------------------------------------------------------------------------
# Install System Dependencies
# -----------------------------------------------------------------------------
# gcc, g++: Compilers for building Python packages with C extensions
# libffi-dev: Development files for Foreign Function Interface
# libssl-dev: OpenSSL development files (for secure connections)
# python3-dev: Python development headers
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
# Switch to Superset User
# -----------------------------------------------------------------------------
# Switch back to superset user for Python package installation
USER superset

# -----------------------------------------------------------------------------
# Install Python Dependencies
# -----------------------------------------------------------------------------
# Install Cassandra driver for Superset to connect to Cassandra database
# cassandra-driver: Official Python driver for Apache Cassandra
#                  Required for Superset to query Cassandra tables
#                  Version 3.29.0 matches the version used in Spark and other components
RUN pip install --no-cache-dir \
    cassandra-driver==3.29.0

# -----------------------------------------------------------------------------
# Environment Variables for Superset Configuration
# -----------------------------------------------------------------------------
# SUPERSET_HOME: Superset home directory (set by base image)
#                Default: /app
#                Contains: superset_config.py, logs/, etc.

# SUPERSET_CONFIG_PATH: Path to Superset configuration file
#                       Default: /app/superset_config.py
#                       Can be customized for production settings
ENV SUPERSET_CONFIG_PATH=/app/superset_config.py

# SUPERSET_SECRET_KEY: Secret key for Flask sessions and encryption
#                      Generate with: openssl rand -base64 42
#                      This is a placeholder - generate a real key for production
ENV SUPERSET_SECRET_KEY=weather-house-superset-secret-key-change-in-production

# SUPERSET_DATABASE_URI: Database connection string for Superset metadata
#                        Uses PostgreSQL (provided by base image or external)
#                        Format: postgresql://user:password@host:port/database
#                        Overridden in docker-compose.yml to use external PostgreSQL
ENV SUPERSET_DATABASE_URI=postgresql://superset:superset@postgres:5432/superset

# SUPERSET_REDIS_HOST: Redis host for caching and task queue
#                      Not required for basic setup, but useful for production
#                      Overridden in docker-compose.yml if Redis is available
ENV SUPERSET_REDIS_HOST=redis

# SUPERSET_REDIS_PORT: Redis port
#                     Default: 6379
ENV SUPERSET_REDIS_PORT=6379

# SUPERSET_ENABLE_PROXY_FIX: Enable proxy fix for reverse proxy setups
#                            Set to true if Superset is behind a reverse proxy (nginx, etc.)
ENV SUPERSET_ENABLE_PROXY_FIX=true

# SUPERSET_ENABLE_CORS: Enable Cross-Origin Resource Sharing
#                       Set to true to allow API access from other domains
ENV SUPERSET_ENABLE_CORS=true

# SUPERSET_CORS_OPTIONS: CORS options (JSON format)
#                        Allow all origins for development (restrict in production)
ENV SUPERSET_CORS_OPTIONS='{"origins": ["*"], "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"], "allow_headers": ["*"]}'

# SUPERSET_ROW_LIMIT: Default row limit for queries
#                     Set to 10000 rows (adjust based on needs)
ENV SUPERSET_ROW_LIMIT=10000

# SUPERSET_SQLLAB_TIMEOUT: SQL query timeout (seconds)
#                          Set to 300 (5 minutes) for long-running queries
ENV SUPERSET_SQLLAB_TIMEOUT=300

# SUPERSET_ENABLE_TEMPLATE_PROCESSING: Enable Jinja2 template processing in SQL
#                                      Set to true to allow dynamic SQL queries
ENV SUPERSET_ENABLE_TEMPLATE_PROCESSING=true

# SUPERSET_FEATURE_FLAGS: Feature flags (JSON format)
#                         Enable/disable Superset features
#                         ALERT_REPORTS: Enable alert reports
#                         DASHBOARD_NATIVE_FILTERS: Enable native filters
ENV SUPERSET_FEATURE_FLAGS='{"ALERT_REPORTS": true, "DASHBOARD_NATIVE_FILTERS": true}'

# SUPERSET_LOAD_EXAMPLES: Load example datasets and dashboards
#                         Set to false - we only want our weather data
ENV SUPERSET_LOAD_EXAMPLES=false

# SUPERSET_WORKERS: Number of Gunicorn worker processes
#                   Set to 4 for moderate load (adjust based on CPU cores)
ENV SUPERSET_WORKERS=4

# SUPERSET_WORKER_TIMEOUT: Worker timeout (seconds)
#                          Set to 300 (5 minutes) for long-running requests
ENV SUPERSET_WORKER_TIMEOUT=300

# SUPERSET_WORKER_CLASS: Gunicorn worker class
#                        gevent: Async worker for better concurrency
ENV SUPERSET_WORKER_CLASS=gevent

# -----------------------------------------------------------------------------
# Expose Ports
# -----------------------------------------------------------------------------
# 8088: Superset Web UI port
#       Access Superset UI at http://localhost:8088
#       Default credentials: admin / admin (change on first login)
EXPOSE 8088

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------
# Check if Superset webserver is responding
# - interval: Check every 30 seconds
# - timeout: Wait 10 seconds for response
# - retries: Mark unhealthy after 3 consecutive failures
# - start-period: Grace period during startup (120 seconds - Superset takes time to initialize)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=120s \
    CMD curl -f http://localhost:8088/health || exit 1

# -----------------------------------------------------------------------------
# Default Command
# -----------------------------------------------------------------------------
# The base image has an entrypoint that:
# 1. Initializes Superset database (if needed)
# 2. Creates admin user (if needed)
# 3. Starts Superset webserver
#
# In docker-compose.yml, we'll run:
#   - Superset initialization: superset db upgrade && superset init
#   - Superset webserver: gunicorn -w 4 -k gevent --timeout 300 -b 0.0.0.0:8088 superset.app:create_app()
#
# No CMD specified here - docker-compose.yml controls behavior

