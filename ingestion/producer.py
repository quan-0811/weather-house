"""
Weather Data Producer

Reads ISD format CSV files, transforms to WeatherEvent schema,
and publishes to Kafka topic for streaming processing.
"""
import os
import csv
import json
import time
import logging
from typing import List
from kafka import KafkaProducer
from kafka.errors import KafkaError
from pydantic import ValidationError
from schemas.weather_schema import WeatherEvent
from ingestion.transformers import transform_isd_to_weather_event

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WeatherProducer:
    """
    Producer that reads CSV files and publishes weather events to Kafka.
    """
    
    def __init__(self):
        """Initialize producer with configuration from environment variables."""
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092').split(',')
        
        self.topic = os.getenv('KAFKA_TOPIC_EVENTS', 'weather-events')
        self.interval = float(os.getenv('PRODUCER_INTERVAL_SECONDS', '1'))
        self.producer_id = os.getenv('PRODUCER_ID', 'producer-1')
        self.data_dir = '/app/data'
        
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
            compression_type='snappy',
            batch_size=16384,
            linger_ms=10,
        )
        
        logger.info(
            f"[{self.producer_id}] Initialized producer. "
            f"Kafka: {self.bootstrap_servers}, Topic: {self.topic}, "
            f"Interval: {self.interval}s"
        )
    
    def find_csv_files(self) -> List[str]:
        """
        Find all CSV files in data directory.
        Returns:
            List of CSV filenames sorted alphabetically        
        """
        try:
            csv_files = [
                f for f in os.listdir(self.data_dir) 
                if f.endswith('.csv')
            ]
            return sorted(csv_files)
        except OSError as e:
            logger.error(f"[{self.producer_id}] Error listing directory: {e}")
            return []
    
    def on_send_success(self, record_metadata):
        """Callback for successful Kafka sends."""
        logger.debug(
            f"[{self.producer_id}] Message sent to "
            f"{record_metadata.topic}[{record_metadata.partition}] "
            f"offset {record_metadata.offset}"
        )
    
    def on_send_error(self, exception):
        """Callback for failed Kafka sends."""
        logger.error(
            f"[{self.producer_id}] Failed to send message: {exception}"
        )
    
    def read_and_publish_csv(self, csv_file: str) -> int:
        """
        Read CSV file line-by-line and publish to Kafka.
        Args:
            csv_file: Name of CSV file to process
        Returns:
            Number of events successfully published
        """
        filepath = os.path.join(self.data_dir, csv_file)
        logger.info(f"[{self.producer_id}] Processing {csv_file}")
        
        if not os.path.exists(filepath):
            logger.error(f"[{self.producer_id}] File not found: {filepath}")
            return 0
        
        row_count = 0
        error_count = 0
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        event_dict = transform_isd_to_weather_event(row)
                        
                        weather_event = WeatherEvent(**event_dict)
                        
                        key = weather_event.station_id
                        value = weather_event.model_dump_json()
                        
                        future = self.producer.send(
                            self.topic,
                            key=key,
                            value=value
                        )
                        
                        future.add_callback(self.on_send_success)
                        future.add_errback(self.on_send_error)
                        
                        row_count += 1
                        
                        if self.interval > 0:
                            time.sleep(self.interval)
                        
                        if row_count % 100 == 0:
                            logger.info(
                                f"[{self.producer_id}] Processed {row_count} rows "
                                f"from {csv_file}"
                            )
                    
                    except ValidationError as e:
                        error_count += 1
                        logger.warning(
                            f"[{self.producer_id}] Validation error at row {row_num}: {e}"
                        )
                        continue
                    except Exception as e:
                        error_count += 1
                        logger.error(
                            f"[{self.producer_id}] Error processing row {row_num}: {e}",
                            exc_info=True
                        )
                        continue
            
            self.producer.flush()
            logger.info(
                f"[{self.producer_id}] Published {row_count} events from {csv_file} "
                f"({error_count} errors)"
            )
            
            return row_count
        
        except Exception as e:
            logger.error(
                f"[{self.producer_id}] Error reading file {csv_file}: {e}",
                exc_info=True
            )
            return 0
    
    def run(self):
        """
        Main loop: Find CSV files and process them continuously.
        
        """
        logger.info(f"[{self.producer_id}] Starting producer")
        
        while True:
            try:
                csv_files = self.find_csv_files()
                
                if not csv_files:
                    logger.warning(
                        f"[{self.producer_id}] No CSV files found in {self.data_dir}, "
                        f"waiting 60s..."
                    )
                    time.sleep(60)
                    continue
                
                total_events = 0
                for csv_file in csv_files:
                    events = self.read_and_publish_csv(csv_file)
                    total_events += events
                
                logger.info(
                    f"[{self.producer_id}] Finished processing all files "
                    f"({total_events} total events), waiting 60s before restart"
                )
                time.sleep(60)
            
            except KeyboardInterrupt:
                logger.info(f"[{self.producer_id}] Received interrupt signal, shutting down")
                break
            except Exception as e:
                logger.error(
                    f"[{self.producer_id}] Unexpected error in main loop: {e}",
                    exc_info=True
                )
                time.sleep(60)
        
        self.producer.close()
        logger.info(f"[{self.producer_id}] Producer stopped")


if __name__ == '__main__':
    producer = WeatherProducer()
    producer.run()