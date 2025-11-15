# =============================================================================
# APACHE CASSANDRA DOCKERFILE
# =============================================================================
# Purpose: Distributed NoSQL database for real-time weather data queries
# Role: Stores weather events, aggregates, and alerts for fast read access
# Version: Apache Cassandra 4.1.3
# Architecture: Single node (can be expanded to cluster)
# =============================================================================

# Use official Cassandra image as base
# This image contains Cassandra binaries and Java runtime
FROM cassandra:4.1.3

# -----------------------------------------------------------------------------
# Switch to Root for Configuration
# -----------------------------------------------------------------------------
# Cassandra runs as cassandra user, but we need root to modify config files
USER root

# -----------------------------------------------------------------------------
# Install System Dependencies
# -----------------------------------------------------------------------------
# curl: For health checks and downloading
# netcat-openbsd: For network connectivity checks
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        netcat-openbsd && \
    rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Copy Initialization Script
# -----------------------------------------------------------------------------
# init.cql: CQL script to create keyspace and tables on first startup
# Creates: weather_ks keyspace with weather_events, weather_aggregates, weather_alerts tables
COPY init.cql /docker-entrypoint-initdb.d/init.cql

# Make script readable by cassandra user
RUN chmod 644 /docker-entrypoint-initdb.d/init.cql && \
    chown cassandra:cassandra /docker-entrypoint-initdb.d/init.cql

# -----------------------------------------------------------------------------
# Environment Variables for Cassandra Configuration
# -----------------------------------------------------------------------------
# CASSANDRA_CLUSTER_NAME: Name of the Cassandra cluster
#                         All nodes in a cluster must have the same name
#                         Set to 'weather-cluster' for this project
ENV CASSANDRA_CLUSTER_NAME=weather-cluster

# CASSANDRA_DC: Data center name (for multi-datacenter deployments)
#               Set to 'datacenter1' for single datacenter
ENV CASSANDRA_DC=datacenter1

# CASSANDRA_RACK: Rack name within the data center
#                 Set to 'rack1' for single rack
ENV CASSANDRA_RACK=rack1

# CASSANDRA_ENDPOINT_SNITCH: Snitch implementation for topology awareness
#                            GossipingPropertyFileSnitch: Uses network topology
#                            Helps Cassandra understand node locations
ENV CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch

# CASSANDRA_SEEDS: Comma-separated list of seed nodes
#                  Seed nodes are contacted by new nodes to discover the cluster
#                  For single node, set to itself
#                  For multi-node, list all seed nodes
ENV CASSANDRA_SEEDS=cassandra

# CASSANDRA_LISTEN_ADDRESS: IP address to listen on for inter-node communication
#                           Set to 0.0.0.0 to listen on all interfaces
#                           Overridden in docker-compose.yml with container hostname
ENV CASSANDRA_LISTEN_ADDRESS=0.0.0.0

# CASSANDRA_BROADCAST_ADDRESS: IP address to broadcast to other nodes
#                              Other nodes use this to connect
#                              Overridden in docker-compose.yml with container hostname
ENV CASSANDRA_BROADCAST_ADDRESS=cassandra

# CASSANDRA_RPC_ADDRESS: IP address for client connections (CQL, Thrift)
#                        Set to 0.0.0.0 to accept connections from any interface
ENV CASSANDRA_RPC_ADDRESS=0.0.0.0

# CASSANDRA_BROADCAST_RPC_ADDRESS: IP address to broadcast to clients
#                                  Clients use this to connect
#                                  Overridden in docker-compose.yml with container hostname
ENV CASSANDRA_BROADCAST_RPC_ADDRESS=cassandra

# CASSANDRA_NUM_TOKENS: Number of virtual nodes (vnodes) per physical node
#                       More tokens = better load distribution
#                       Default: 256 (good for most use cases)
ENV CASSANDRA_NUM_TOKENS=256

# CASSANDRA_INITIAL_TOKEN: Initial token for this node (for manual token assignment)
#                          Not needed when using vnodes (num_tokens > 1)
ENV CASSANDRA_INITIAL_TOKEN=

# CASSANDRA_AUTO_BOOTSTRAP: Automatically bootstrap (join cluster) on startup
#                           Set to true for new nodes joining existing cluster
ENV CASSANDRA_AUTO_BOOTSTRAP=true

# CASSANDRA_AUTHENTICATOR: Authentication mechanism
#                         AllowAllAuthenticator: No authentication (for development)
#                         PasswordAuthenticator: Username/password authentication (for production)
ENV CASSANDRA_AUTHENTICATOR=AllowAllAuthenticator

# CASSANDRA_AUTHORIZER: Authorization mechanism
#                      AllowAllAuthorizer: No authorization (for development)
#                      CassandraAuthorizer: Role-based access control (for production)
ENV CASSANDRA_AUTHORIZER=AllowAllAuthorizer

# CASSANDRA_HEAP_NEWSIZE: Size of young generation heap (for garbage collection)
#                         Set to 800M (good for 2GB total heap)
ENV CASSANDRA_HEAP_NEWSIZE=800M

# CASSANDRA_MAX_HEAP_SIZE: Maximum Java heap size
#                          Set to 2G for moderate workloads
#                          Should be ~50% of available RAM (leave room for OS and off-heap)
ENV CASSANDRA_MAX_HEAP_SIZE=2G

# CASSANDRA_COMMITLOG_DIR: Directory for commit log (write-ahead log)
#                          /var/lib/cassandra/commitlog (default)
ENV CASSANDRA_COMMITLOG_DIR=/var/lib/cassandra/commitlog

# CASSANDRA_SAVED_CACHES_DIR: Directory for saved caches
#                             /var/lib/cassandra/saved_caches (default)
ENV CASSANDRA_SAVED_CACHES_DIR=/var/lib/cassandra/saved_caches

# CASSANDRA_DATA_DIR: Directory for data files (SSTables)
#                     /var/lib/cassandra/data (default)
ENV CASSANDRA_DATA_DIR=/var/lib/cassandra/data

# CASSANDRA_HINTS_DIR: Directory for hints (for eventual consistency)
#                      /var/lib/cassandra/hints (default)
ENV CASSANDRA_HINTS_DIR=/var/lib/cassandra/hints

# CASSANDRA_CDC_RAW_DIR: Directory for Change Data Capture (CDC) raw files
#                        /var/lib/cassandra/cdc_raw (default)
ENV CASSANDRA_CDC_RAW_DIR=/var/lib/cassandra/cdc_raw

# CASSANDRA_START_RPC: Start RPC server (CQL, Thrift) on startup
#                      Set to true to accept client connections
ENV CASSANDRA_START_RPC=true

# CASSANDRA_ENABLE_USER_DEFINED_FUNCTIONS: Enable user-defined functions
#                                          Set to false for security (unless needed)
ENV CASSANDRA_ENABLE_USER_DEFINED_FUNCTIONS=false

# CASSANDRA_ENABLE_MATERIALIZED_VIEWS: Enable materialized views
#                                      Set to true to allow materialized view creation
ENV CASSANDRA_ENABLE_MATERIALIZED_VIEWS=true

# CASSANDRA_ENABLE_SCRIPTED_USER_DEFINED_FUNCTIONS: Enable scripted UDFs (JavaScript)
#                                                    Set to false for security
ENV CASSANDRA_ENABLE_SCRIPTED_USER_DEFINED_FUNCTIONS=false

# CASSANDRA_KEYSPACE: Default keyspace name (optional)
#                     Not used - we create keyspace via init.cql
ENV CASSANDRA_KEYSPACE=

# -----------------------------------------------------------------------------
# Security: Switch to Non-Root User
# -----------------------------------------------------------------------------
# Run Cassandra as 'cassandra' user (provided by base image)
# This is a security best practice
USER cassandra

# -----------------------------------------------------------------------------
# Expose Ports
# -----------------------------------------------------------------------------
# 7000: Inter-node communication (gossip protocol)
#       Cassandra nodes use this to discover each other and exchange cluster state
# 7001: SSL inter-node communication (if SSL enabled)
#       7001 is used when encryption is enabled
# 9042: CQL native protocol port (client connections)
#       Applications (Spark, Superset) connect here using CQL
# 9160: Thrift RPC port (legacy, deprecated)
#       Still exposed for backward compatibility
EXPOSE 7000 7001 9042 9160

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------
# Check if Cassandra is responding to CQL queries
# Uses nodetool status to verify node is up and normal
# - interval: Check every 30 seconds
# - timeout: Wait 10 seconds for response
# - retries: Mark unhealthy after 3 consecutive failures
# - start-period: Grace period during startup (120 seconds - Cassandra takes time to start)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=120s \
    CMD nodetool status | grep -E "^UN|^DN" || exit 1

# -----------------------------------------------------------------------------
# Default Command
# -----------------------------------------------------------------------------
# The base image has an entrypoint that:
# 1. Reads environment variables
# 2. Generates cassandra.yaml configuration
# 3. Runs init scripts from /docker-entrypoint-initdb.d/ (our init.cql)
# 4. Starts Cassandra daemon
#
# Cassandra will:
# - Join the cluster (if seeds are available)
# - Create keyspace and tables from init.cql
# - Start accepting client connections on port 9042
#
# No CMD override needed - base image handles it

