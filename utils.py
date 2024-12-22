import time
import json
import logging
from devices.mqtt_handler import mqtt_client

def get_shelly_status(shelly_id: str):
    """
    Trimite o cerere MQTT pentru a obține starea dispozitivului Shelly.
    """
    status_topic = f"shellies/{shelly_id}/color/0/get"
    response_topic = f"shellies/{shelly_id}/color/0/status"
    status_data = None

    def on_message(client, userdata, message):
        nonlocal status_data
        if message.topic == response_topic:
            status_data = json.loads(message.payload.decode())
            logging.info(f"Received MQTT status for {shelly_id}: {status_data}")

    try:
        mqtt_client.subscribe(response_topic)
        mqtt_client.on_message = on_message

        mqtt_client.publish(status_topic, "")
        logging.info(f"Requested status from Shelly {shelly_id} via MQTT.")


        for _ in range(10):
            if status_data:
                break
            time.sleep(1)

        if not status_data:
            logging.warning(f"No status received from Shelly {shelly_id} after 10 seconds.")
        return status_data
    finally:
        mqtt_client.unsubscribe(response_topic)
        logging.info(f"Unsubscribed from {response_topic}")
