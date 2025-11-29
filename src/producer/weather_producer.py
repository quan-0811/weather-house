import json
import time
import os
import random
from kafka.admin import KafkaAdminClient, NewTopic
from kafka import KafkaProducer
import pandas as pd
from utils import get_corrupted_payload
from config import KAFKA_BROKERS, TOPIC_NAME, INPUT_FILE, CORRUPTION_PROBABILITY, DUPLICATE_PROBABILITY

# --- Topic Creation ---
admin_client = KafkaAdminClient(bootstrap_servers=KAFKA_BROKERS)
topic = NewTopic(name=TOPIC_NAME, num_partitions=3, replication_factor=3)
try:
    admin_client.create_topics([topic])
except Exception:
    pass

# --- Load Data ---
data_source_path = os.path.join(os.path.dirname(__file__), INPUT_FILE)
csv_data = pd.read_csv(data_source_path)
csv_data = csv_data.to_dict('records')
producer = KafkaProducer(bootstrap_servers=KAFKA_BROKERS)

# --- Send Data ---
print(f"Starting Stream with corruption probability {CORRUPTION_PROBABILITY} and duplicate probability {DUPLICATE_PROBABILITY}...")
i = 0

for row in csv_data:
    payload_str = json.dumps(row)
    log_msg = "Valid"
    
    if random.random() < CORRUPTION_PROBABILITY:
        payload_str, log_msg = get_corrupted_payload(row)
        print(f"ID {i}: {log_msg}")
    else:
        print(f"ID {i}: {log_msg}")

    key = str(row['location_id']).encode('utf-8')
    value = payload_str.encode('utf-8')

    producer.send(TOPIC_NAME, key=key, value=value)

    if random.random() < DUPLICATE_PROBABILITY:
        print(f"ID {i}: Sending DUPLICATE")
        producer.send(TOPIC_NAME, key=key, value=value)

    producer.flush()
    i += 1
    time.sleep(2)

producer.close()