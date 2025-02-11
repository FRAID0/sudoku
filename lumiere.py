LED_COUNT      = 150      # Number of LED pixels.
LED_PIN        = 18       # GPIO pin connected to pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000   # LED signal frequency in hertz (usually 800 kHz).
LED_DMA        = 10       # DMA channel to be used to generate the signal (try 10).
LED_BRIGHTNESS = 65       # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False    # True to invert the signal (when using NPN transistor level switching)
LED_CHANNEL    = 0        # set to '1' for GPIO 13, 19, 41, 45 or 53

import time
from rpi_ws281x import *
import argparse
import paho.mqtt.client as mqtt

# Configuration MQTT
broker = "iot.it.hs-worms.de"
#broker = "192.168.2.124"
port = 4105

LED_GAME_TOPIC = "game/led"
LED_GAME_TOPIC_SELBST = "game/led/1"
username = "pass"
password = "passmqtt"

def color_wipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()
    time.sleep(wait_ms / 1000.0)

def on_connect(client, userdata, flags, rc):
    """Callback function when connected to MQTT broker"""
    if rc == 0:
        print("Connected to the MQTT broker")
        client.subscribe(LED_GAME_TOPIC)
        client.subscribe(LED_GAME_TOPIC_SELBST)
        print("Subscribed successfully to", LED_GAME_TOPIC, LED_GAME_TOPIC_SELBST)
    else:
        print(f"Failed to connect, return code {rc}\n")

def on_message(client, userdata, msg):
    """Callback function when a message is received from the MQTT broker"""
    global strip  # Ensure strip is accessible
    message = msg.payload.decode()
    print(f"Received message: {message}")
    if message == '{"state": "on"}':
        color_wipe(strip, Color(255, 255, 255))  # Switch on the white light
    elif message == '{"state": "red"}':
        color_wipe(strip, Color(255, 0, 0))  # Set color to red
    elif message == '{"state": "green"}':
        color_wipe(strip, Color(0, 255, 0))  # Set color to green
    elif message == '{"state": "blue"}':
        color_wipe(strip, Color(0, 0, 255))  # Set color to blue
    elif message == '{"state": "off"}':
        color_wipe(strip, Color(0, 0, 0))  # Switch off LEDs

if __name__ == '__main__':
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    strip.begin()

    # Set up MQTT client
    client = mqtt.Client()
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker, port, 60)
    client.loop_start()

    print('Press Ctrl-C to quit.')
    if not args.clear:
        print('Use "-c" argument to clear LEDs on exit')

    try:
        # Keep the script running to listen to MQTT messages
        while True:
            time.sleep(1)  # Avoid busy waiting
    except KeyboardInterrupt:
        if args.clear:
            color_wipe(strip, Color(0, 0, 0), 10)  # Turn off LEDs on exit
        client.loop_stop()
        client.disconnect()
