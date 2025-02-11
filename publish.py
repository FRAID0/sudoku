import paho.mqtt.client as mqtt
import json

class MQTTClient:
    def __init__(self):
        # Create an instance of MQTT client
        self.client = mqtt.Client()

        # Assign callback functions
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish

        # Connect to the MQTT broker
        self.host = "iot.it.hs-worms.de"
        self.port = 4105
        self.keepalive = 60
        self.LED_GAME_TOPIC = "game/led"
        self.client_id = ""  # Leave empty for auto-generated ID
        self.client.connect(self.host, self.port, self.keepalive)

        # Start the message handling loop
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback function when connected to the broker"""
        if rc == 0:
            print("Connected to the MQTT broker")
        else:
            print(f"Connection failed with result code {rc}")

    def on_disconnect(self, client, userdata, rc, properties=None):
        """Callback function when disconnected from the broker"""
        print(f"Disconnected from the MQTT broker with reason code {rc}")

    def on_publish(self, client, userdata, mid, reason_code=None, properties=None):
        """Callback function when a message is successfully published"""
        print(f"Message published successfully with reason code {reason_code}")

    @property
    def callback_api_version(self):
        return "MQTT API Version 1.0"

    def publish(self, LED_GAME_TOPIC, payload, qos=0, retain=False):
        """Publish a message"""
        json_payload = json.dumps(payload)  # Convert dict to JSON string
        self.client.publish(LED_GAME_TOPIC, json_payload, qos, retain)
        print(f"Published message on topic '{LED_GAME_TOPIC}': {json_payload}")

    def disconnect(self):
        """Clean disconnection"""
        self.client.loop_stop()
        self.client.disconnect()

if __name__ == "__main__":
    mqtt_client = MQTTClient()

    mqtt_client.publish("game/led", {"state": "red"})
    mqtt_client.disconnect()
