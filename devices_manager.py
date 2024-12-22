import json
import os
import logging
import time

DEVICES_FILE = "devices.json"

DEFAULT_DEVICE_STRUCTURE = {
    "status": "off",
    "ison": False,
    "last_seen": 0, 
    "source": "mqtt",
    "has_timer": False,
    "timer_started": 0,
    "timer_duration": 0,
    "timer_remaining": 0,
    "mode": "white",
    "red": 0,
    "green": 0,
    "blue": 0,
    "gain": 100,
    "temp": 3000,
    "brightness": 100,
    "effect": 0,
}

def load_devices():
    if not os.path.exists(DEVICES_FILE):
        return []
    with open(DEVICES_FILE, "r") as f:
        return json.load(f)

def save_devices(devices):
    with open(DEVICES_FILE, "w") as f:
        json.dump(devices, f, indent=4)

def initialize_device(name, device_id, shelly_id):

    return {"name": name, "device_id": device_id, "shelly_id": shelly_id, **DEFAULT_DEVICE_STRUCTURE}

def update_device_status(device_id, status_details):

    devices = load_devices()
    device_found = False
    current_time = int(time.time()) 

    for device in devices:
        if device["device_id"] == device_id or device.get("shelly_id") == device_id:
            logging.info(f"Updating device {device_id} with details {status_details}")
            device.update(status_details)
            device["last_seen"] = current_time 
            device_found = True
            break

    if not device_found:
        logging.warning(f"Device {device_id} not found. Initializing new device.")
        new_device = initialize_device(
            name=device_id,
            device_id=device_id,
            shelly_id=device_id,
        )
        new_device.update(status_details)
        new_device["last_seen"] = current_time
        devices.append(new_device)

    devices = remove_duplicates(devices)
    save_devices(devices)
    logging.info(f"Devices.json updated successfully with device {device_id}")
    return True

def remove_duplicates(devices):
    unique_devices = {}
    for device in devices:
        unique_key = device.get("device_id") or device.get("shelly_id")
        unique_devices[unique_key] = device
    return list(unique_devices.values())

def clean_devices_file():
    devices = load_devices()
    devices = remove_duplicates(devices)
    save_devices(devices)
    logging.info("Devices.json cleaned successfully.")
