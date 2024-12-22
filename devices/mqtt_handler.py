import paho.mqtt.client as mqtt
import json
import asyncio
import logging
from devices_manager import load_devices, update_device_status

logging.basicConfig(level=logging.INFO)

mqtt_client = mqtt.Client(client_id="smart-home-client")


def init_mqtt_client():
    try:
        mqtt_client.connect("192.168.100.140", 1883, 60)
        mqtt_client.loop_start()
        logging.info("MQTT client initialized successfully.")
    except Exception as e:
        logging.error(f"Failed to initialize MQTT client: {e}")


def stop_mqtt_client():
    mqtt_client.loop_stop()
    logging.info("MQTT client stopped.")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Successfully connected to MQTT broker.")
  
        client.subscribe("shellies/+/color/0/status")  
    else:
        logging.error(f"Failed to connect to MQTT broker. Result code: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        topic_parts = msg.topic.split("/")


        if topic_parts[-1] == "online":
            shelly_id = topic_parts[1]
            status = payload.lower() == "online"
            logging.info(f"Device {shelly_id} is now {'online' if status else 'offline'}.")


            update_device_status(shelly_id, {"ison": status})
        else:

            payload_json = json.loads(payload)
            shelly_id = topic_parts[1]
            status_details = {
                "ison": payload_json.get("ison"),
                "brightness": payload_json.get("brightness"),
                "temp": payload_json.get("temp"),
                "red": payload_json.get("red"),
                "green": payload_json.get("green"),
                "blue": payload_json.get("blue"),
                "gain": payload_json.get("gain"),
            }
            update_device_status(shelly_id, status_details)
    except Exception as e:
        logging.error(f"Error in on_message: {e}")

async def monitor_status_updates():

    TIMEOUT_SECONDS = 10

    while True:
        current_time = int(time.time())
        devices = load_devices()
        for device in devices:
            last_seen = device.get("last_seen", 0)
            if current_time - last_seen > TIMEOUT_SECONDS:
                if device["ison"]:
                    logging.warning(f"Device {device['device_id']} is inactive. Marking as off.")
                    device["ison"] = False
        save_devices(devices)
        await asyncio.sleep(5)


def unsubscribe_device(device_id: str):
    topic_status = f"shellies/{device_id}/color/0/status"
    result = mqtt_client.unsubscribe(topic_status)
    if result[0] == mqtt.MQTT_ERR_SUCCESS:
        logging.info(f"Unsubscribed from topic: {topic_status}")
    else:
        logging.warning(f"Failed to unsubscribe from topic: {topic_status}")


def clear_unused_subscriptions():
    try:
        mqtt_client.unsubscribe("#")
        logging.info("All subscriptions cleared successfully.")
    except Exception as e:
        logging.error(f"Failed to clear subscriptions: {e}")


def send_mqtt_command(device_id, payload):
    devices = load_devices()
    device = next((d for d in devices if d["device_id"] == device_id), None)
    if not device or "shelly_id" not in device:
        raise ValueError(f"Device {device_id} not found or missing shelly_id")
    topic = f"shellies/{device['shelly_id']}/color/0/set"
    try:
        mqtt_client.publish(topic, json.dumps(payload))
        logging.info(f"Sent MQTT command to {topic}: {payload}")
    except Exception as e:
        logging.error(f"Failed to send MQTT command: {e}")


def turn_on(device_id):
    topic = f"shellies/{device_id}/color/0/command"
    payload = "on"
    result = mqtt_client.publish(topic, payload)
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        logging.error(f"Failed to publish to {topic}. Error: {result.rc}")
    else:
        logging.info(f"Successfully published turn on command to {topic}")


def turn_off(device_id):
    topic = f"shellies/{device_id}/color/0/command"
    payload = "off"
    result = mqtt_client.publish(topic, payload)
    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        logging.error(f"Failed to publish to {topic}. Error: {result.rc}")
    else:
        logging.info(f"Successfully published turn off command to {topic}")


def set_brightness(device_id, brightness):
    send_mqtt_command(device_id, {"brightness": brightness})


def set_temp(device_id, temp):
    send_mqtt_command(device_id, {"temp": temp, "mode": "white"})


def set_color(device_id, red, green, blue, gain=100):
    send_mqtt_command(device_id, {"red": red, "green": green, "blue": blue, "gain": gain, "mode": "color"})


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
