import json
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("PAHO MQTT Connected with result code", rc)
    client.subscribe("kavachgrid/#")

def on_message(client, userdata, msg):
    print(f"PAHO Message received on {msg.topic}: {msg.payload.decode('utf-8')}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_start()

import time
time.sleep(2)
client.publish("kavachgrid/feeder/FEEDER-01", json.dumps({"test": "hello"}))
time.sleep(2)
client.loop_stop()
print("Test completed successfully!")
