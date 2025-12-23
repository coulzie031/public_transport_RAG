import json
import os
from confluent_kafka import Consumer, KafkaError
from elasticsearch import Elasticsearch

# Configuration
KAFKA_CONF = {
    'bootstrap.servers': os.environ.get('KAFKA_SERVER', 'kafka:9092'),
    'group.id': 'stations-sink-group',
    'auto.offset.reset': 'earliest' # Start from the beginning if the index is empty
}

ELASTIC_URL = os.environ.get('ELASTIC_SERVER', 'http://elasticsearch:9200')

def run_sink():
    # Initialize Kafka Consumer and Elastic Client
    consumer = Consumer(KAFKA_CONF)
    consumer.subscribe(['paris-metro-stations'])
    
    es = Elasticsearch(
        ELASTIC_URL,
        headers={"Accept": "application/json", "Content-Type": "application/json"}
        )
    
    print(f"📥 Sink started. Listening to 'paris-metro-stations' and pushing to {ELASTIC_URL}...")

    try:
        while True:
            msg = consumer.poll(1.0) # Wait for a message for 1 second

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    print(f"❌ Kafka Error: {msg.error()}")
                    break

            # 1. Decode correctly for the LLM (UTF-8)
            # This ensures "d'orly" stays "d'orly"
            try:
                raw_data = msg.value().decode('utf-8')
                data = json.loads(raw_data)
                
                # 2. Push to Elasticsearch
                # Using the Station ID as the document ID to prevent duplicates
                res = es.index(index="stations", id=data['id'], document=data)
                
                print(f"✅ Indexed: {data.get('name')} (Status: {res['result']})", flush=True)
                
            except Exception as e:
                print(f"⚠️ Failed to process message: {e}")

    except KeyboardInterrupt:
        print("Stopping sink...")
    finally:
        consumer.close()

if __name__ == "__main__":
    run_sink()
