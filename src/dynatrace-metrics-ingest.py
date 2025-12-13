import paho.mqtt.client as mqtt
import requests
import json
import time
import os      
from dotenv import load_dotenv

load_dotenv()

# Dynatrace Configuration from environment variables
TENANT_HOST = os.getenv("TENANT_HOST")
API_TOKEN = os.getenv("API_TOKEN")
DT_METRICS_INGEST_ENDPOINT = f"https://{TENANT_HOST}/api/v2/metrics/ingest"

# MQTT Configuration from environment variables
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_USER = os.getenv("MQTT_USER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
MQTT_CLIENT_ID = os.getenv("MQTT_CLIENT_ID")
MQTT_TOPIC = os.getenv("MQTT_TOPIC")

METRIC_MAP = {
    "1.8.0": "smartmeter.energy.active.import.total",  
    "2.8.0": "smartmeter.energy.active.export.total", 
    "3.8.1": "smartmeter.energy.reactive.import.total",
    "4.8.1": "smartmeter.energy.reactive.export.total",
    "1.7.0": "smartmeter.power.active.import",        
    "2.7.0": "smartmeter.power.active.export",        
    "3.7.0": "smartmeter.power.reactive.import",
    "4.7.0": "smartmeter.power.reactive.export",
    "saldo": "smartmeter.power.active.saldo",    
    "1.128.0": "smartmeter.inkasso"
}

def send_to_dynatrace(payload):
    if not payload:
        return

    payload_str = "\n".join(payload)
    headers = {
        "Authorization": f"Api-Token {API_TOKEN}",
        "Content-Type": "text/plain; charset=utf-8"
    }

    try:
        r = requests.post(DT_METRICS_INGEST_ENDPOINT, headers=headers, data=payload_str, timeout=5)
        
        if r.status_code == 202:
            print(f"Dynatrace Ingest Success ({len(payload)} metrics)")
        else:
            print(f"Dynatrace Error {r.status_code}: {r.text}")
            
    except requests.RequestException as e:
        print(f"Network Error sending to Dynatrace: {e}")
        
        

# MQTT callback for connection
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC)
        print(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"Failed to connect, return code {reason_code}")

# MQTT callback for message reception and sending to Dynatrace
def on_message(client, userdata, msg):
    try:
        # 1. Parse JSON
        payload_str = msg.payload.decode('utf-8')
        data = json.loads(payload_str)
        
        dt_payload_lines = []

        # 2. Iterate over the JSON keys and map them
        for key, value in data.items():
            # We skip 'time' because we are using ingest time
            if key == "time": 
                continue
            
            if key in METRIC_MAP:
                metric_key = METRIC_MAP[key]
                line = f"{metric_key} {value}"
                dt_payload_lines.append(line)
            else:
                pass

        # 3. Send to Dynatrace
        if dt_payload_lines:
            print(f"\nReceived MQTT Data. Sending {len(dt_payload_lines)} metrics...")
            send_to_dynatrace(dt_payload_lines)
        
    except json.JSONDecodeError:
        print(f"Received non-JSON message")
    except Exception as e:
        print(f"Error in processing: {e}")
       
# MQTT Client Setup
client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2, 
    client_id=MQTT_CLIENT_ID
)

# set authentication and callbacks
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

# Connect to MQTT Broker and start loop
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print(f"Sending data to {DT_METRICS_INGEST_ENDPOINT}")
    
    
    while True:
        time.sleep(1)

except Exception as e:
    print(f"Error: {e}")
finally:
    client.loop_stop()