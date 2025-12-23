import time
import json
import os
import requests
from confluent_kafka import Producer
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("PRIM_TOKEN")
KAFKA_CONF = {'bootstrap.servers': os.environ.get('KAFKA_SERVER', 'kafka:29092')}

def delivery_report(err, msg):
    if err is not None:
        print(f"❌ Delivery failed: {err}")
    # We won't print success for every station to avoid flooding your console

def run_producer():
    p = Producer(KAFKA_CONF)
    topic = "paris-metro-stations"
    
    print(f"🚀 Producer started. Pushing whole batch to '{topic}'")

    try:
        while True:
            start_time = time.time()
            
            # 1. Fetch data from API
            url = 'https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/commercial_modes/commercial_mode:Metro/stop_areas'
            headers = {"apikey": api_key}
            params = {"count": 1000} 
            
            
            test_data = [
                    {"id": "test:1", "name": "Aéroport d'Orly", "zone": "Sud"},
                    {"id": "test:2", "name": "Montparnasse-Bienvenüe", "line": "13"},
                    {"id": "test:3", "name": "Étienne Marcel", "status": "Ouverte"},
                    {"id": "test:4", "name": "Château d'Eau", "note": "Check apostrophe \u0027"},
                    {"id": "test:5", "name": "Bibliothèque François-Mitterrand", "type": "RER"}
                ]

            try:
                for station in test_data:
                    entry = {
                        "id": station["id"],
                        "name": station["name"],   
                    }
                        # produce() is ASYNCHRONOUS - it just adds to a local buffer
                    
                    p.produce(
                        topic, 
                        key=entry["id"], 
                        value=json.dumps(entry).encode('utf-8'),
                        callback=delivery_report
                    )
                    p.poll(0)
                
                
                
                
                # response = requests.get(url, headers=headers, params=params, timeout=10)
                # response.raise_for_status()
                # data = response.json()
                # stations = data.get("stop_areas", [])
                
                # print(f"Fetched {len(stations)} stations. Starting Kafka produce...")

                # # 2. Queue the entire batch
                # for station in stations:
                #     entry = {
                #         "id": station["id"],
                #         "name": station["name"],
                #         "coordinates": {
                #             "lat": station["coord"]["lat"],
                #             "lon": station["coord"]["lon"]
                #         }
                #     }
                    
                #     # produce() is ASYNCHRONOUS - it just adds to a local buffer
                #     p.produce(
                #         topic, 
                #         key=entry["id"], 
                #         value=json.dumps(entry).encode('utf-8'),
                #         callback=delivery_report
                #     )
                #     # Serve any pending delivery callbacks
                #     p.poll(0)

                # 3. FLUSH ONCE: This sends the whole buffer to Kafka in one go
                print("Flushing batch to broker...")
                p.flush()
                print(f"Batch sent successfully at {time.strftime('%H:%M:%S')}")

            except Exception as e:
                print(f"⚠️ Error during batch: {e}")


    except KeyboardInterrupt:
        print("Stopping producer...")
    finally:
        p.flush()

if __name__ == "__main__":
    run_producer()
