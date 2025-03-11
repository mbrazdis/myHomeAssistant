# app/core/devices_manager.py
import json
import os
import time
import logging
from typing import Dict, Any, List

from app.core.config import settings

logger = logging.getLogger(__name__)

def load_devices() -> List[Dict[str, Any]]:
    """Load devices from the JSON file"""
    try:
        if os.path.exists(settings.DEVICES_FILE):
            with open(settings.DEVICES_FILE, 'r') as f:
                return json.load(f)
        else:
            # Create empty file if it doesn't exist
            with open(settings.DEVICES_FILE, 'w') as f:
                json.dump([], f)
            return []
    except Exception as e:
        logger.error(f"Error loading devices: {e}")
        return []

def save_devices(devices: List[Dict[str, Any]]) -> bool:
    """Save devices to the JSON file"""
    try:
        with open(settings.DEVICES_FILE, 'w') as f:
            json.dump(devices, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving devices: {e}")
        return False

def initialize_device(name: str, device_id: str, shelly_id: str) -> Dict[str, Any]:
    """Initialize a new device with default values"""
    devices = load_devices()
    
    # Check if device already exists
    for device in devices:
        if device['device_id'] == device_id:
            return device
    
    # Create new device
    new_device = {
        "name": name,
        "device_id": device_id,
        "shelly_id": shelly_id,
        "ison": False,
        "last_seen": int(time.time()),
        "source": "api",
        "has_timer": False,
        "timer_started": 0,
        "timer_duration": 0,
        "timer_remaining": 0,
        "mode": "color",
        "red": 255,
        "green": 255,
        "blue": 255,
        "white": 0,
        "gain": 100,
        "temp": 4750,
        "brightness": 100,
        "effect": 0,
        "energy": 0,
        "power": 0
    }
    
    devices.append(new_device)
    save_devices(devices)
    logger.info(f"Initialized new device: {device_id}")
    return new_device

def update_device_status(device_id: str, status_data: Dict[str, Any]) -> bool:
    """Update a device's status information"""
    devices = load_devices()
    
    # Find the device by ID or Shelly ID
    device = next(
        (d for d in devices if d.get("device_id") == device_id or d.get("shelly_id") == device_id), 
        None
    )
    
    if not device:
        logger.warning(f"Device {device_id} not found for status update")
        return False
    
    # Update the device status
    device.update(status_data)
    device["last_seen"] = int(time.time())
    
    # Save the updated devices
    save_success = save_devices(devices)
    if save_success:
        logger.info(f"Updated device {device_id} status: {status_data}")
    
    return save_success