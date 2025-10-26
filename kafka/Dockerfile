FROM confluentinc/cp-kafka:7.5.0

# Install utilities
USER root
RUN yum install -y netcat && yum clean all

# Create topics directory
RUN mkdir -p /etc/kafka/topics

# Copy topic creation script
COPY create-topics.sh /usr/local/bin/create-topics.sh
RUN chmod +x /usr/local/bin/create-topics.sh

# Switch back to appuser
USER appuser

# Default command
CMD ["kafka-server-start", "/etc/kafka/server.properties"]
