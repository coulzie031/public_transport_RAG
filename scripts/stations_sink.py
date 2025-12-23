import json
import os
import sys
import time
from confluent_kafka import Consumer, KafkaError
from elasticsearch import Elasticsearch

# --- CONFIG ---
INDEX_NAME = "stations"
KAFKA_CONF = {
    'bootstrap.servers': os.environ.get('KAFKA_SERVER', 'kafka:29092'),
    'group.id': 'stations-sink-text-v1',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True
}

def create_index_if_not_exists(es):
    if not es.indices.exists(index=INDEX_NAME):
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    # Standard text field with fuzzy capabilities
                    "name": {"type": "text", "analyzer": "standard"}, 
                    "city": {"type": "keyword"},
                    "lines": {"type": "keyword"},
                    "coordinates": {"type": "geo_point"}
                }
            }
        }
        es.indices.create(index=INDEX_NAME, body=mapping)
        print(f"✅ Index '{INDEX_NAME}' created (Standard Text).")

def run_sink():
    es = Elasticsearch(os.environ.get('ELASTIC_SERVER'), meta_header=False)
    
    while True:
        try:
            if es.ping(): break
        except: pass
        time.sleep(5)

    create_index_if_not_exists(es)

    consumer = Consumer(KAFKA_CONF)
    consumer.subscribe(['stations'])

    print(f"🚀 Stations Sink Started (Text Mode)...")

    while True:
        msg = consumer.poll(1.0)
        if msg is None: continue
        
        if msg.error():
            print(f"❌ Kafka Error: {msg.error()}")
            continue

        try:
            val = msg.value()
            if not val: continue
            data = json.loads(val.decode('utf-8'))

            # Just index the raw data. No API calls needed!
            es.index(index=INDEX_NAME, id=data['id'], document=data)
            print(f"✅ Indexed: {data.get('name')}")

        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    run_sink()
