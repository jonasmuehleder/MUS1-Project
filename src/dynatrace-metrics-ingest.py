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


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Connected to MQTT Broker!")
    else:
        print(f"Failed to connect, return code {reason_code}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
client.on_connect = on_connect

try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    
    print(f"Sending data to {DT_METRICS_INGEST_ENDPOINT}")
    
    # Keep running so we can see the connection messages
    time.sleep(5) 

except Exception as e:
    print(f"Error: {e}")
finally:
    client.loop_stop()