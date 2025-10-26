#!/usr/bin/env python3
"""
Demo 3: Consumer Group Load Balancing
Run multiple instances of this script to see partition distribution
"""

from kafka import KafkaConsumer
import json
import socket

# Kafka configuration
BOOTSTRAP_SERVERS = ['localhost:9092']
TOPIC = 'weather-readings'
GROUP_ID = 'weather-consumer-group'

# Get hostname to identify this consumer instance
CONSUMER_ID = socket.gethostname() + "-" + str(hash(str(id(object()))))[:6]

# Initialize consumer
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id=GROUP_ID,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    key_deserializer=lambda k: k.decode('utf-8') if k else None
)

def main():
    print("=" * 60)
    print(f"🔄 Consumer Group Demo - Instance: {CONSUMER_ID}")
    print(f"Topic: {TOPIC} | Group: {GROUP_ID}")
    print("=" * 60)
    print("TIP: Open 2-3 terminals and run this script to see")
    print("     how Kafka distributes partitions across consumers!")
    print("-" * 60)
    
    try:
        for message in consumer:
            data = message.value
            
            print(f"[{CONSUMER_ID}] Partition {message.partition} | "
                  f"{message.key}: {data['temperature']}°C | "
                  f"Offset: {message.offset}")
                  
    except KeyboardInterrupt:
        print(f"\nConsumer {CONSUMER_ID} stopped.")
    finally:
        consumer.close()

if __name__ == '__main__':
    main()
