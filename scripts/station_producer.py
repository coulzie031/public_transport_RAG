import sys
import os
import time
import json
import requests
from confluent_kafka import Producer

# 1. IMMEDIATE LOGGING TEST
print("--- SCRIPT STARTING ---", flush=True)

# 2. CHECK ENVIRONMENT
api_key = os.environ.get("PRIM_TOKEN")
kafka_server = os.environ.get("KAFKA_SERVER", "kafka:29092")

if not api_key:
    print("❌ ERROR: PRIM_TOKEN is missing!", flush=True)
    sys.exit(1)

print(f"🔗 Connecting to Kafka at: {kafka_server}", flush=True)

def delivery_report(err, msg):
    if err is not None:
        print(f"❌ Kafka Error: {err}", flush=True)
    else:
        print(f"✅ Message delivered to {msg.topic()}", flush=True)

def run():
    try:
        p = Producer({'bootstrap.servers': kafka_server})
        
        url = 'https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/commercial_modes/commercial_mode:Metro/stop_areas'
        headers = {"apikey": api_key}
        
        print("🌐 Fetching from PRIM API...", flush=True)
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        stations = response.json().get("stop_areas", [])
        print(f"📦 Found {len(stations)} stations.", flush=True)

        for station in stations:
            entry = {
                "id": station["id"],
                "name": station["name"],
                "lat": station["coord"]["lat"],
                "lon": station["coord"]["lon"]
            }
            p.produce('paris-stations', key=entry["id"], value=json.dumps(entry), callback=delivery_report)
        
        print("⏳ Flushing data to Kafka...", flush=True)
        # CRITICAL: Wait up to 30 seconds for the network transfer
        p.flush(30) 
        print("🚀 DONE. Exiting successfully.", flush=True)

    except Exception as e:
        print(f"💥 CRITICAL FAILURE: {str(e)}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    run()
