import json
import os
import requests
from datetime import datetime
from confluent_kafka import Producer

# --- CONFIG ---
KAFKA_SERVER = os.environ.get('KAFKA_SERVER', 'kafka:29092')
TOPIC = "paris-disruptions"
PRIM_TOKEN = os.environ.get('PRIM_TOKEN')



def clean_text(text):
    """Removes HTML tags and cleans whitespace for better LLM processing."""
    if not text: return ""
    return text.replace("<br/>", " ").replace("<b>", "").replace("</b>", "").strip()

def run_producer():
    p = Producer({'bootstrap.servers': KAFKA_SERVER})
    
    # 1. SEND WIPE SIGNAL FIRST
    # This ensures your LLM only sees the latest "Actualité"
    p.produce(TOPIC, value=json.dumps({"control": "CLEAR_ALERTS"}).encode('utf-8'))
    p.flush()

    # 2. FETCH FROM API (Metro Only)
    url = "https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/line_reports/physical_modes/physical_mode:Metro/line_reports"
    headers = {"apikey": PRIM_TOKEN}
    params = {}#"count": 10} # Adjust as needed for testing

    try:
#         response_json=[
#             {"id": "674cb69a-dccc-11f0-a301-0a58a9feac02", "status": "future", "period": {"begin": "20251231T160000", "end": "20260101T043000"}, "severity": "bloquante", 
#                         "title": "Métro 12 / 8 : Mesures de sécurité - Arrêt non desservi", 
#                         "description": "<p>Le 31 décembre à partir de 16:00, l'arrêt ne sera pas desservi à Concorde en raison de mesures de sécurité</p>", "updated_at": "2025-12-23T10:05:46.759776"},
# {"id": "046fe3e0-dcc1-11f0-a301-0a58a9feac02", "status": "future", "period": {"begin": "20251231T160000", "end": "20260101T043000"}, "severity": "bloquante", 
#  "title": "Métro 1 : Mesures de sécurité - Arrêts non desservis", 
#  "description": "<p>Le 31 décembre à partir de 16:00, les arrêts ne seront pas desservis à Tuileries et Champs-Élysées – Clemenceau en raison de mesures de sécurité</p>", "updated_at": "2025-12-23T10:05:46.759787"},
# {"id": "44613c6a-dcc6-11f0-ac5b-0a58a9feac02", "status": "future", "period": {"begin": "20260101T001000", "end": "20260101T051500"}, "severity": "bloquante", 
#  "title": "Métro 2 : Mesures de sécurité - Arrêt non desservi", 
#  "description": "<p>Le 31 décembre à partir de 00:10 l'arrêt ne sera pas desservi à Ternes en raison de mesures de sécurité</p>", "updated_at": "2025-12-23T10:05:46.759799"}
# ]
        
        
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        response_json = response.json()

        disruptions_cleaned = []
        # for disruption in response_json:
        #     payload = json.dumps(disruption, ensure_ascii=False).encode('utf-8')
        #     p.produce(TOPIC, key=disruption['id'], value=payload)
        #     disruptions_cleaned.append(disruption)
          
            

        # Navigate the Navitia structure: Reports -> Disruptions
        for disruption in response_json.get("disruptions", []):
            
            # Filter for 'Actualité' tags as requested
            if 'Actualité' in disruption.get('tags', []):
                title = ""
                description = ""
                
                # Extract text based on channel types
                for message in disruption.get('messages', []):
                    channels = message.get('channel', {}).get('types', [])
                    if 'title' in channels:
                        title = clean_text(message.get('text'))
                    elif 'web' in channels:
                        description = clean_text(message.get('text'))

                # Build the LLM-optimized document
                to_copy = {
                    'id': disruption.get('id'),
                    'status': disruption.get('status'),
                    'period': disruption.get('application_periods', [{}])[0],
                    'severity': disruption.get('severity', {}).get('name'),
                    'title': title,
                    'description': description,
                    'updated_at': datetime.now().isoformat()
                }
                
                # Push to Kafka immediately
                # ensure_ascii=False is vital for the LLM to read French correctly
                payload = json.dumps(to_copy, ensure_ascii=False).encode('utf-8')
                p.produce(TOPIC, key=to_copy['id'], value=payload)
                disruptions_cleaned.append(to_copy)

        p.flush()
        print(f"✅ Successfully processed {len(disruptions_cleaned)} 'Actualité' alerts.")

    except Exception as e:
        print(f"❌ Producer Error: {e}")

if __name__ == "__main__":
    run_producer()
