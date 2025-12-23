import requests
from requests.auth import HTTPBasicAuth

# ---------------------------------------------------------
# 1. 🛑 REPLACE THIS WITH THE KEY YOU COPIED FROM PRIM
# It should look like: '8e401a23-45b6-...' (Not 3b036...)
MY_REAL_KEY = "RO29yT8rnY192fRyHgE2DV57jiQWXOCI"
# ---------------------------------------------------------

# 2. 🌍 The Traffic URL
url = "https://api.navitia.io/v1/coverage/fr-idf/traffic_reports"

print(f"📡 Testing Key: {MY_REAL_KEY[:5]}... (hidden)")

try:
    # 3. 🔐 AUTHENTICATION FIX
    # Navitia expects: Username = Key, Password = Empty string
    auth_method = HTTPBasicAuth(MY_REAL_KEY, "")
    print(auth_method)
    
    response = requests.Request(url, auth=auth_method)
    prepared = response.prepare()
    print('here')
    print(prepared.headers)
    print(prepared.url)        
    # 4. ✅ CHECK RESULT
    if response.status_code == 200:
        print("\n✅ SUCCESS! Authentication accepted.")
        data = response.json()
        
        # Show count of alerts
        disruptions = data.get("disruptions", [])
        print(f"📢 Active Traffic Alerts Found: {len(disruptions)}")
        
        # Show first alert title
        if disruptions:
            first_msg = disruptions[0]['messages'][0]['text']
            print(f"🔸 Example: {first_msg[:100]}...")
            
    elif response.status_code == 401:
        print("\n❌ STILL 401 ERROR: The key is still wrong.")
        print("👉 Did you copy the 'Jeton API' exactly from the PRIM dashboard?")
    else:
        print(f"\n❌ Error {response.status_code}: {response.text}")

except Exception as e:
    print(f"Critical Error: {e}")