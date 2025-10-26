#!/usr/bin/env python3
"""
Demo 2 Producer: Simulates IoT weather sensors sending data to Kafka
"""

from kafka import KafkaProducer
import json
import time
import random
from datetime import datetime

# Kafka configuration
BOOTSTRAP_SERVERS = ['localhost:9092']
TOPIC = 'weather-readings'

# Initialize producer
producer = KafkaProducer(
    bootstrap_servers=BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    key_serializer=lambda k: k.encode('utf-8') if k else None
)

# Simulated weather stations
LOCATIONS = ['Hanoi', 'HoChiMinh', 'DaNang', 'HaiPhong', 'CanTho']

def generate_weather_data(location):
    """Generate random weather data"""
    return {
        'location': location,
        'timestamp': datetime.now().isoformat(),
        'temperature': round(random.uniform(20.0, 35.0), 2),
        'humidity': round(random.uniform(40.0, 90.0), 2),
        'pressure': round(random.uniform(1000.0, 1020.0), 2),
        'wind_speed': round(random.uniform(0.0, 20.0), 2)
    }

def main():
    print("🌤️  Weather IoT Producer started...")
    print(f"Publishing to topic: {TOPIC}")
    print(f"Locations: {', '.join(LOCATIONS)}")
    print("-" * 50)
    
    try:
        count = 0
        while True:
            # Pick random location
            location = random.choice(LOCATIONS)
            
            # Generate weather reading
            weather_data = generate_weather_data(location)
            
            # Send to Kafka (using location as key for partitioning)
            future = producer.send(
                topic=TOPIC,
                key=location,
                value=weather_data
            )
            
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            
            count += 1
            print(f"[{count}] Sent: {location} | Temp: {weather_data['temperature']}°C | "
                  f"Partition: {record_metadata.partition} | Offset: {record_metadata.offset}")
            
            # Sleep 2 seconds before next reading
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n\n✅ Producer stopped. Total messages sent:", count)
    finally:
        producer.close()

if __name__ == '__main__':
    main()
