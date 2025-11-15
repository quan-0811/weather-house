# =============================================================================
# APACHE HDFS DOCKERFILE
# =============================================================================
# Purpose: Distributed file system for storing large-scale weather data
# Role: Stores bronze (raw), silver (cleaned), and gold (aggregated) data layers
# Version: Apache Hadoop 3.3.6
# Architecture: 1 NameNode, 1 Secondary NameNode, 3 DataNodes
# =============================================================================

# Use official Hadoop image as base
# This image contains Hadoop binaries, HDFS, and Java runtime
FROM apache/hadoop:3.3.6

# -----------------------------------------------------------------------------
# Switch to Root for Configuration
# -----------------------------------------------------------------------------
# Hadoop runs as hadoop user, but we need root to modify config files
USER root

# -----------------------------------------------------------------------------
# Install System Dependencies
# -----------------------------------------------------------------------------
# ssh: Required for Hadoop daemons to communicate (SSH-based startup)
# rsync: For data synchronization between nodes
# netcat-openbsd: For health checks and network debugging
# curl: For downloading and health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
        openssh-server \
        openssh-client \
        rsync \
        netcat-openbsd \
        curl && \
    rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Configure SSH for Passwordless Access
# -----------------------------------------------------------------------------
# Hadoop uses SSH to start/stop daemons on different nodes
# Generate SSH keys for passwordless authentication
# -t rsa: Generate RSA key pair
# -N "": No passphrase (for automation)
# -f: Output file location
RUN ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa && \
    cat /root/.ssh/id_rsa.pub >> /root/.ssh/authorized_keys && \
    chmod 600 /root/.ssh/authorized_keys && \
    chmod 700 /root/.ssh

# Configure SSH to not prompt for host key verification
# StrictHostKeyChecking=no: Automatically accept new host keys
# UserKnownHostsFile=/dev/null: Don't save known hosts (Docker containers)
RUN echo "Host *" >> /root/.ssh/config && \
    echo "  StrictHostKeyChecking no" >> /root/.ssh/config && \
    echo "  UserKnownHostsFile /dev/null" >> /root/.ssh/config

# -----------------------------------------------------------------------------
# Create HDFS Data Directories
# -----------------------------------------------------------------------------
# /hadoop/dfs/name: NameNode metadata storage (edits, fsimage)
#                   Contains file system namespace and block locations
# /hadoop/dfs/data: DataNode block storage (actual file data)
#                   Stores the actual data blocks of files
# /hadoop/dfs/secondary: Secondary NameNode checkpoint storage
#                        Stores periodic snapshots of NameNode metadata
RUN mkdir -p /hadoop/dfs/name \
             /hadoop/dfs/data \
             /hadoop/dfs/secondary \
             /hadoop/logs && \
    chmod -R 755 /hadoop

# -----------------------------------------------------------------------------
# Copy HDFS Configuration Files
# -----------------------------------------------------------------------------
# core-site.xml: Core Hadoop configuration (default filesystem, ports)
# hdfs-site.xml: HDFS-specific configuration (replication, directories)
# These files define how HDFS operates (ports, directories, replication factor)
COPY conf/core-site.xml $HADOOP_HOME/etc/hadoop/core-site.xml
COPY conf/hdfs-site.xml $HADOOP_HOME/etc/hadoop/hdfs-site.xml

# -----------------------------------------------------------------------------
# Environment Variables for HDFS Configuration
# -----------------------------------------------------------------------------
# HADOOP_HOME: Hadoop installation directory (set by base image)
#              Points to /opt/hadoop-3.3.6

# HDFS_NAMENODE_USER: User to run NameNode daemon
#                     Set to root for simplicity (can be changed to hadoop user)
ENV HDFS_NAMENODE_USER=root

# HDFS_DATANODE_USER: User to run DataNode daemon
#                     Set to root for simplicity
ENV HDFS_DATANODE_USER=root

# HDFS_SECONDARYNAMENODE_USER: User to run Secondary NameNode daemon
#                               Set to root for simplicity
ENV HDFS_SECONDARYNAMENODE_USER=root

# HDFS_NAMENODE_DIR: Directory for NameNode metadata storage
#                    Must match dfs.namenode.name.dir in hdfs-site.xml
ENV HDFS_NAMENODE_DIR=/hadoop/dfs/name

# HDFS_DATANODE_DIR: Directory for DataNode block storage
#                    Must match dfs.datanode.data.dir in hdfs-site.xml
ENV HDFS_DATANODE_DIR=/hadoop/dfs/data

# HDFS_SECONDARYNAMENODE_DIR: Directory for Secondary NameNode checkpoints
#                              Must match dfs.namenode.checkpoint.dir in hdfs-site.xml
ENV HDFS_SECONDARYNAMENODE_DIR=/hadoop/dfs/secondary

# HADOOP_CONF_DIR: Directory containing Hadoop configuration files
#                  Points to $HADOOP_HOME/etc/hadoop
ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop

# HADOOP_LOG_DIR: Directory for Hadoop daemon logs
#                 Logs from NameNode, DataNode, Secondary NameNode
ENV HADOOP_LOG_DIR=/hadoop/logs

# HDFS_NAMENODE_HOST: Hostname of NameNode (overridden in docker-compose)
#                     DataNodes and Secondary NameNode connect here
ENV HDFS_NAMENODE_HOST=namenode

# HDFS_NAMENODE_PORT: RPC port for NameNode (default: 9000)
#                     Clients and DataNodes connect here
ENV HDFS_NAMENODE_PORT=9000

# HDFS_NAMENODE_HTTP_PORT: HTTP port for NameNode Web UI (default: 9870)
#                          Web interface to browse file system
ENV HDFS_NAMENODE_HTTP_PORT=9870

# HDFS_DATANODE_PORT: RPC port for DataNode (default: 9866)
#                     NameNode connects here to send commands
ENV HDFS_DATANODE_PORT=9866

# HDFS_DATANODE_HTTP_PORT: HTTP port for DataNode Web UI (default: 9864)
#                          Web interface to view DataNode status
ENV HDFS_DATANODE_HTTP_PORT=9864

# HDFS_SECONDARYNAMENODE_HTTP_PORT: HTTP port for Secondary NameNode Web UI (default: 9868)
#                                   Web interface to view checkpoint status
ENV HDFS_SECONDARYNAMENODE_HTTP_PORT=9868

# HDFS_REPLICATION: Default replication factor for files
#                   Set to 3 (each block stored on 3 DataNodes)
#                   Provides fault tolerance (can lose 2 DataNodes)
ENV HDFS_REPLICATION=3

# -----------------------------------------------------------------------------
# Format NameNode (Only on First Startup)
# -----------------------------------------------------------------------------
# This command formats the NameNode filesystem
# WARNING: This deletes all data! Only run on first startup
# The command is commented out - uncomment only for initial setup
# Format creates the initial metadata structure
# RUN hdfs namenode -format -force -nonInteractive

# -----------------------------------------------------------------------------
# Create Startup Scripts
# -----------------------------------------------------------------------------
# Script to start NameNode
# -format: Format the filesystem (only on first run)
# -force: Force format even if metadata exists
# -nonInteractive: Don't prompt for confirmation
RUN echo '#!/bin/bash\n\
set -e\n\
# Start SSH daemon (required for Hadoop)\n\
service ssh start\n\
# Format NameNode if directory is empty (first startup only)\n\
if [ ! -d "$HDFS_NAMENODE_DIR/current" ]; then\n\
  echo "Formatting NameNode..."\n\
  hdfs namenode -format -force -nonInteractive\n\
fi\n\
# Start NameNode daemon\n\
echo "Starting NameNode..."\n\
hdfs --daemon start namenode\n\
# Keep container running\n\
tail -f $HADOOP_LOG_DIR/hadoop-root-namenode-*.log\n\
' > /start-namenode.sh && chmod +x /start-namenode.sh

# Script to start Secondary NameNode
RUN echo '#!/bin/bash\n\
set -e\n\
# Start SSH daemon\n\
service ssh start\n\
# Start Secondary NameNode daemon\n\
echo "Starting Secondary NameNode..."\n\
hdfs --daemon start secondarynamenode\n\
# Keep container running\n\
tail -f $HADOOP_LOG_DIR/hadoop-root-secondarynamenode-*.log\n\
' > /start-secondarynamenode.sh && chmod +x /start-secondarynamenode.sh

# Script to start DataNode
RUN echo '#!/bin/bash\n\
set -e\n\
# Start SSH daemon\n\
service ssh start\n\
# Wait for NameNode to be ready\n\
echo "Waiting for NameNode at ${HDFS_NAMENODE_HOST}:${HDFS_NAMENODE_PORT}..."\n\
while ! nc -z ${HDFS_NAMENODE_HOST} ${HDFS_NAMENODE_PORT}; do\n\
  sleep 2\n\
done\n\
echo "NameNode is ready"\n\
# Start DataNode daemon\n\
echo "Starting DataNode..."\n\
hdfs --daemon start datanode\n\
# Keep container running\n\
tail -f $HADOOP_LOG_DIR/hadoop-root-datanode-*.log\n\
' > /start-datanode.sh && chmod +x /start-datanode.sh

# -----------------------------------------------------------------------------
# Expose Ports
# -----------------------------------------------------------------------------
# NameNode Ports:
# 9000 - NameNode RPC (clients and DataNodes connect here)
# 9870 - NameNode Web UI (browse file system, view cluster status)
#
# DataNode Ports:
# 9866 - DataNode RPC (NameNode sends commands here)
# 9864 - DataNode Web UI (view DataNode status, block information)
#
# Secondary NameNode Ports:
# 9868 - Secondary NameNode Web UI (view checkpoint status)
EXPOSE 9000 9870 9866 9864 9868

# -----------------------------------------------------------------------------
# Health Check (NameNode)
# -----------------------------------------------------------------------------
# Check if NameNode Web UI is responding
# - interval: Check every 30 seconds
# - timeout: Wait 10 seconds for response
# - retries: Mark unhealthy after 3 consecutive failures
# - start-period: Grace period during startup (60 seconds - HDFS takes time to start)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=60s \
    CMD curl -f http://localhost:9870/ || exit 1

# -----------------------------------------------------------------------------
# Default Command
# -----------------------------------------------------------------------------
# This Dockerfile is used by NameNode, Secondary NameNode, and DataNodes
# The actual command is specified in docker-compose.yml:
#   - NameNode: /start-namenode.sh
#   - Secondary NameNode: /start-secondarynamenode.sh
#   - DataNode: /start-datanode.sh
#
# No CMD specified here - docker-compose.yml controls behavior

