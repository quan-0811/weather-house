# =============================================================================
# APACHE ZOOKEEPER DOCKERFILE
# =============================================================================
# Purpose: Coordination service for Kafka cluster (required, not using KRaft)
# Role: Manages Kafka broker metadata, leader election, configuration
# Version: Apache Zookeeper 3.9.1
# =============================================================================

# Use official Zookeeper image as base
# This image contains Zookeeper binaries and Java runtime
FROM zookeeper:3.9.1

# -----------------------------------------------------------------------------
# Environment Variables for Zookeeper Configuration
# -----------------------------------------------------------------------------
# ZOO_MY_ID: Unique identifier for this Zookeeper instance (1-255)
#            Used in a Zookeeper ensemble (cluster) to identify each node
#            For single node, set to 1
ENV ZOO_MY_ID=1

# ZOO_SERVERS: List of all Zookeeper servers in the ensemble
#              Format: server.id=hostname:peer_port:election_port:server_type
#              - peer_port: Port for peer communication (default 2888)
#              - election_port: Port for leader election (default 3888)
#              - server_type: 'participant' (voting member) or 'observer' (non-voting)
#              For single node, this can be empty or set to itself
ENV ZOO_SERVERS="server.1=zookeeper:2888:3888;2181"

# ZOO_TICK_TIME: Basic time unit in milliseconds used by Zookeeper
#                All other timeouts are multiples of this value
#                Default: 2000ms (2 seconds)
#                Used for: session timeout, connection timeout, etc.
ENV ZOO_TICK_TIME=2000

# ZOO_INIT_LIMIT: Maximum time (in ticks) for followers to connect to leader
#                 Default: 10 ticks = 20 seconds (10 * 2000ms)
#                 If followers can't connect within this time, they restart
ENV ZOO_INIT_LIMIT=10

# ZOO_SYNC_LIMIT: Maximum time (in ticks) for followers to sync with leader
#                 Default: 5 ticks = 10 seconds (5 * 2000ms)
#                 If sync takes longer, follower is considered dead
ENV ZOO_SYNC_LIMIT=5

# ZOO_MAX_CLIENT_CNXNS: Maximum number of client connections per IP
#                      Default: 60
#                      Prevents a single client from overwhelming the server
ENV ZOO_MAX_CLIENT_CNXNS=60

# ZOO_AUTOPURGE_PURGEINTERVAL: Interval (in hours) to purge old snapshots and logs
#                              Default: 0 (disabled)
#                              Set to 1 to enable daily cleanup
ENV ZOO_AUTOPURGE_PURGEINTERVAL=1

# ZOO_AUTOPURGE_SNAPRETAINCOUNT: Number of snapshots to retain after purge
#                                Default: 3
#                                Keeps last 3 snapshots for recovery
ENV ZOO_AUTOPURGE_SNAPRETAINCOUNT=3

# ZOO_4LW_COMMANDS_WHITELIST: Commands allowed via 4-letter-word commands
#                             Default: srvr, mntr, ruok
#                             These are monitoring commands (stat, mntr, ruok, etc.)
#                             'ruok' = "Are you OK?" - health check command
ENV ZOO_4LW_COMMANDS_WHITELIST="srvr,mntr,ruok"

# ZOO_STANDALONE_ENABLED: Enable standalone mode (single node, no ensemble)
#                         Default: true
#                         Set to false if running in ensemble mode
ENV ZOO_STANDALONE_ENABLED=true

# -----------------------------------------------------------------------------
# Expose Ports
# -----------------------------------------------------------------------------
# 2181: Client port - Kafka brokers and clients connect here
#        This is the main port for Zookeeper client connections
# 2888: Peer communication port - Used by Zookeeper servers to communicate
#        Only needed in ensemble mode (multiple Zookeeper nodes)
# 3888: Leader election port - Used for leader election in ensemble mode
#        Only needed in ensemble mode
# 8080: Admin server port - Web UI for Zookeeper (if enabled)
EXPOSE 2181 2888 3888 8080

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------
# Uses 'ruok' (Are you OK?) command to check if Zookeeper is responsive
# - interval: Check every 30 seconds
# - timeout: Wait 10 seconds for response
# - retries: Mark unhealthy after 3 consecutive failures
# - start-period: Grace period during startup (30 seconds)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=30s \
    CMD echo ruok | nc localhost 2181 | grep imok || exit 1

# -----------------------------------------------------------------------------
# Default Command
# -----------------------------------------------------------------------------
# The base image already has an entrypoint that starts Zookeeper
# It reads the environment variables above and generates zoo.cfg
# No need to override CMD - base image handles it
# Zookeeper will start in the foreground and listen on port 2181

