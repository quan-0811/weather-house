#!/usr/bin/env python3
"""
Demo 2 Consumer: Processes weather data from Kafka
"""

from kafka import KafkaConsumer
import json

# Kafka configuration
BOOTSTRAP_SERVERS = ['localhost:9092']
TOPIC = 'weather-readings'
GROUP_ID = 'weather-processing-group'

# Initialize consumer
consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP_SERVERS,
    auto_offset_reset='earliest',  # Start from beginning if no offset
    enable_auto_commit=True,
    group_id=GROUP_ID,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    key_deserializer=lambda k: k.decode('utf-8') if k else None
)

def main():
    print("Weather Consumer started...")
    print(f"Subscribed to topic: {TOPIC}")
    print(f"Consumer group: {GROUP_ID}")
    print("-" * 50)
    
    try:
        for message in consumer:
            data = message.value
            location = message.key
            
            alert = "HIGH TEMP!" if data['temperature'] > 32 else ""
            
            print(f"[Partition {message.partition}] {location} | "
                  f"Temp: {data['temperature']}°C | "
                  f"Humidity: {data['humidity']}% | "
                  f"Offset: {message.offset} {alert}")
                  
    except KeyboardInterrupt:
        print("\n\n✅ Consumer stopped.")
    finally:
        consumer.close()

if __name__ == '__main__':
    main()
