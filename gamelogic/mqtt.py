import paho.mqtt.client as mqtt
import json
from game_logic import *

BROKER_HOST = "test.mosquitto.org"

BROKER_PORT = 1883

START_GAME_TOPIC = "game/start"
FULL_GRID_TOPIC = "sudoku/game_sync" 
SYNCH_GAME_TOPIC = "game/grid"
UPDATE_GAME_TOPIC = "game/update"
RESTART_GAME_TOPIC = "game/restart"
RESTARTED_GAME_TOPIC = "game/restarted"
END_GAME_TOPIC = "game/end"
LED_GAME_TOPIC = "game/led"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully")
        # Souscrire aux topics avec QoS 0
        client.subscribe([(START_GAME_TOPIC, 0), (SYNCH_GAME_TOPIC, 0),(RESTART_GAME_TOPIC ,0),(RESTARTED_GAME_TOPIC ,0),(UPDATE_GAME_TOPIC,0),(END_GAME_TOPIC,0),(LED_GAME_TOPIC,0),(FULL_GRID_TOPIC, 0)])
        print(f"Subscribed to topics: {START_GAME_TOPIC}, {SYNCH_GAME_TOPIC},{RESTART_GAME_TOPIC},{RESTARTED_GAME_TOPIC},{END_GAME_TOPIC},{UPDATE_GAME_TOPIC},{LED_GAME_TOPIC},{FULL_GRID_TOPIC}")
    else:
        print(f"Connection failed with code {rc}")



def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Message received on topic {msg.topic}: {payload}")

        if msg.topic == START_GAME_TOPIC:
            handle_start_game(client, payload)
        elif msg.topic == SYNCH_GAME_TOPIC:
            print(f"Message brut reçu sur le topic {msg.topic} : {msg.payload}")
            handle_grid_update(client, payload)  
        elif msg.topic == RESTART_GAME_TOPIC:  
            print("Restart message received. Resetting the game.")
            restart_game(client, payload)  

    except json.JSONDecodeError as e:
        print(f"Invalid JSON message received: {e}")
    except Exception as e:
        print(f"Error handling message: {e}")



client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER_HOST, BROKER_PORT, 60)
except Exception as e:
    print(f"Failed to connect to broker: {e}")
    exit(1)

client.loop_forever()
