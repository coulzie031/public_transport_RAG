import os
import requests
import dotenv



# --- CONFIG ---
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY") # Don't forget to set this!
NVIDIA_MODEL = "nvidia/nv-embedqa-e5-v5" # Or "snowflake/arctic-embed-l"

def get_nvidia_embedding(text, input_type="passage"):
    """
    Calls NVIDIA NIM API to get embeddings.
    input_type: "passage" (for storing) or "query" (for searching)
    """
    if not text: return []
    
    invoke_url = "https://integrate.api.nvidia.com/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "input": [text],
        "model": NVIDIA_MODEL,
        "input_type": input_type, 
        "encoding_format": "float"
    }

    try:
        response = requests.post(invoke_url, headers=headers, json=payload, timeout=5)
        response.raise_for_status()
        # Extract the vector
        return response.json()['data'][0]['embedding']
    except Exception as e:
        print(f"⚠️ NVIDIA API Error: {e}")
        return []
