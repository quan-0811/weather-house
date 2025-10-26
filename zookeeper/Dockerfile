FROM confluentinc/cp-zookeeper:7.5.0

# Install utilities
USER root
RUN yum install -y netcat && yum clean all

# Create necessary directories
RUN mkdir -p /var/lib/zookeeper/data && \
    mkdir -p /var/lib/zookeeper/log && \
    chown -R appuser:appuser /var/lib/zookeeper

# Switch back to appuser
USER appuser

# Expose Zookeeper port
EXPOSE 2181

# Default command
CMD ["zookeeper-server-start", "/etc/kafka/zookeeper.properties"]
