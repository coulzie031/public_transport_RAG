import json
import os
import sys
import time
from confluent_kafka import Consumer, KafkaError
from elasticsearch import Elasticsearch

# Make sure this import works! 
# If you don't have this file, put the function back inside this script.
try:
    from tools.nvidia_embedding import get_nvidia_embedding
except ImportError:
    print("❌ Error: Could not import 'nvidia_embedding'. Did you create the file?")
    sys.exit(1)

# --- CONFIG ---
VECTOR_DIMS = 1024 
INDEX_NAME = "paris-disruptions"
TOPIC = "paris-disruptions-metro"
KAFKA_CONF = {
    'bootstrap.servers': os.environ.get('KAFKA_SERVER', 'kafka:29092'),
    'group.id': 'nvidia-sink-group-v1',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
    'session.timeout.ms': 6000
}

def create_index_if_not_exists(es):
    if not es.indices.exists(index=INDEX_NAME):
        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "title": {"type": "text"},
                    "description": {"type": "text"},
                    "impact": {"type": "keyword"},
                    "mode": {"type": "keyword"},
                    "embedding_vector": {
                        "type": "dense_vector",
                        "dims": VECTOR_DIMS,
                        "index": True,
                        "similarity": "cosine"
                    }
                }
            }
        }
        es.indices.create(index=INDEX_NAME, body=mapping)
        print(f"✅ Index '{INDEX_NAME}' created with NVIDIA mapping.")

def run_sink():
    es = Elasticsearch(os.environ.get('ELASTIC_SERVER'), meta_header=False)
    
    # Retry logic for Elasticsearch connection on startup
    while True:
        try:
            if es.ping():
                break
        except:
            pass
        print("⏳ Waiting for Elasticsearch...")
        time.sleep(5)

    create_index_if_not_exists(es)
    
    print("🚀 NVIDIA-Powered Sink Started...")

    # --- OUTER LOOP: HANDLES CRASHES ---
    while True:
        try:
            consumer = Consumer(KAFKA_CONF)
            consumer.subscribe([TOPIC])

            # --- INNER LOOP: PROCESSES MESSAGES ---
            while True:
                msg = consumer.poll(1.0)
                if msg is None: continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(f"❌ Kafka Error: {msg.error()}")
                        break # Break inner loop to restart consumer

                try:
                    val = msg.value()
                    if not val: continue
                    data = json.loads(val.decode('utf-8'))
                    
                    # 1. WIPE SIGNAL
                    if data.get("control") == "CLEAR_ALERTS":
                        mode_to_wipe = data.get("mode")

                        if mode_to_wipe:
                            print(f"🧹 Clearing alerts for mode={mode_to_wipe}...")
                            es.delete_by_query(
                                index=INDEX_NAME,
                                body={"query": {"term": {"mode": mode_to_wipe}}},
                                conflicts="proceed"
                            )
                        else:
                            print("🧹 Clearing ALL alerts (no mode specified)...")
                            es.delete_by_query(
                                index=INDEX_NAME, 
                                body={"query": {"match_all": {}}},
                                conflicts="proceed"
                            )
                        continue

                    # 2. EMBEDDING (Remote API)
                    text_to_embed = f"{data.get('title', '')} {data.get('description', '')}"
                    
                    # We accept failures here so one bad API call doesn't stop the pipeline
                    try:
                        vector = get_nvidia_embedding(text_to_embed, input_type="passage")
                    except Exception as e:
                        print(f"⚠️ Embedding Failed: {e}")
                        vector = None

                    if vector:
                        data['embedding_vector'] = vector
                        es.index(index=INDEX_NAME, id=data['id'], document=data)
                        print(f"✅ Indexed: {data.get('title')}")
                    else:
                        print(f"⚠️ Skipped indexing (No vector): {data.get('title')}")

                except Exception as e:
                    print(f"⚠️ Processing Error: {e}")

        except Exception as e:
            print(f"💥 Critical Error: {e}. Retrying in 5s...")
            time.sleep(5)
        finally:
            try: consumer.close()
            except: pass

if __name__ == "__main__":
    run_sink()
