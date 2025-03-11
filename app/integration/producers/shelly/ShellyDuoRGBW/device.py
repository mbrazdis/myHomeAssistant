from typing import Dict, Any, List
import logging
from app.integration.base_device import BaseDevice
import paho.mqtt.client as mqtt
from app.services.mqtt_service import mqtt_service
from app.services.command_queue_service import command_queue
from app.core.devices_manager import load_devices, update_device_status
import json


logger = logging.getLogger(__name__)

class ShellyColorBulb(BaseDevice):
    """Implementation for Shelly Color Bulb devices"""
    
    manufacturer = "shelly"
    device_type = "duorgbw"
    
    def __init__(self, device_id: str, shelly_id: str = None, name: str = None, **kwargs):
        self._device_id = device_id
        self._shelly_id = shelly_id or device_id
        self._name = name or device_id
        self._status = {
            "ison": False,
            "mode": "color",
            "brightness": 100,
            "temp": 4750,
            "red": 255,
            "green": 255,
            "blue": 255,
            "gain": 100,
            "power": 0,
            "energy": 0,
            "online": False
        }
        self._status.update(kwargs)
        
    # Add all required BaseDevice methods
    @property
    def device_id(self) -> str:
        return self._device_id
        
    @property
    def device_type(self) -> str:
        return self.__class__.device_type
        
    @property
    def manufacturer(self) -> str:
        return self.__class__.manufacturer
        
    # Make sure to implement all abstract methods from BaseDevice
    def get_status(self) -> Dict[str, Any]:
        return self._status.copy()
        
    def update_status(self, status_data: Dict[str, Any]) -> bool:
        self._status.update(status_data)
        return True
        
    # Add other required methods here

async def getStatus(device_id: str) -> Dict[str, Any]:
    """Get status for a device"""
    try:
        # Find the device first
        devices = load_devices()
        device = next((d for d in devices if d["device_id"] == device_id), None)
        
        if not device:
            logger.error(f"Device {device_id} not found")
            return None
            
        # Get shelly_id from the device
        shelly_id = device.get("shelly_id", device_id)
        
        # Request status update via MQTT
        topic = f"shellies/{shelly_id}/color/0/status"
        payload = ""  # Empty payload for status request
        
        # Use the safe_publish method
        result = mqtt_service.safe_publish(topic, payload)
        
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error(f"Failed to publish status request to {topic}. Error: {result.rc}")
            
        # Return current device data
        return device
    except Exception as e:
        logger.error(f"Error in getStatus: {e}")
        return None

async def turn_on(device_id: str) -> bool:
    """Turn on a device"""
    try:
        devices = load_devices()
        device = next((d for d in devices if d["device_id"] == device_id), None)
        
        if not device:
            logger.error(f"Device {device_id} not found")
            return False
            
        shelly_id = device.get("shelly_id", device_id)
        topic = f"shellies/{shelly_id}/color/0/command"
        payload = "on"
        
        # Use the safe_publish method instead
        result = mqtt_service.safe_publish(topic, payload)
        
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error(f"Failed to publish to {topic}. Error: {result.rc}")
            return False
            
        logger.info(f"Successfully published turn on command to {topic}")
        update_device_status(device_id, {"ison": True})
        return True
    except Exception as e:
        logger.error(f"Error in turn_on: {e}")
        return False

async def turn_off(device_id: str) -> bool:
    """Turn off a device"""
    try:
        devices = load_devices()
        device = next((d for d in devices if d["device_id"] == device_id), None)
        
        if not device:
            logger.error(f"Device {device_id} not found")
            return False
            
        shelly_id = device.get("shelly_id", device_id)
        topic = f"shellies/{shelly_id}/color/0/command"
        payload = "off"
        
        # Use the safe_publish method instead
        result = mqtt_service.safe_publish(topic, payload)
        
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error(f"Failed to publish to {topic}. Error: {result.rc}")
            return False
            
        logger.info(f"Successfully published turn off command to {topic}")
        update_device_status(device_id, {"ison": False})
        return True
    except Exception as e:
        logger.error(f"Error in turn_off: {e}")
        return False


async def set_color_multiple(device_ids: List[str], red: int, green: int, blue: int, gain: int = 100, white: int = 0) -> Dict[str, bool]:
    """Set the same color for multiple devices through the command queue"""
    async def execute_set_color(device_id: str, red: int, green: int, blue: int, gain: int = 100, white: int = 0) -> bool:
        try:
            # Find the device
            devices = load_devices()
            device = next((d for d in devices if d["device_id"] == device_id), None)
            
            if not device:
                logger.error(f"Device {device_id} not found")
                return False
                
            # Get shelly_id from the device
            shelly_id = device.get("shelly_id", device_id)
            
            # Create the topic and payload
            topic = f"shellies/{shelly_id}/color/0/set"
            payload = json.dumps({
                "mode": "color",
                "red": red,
                "green": green, 
                "blue": blue,
                "gain": gain,
                "white": white
            })
            
            # Send the command
            result = mqtt_service.safe_publish(topic, payload)
            
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to publish to {topic}. Error: {result.rc}")
                return False
                
            logger.info(f"Successfully published color command to {topic}")
            
            # Update device status
            update_device_status(device_id, {
                "mode": "color",
                "red": red,
                "green": green,
                "blue": blue,
                "gain": gain,
                "white": white
            })
            
            return True
        except Exception as e:
            logger.error(f"Error in set_color: {e}")
            return False
    
    single_device_mode = isinstance(device_ids, str)
    if single_device_mode:
        device_ids = [device_ids]
    
    results = await command_queue.add_bulk_command(
        device_ids=device_ids,   
        command_func=execute_set_color,
        command_args=[None, red, green, blue, gain, white],
        bypass_queue=True
    )

    if single_device_mode and device_ids:
        return results.get(device_ids[0], False)
    
    return results

async def set_white_multiple(device_ids: List[str], white: int, gain: int = 100, red: int = 0, green: int = 0, blue: int = 0, brightness: int = 100, temp: int = 4750) -> Dict[str, bool]:
    """Set white for multiple devices"""
    async def set_white(device_id: str, white: int, gain: int = 100, red: int = 0, green: int = 0, blue: int = 0, brightness: int = 100, temp: int = 4750) -> bool:
        """Set white for a device"""
        try:
            # Find the device
            devices = load_devices()
            device = next((d for d in devices if d["device_id"] == device_id), None)
            
            if not device:
                logger.error(f"Device {device_id} not found")
                return False
                
            # Get shelly_id from the device
            shelly_id = device.get("shelly_id", device_id)
            
            # Create the topic and payload
            topic = f"shellies/{shelly_id}/color/0/set"
            payload = json.dumps({
                "mode": "white",
                "white": white,
                "gain": gain,
                "red": red,
                "green": green,
                "blue": blue,
                "brightness": brightness,
                "temp": temp
            })
            
            # Send the command
            result = mqtt_service.safe_publish(topic, payload)
            
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to publish to {topic}. Error: {result.rc}")
                return False
                
            logger.info(f"Successfully published white command to {topic}")
            
            # Update device status
            update_device_status(device_id, {
                "mode": "white",
                "white": white,
                "gain": gain,
                "red": red,
                "green": green,
                "blue": blue, 
                "brightness": brightness,
                "temp": temp
            })
            
            return True
        except Exception as e:
            logger.error(f"Error in set_white: {e}")
            return False
        
    single_device_mode = isinstance(device_ids, str)
    if single_device_mode:
        device_ids = [device_ids]

    results = await command_queue.add_bulk_command(
        device_ids=device_ids,   
        command_func=set_white,
        command_args=[None, white, gain, red, green, blue, brightness, temp],
        bypass_queue=True
    )

    if single_device_mode and device_ids:
        return results.get(device_ids[0], False)
    
    return results

async def set_temperature_multiple(device_ids: List[str], temp: int) -> Dict[str, bool]:
    """Set the same color temperature for multiple devices"""
    async def set_temperature(device_id: str, temp: int) -> bool:
        """Set temperature for a device"""
        try:
            # Find the device
            devices = load_devices()
            device = next((d for d in devices if d["device_id"] == device_id), None)
            
            if not device:
                logger.error(f"Device {device_id} not found")
                return False
                
            # Validate temperature range
            valid_temp = max(3000, min(6465, temp))
            if valid_temp != temp:
                logger.warning(f"Temperature {temp}K adjusted to {valid_temp}K (valid range: 2700-6500K)")
            
            # Get shelly_id from the device
            shelly_id = device.get("shelly_id", device_id)
            
            # Create the topic and payload
            topic = f"shellies/{shelly_id}/color/0/set"
            
            # Log the exact payload we're sending
            payload_dict = {
                "mode": "white",
                "temp": valid_temp
            }
            payload = json.dumps(payload_dict)
            
            logger.info(f"Setting temperature for {device_id} with payload: {payload_dict}")
            
            # Send the command
            result = mqtt_service.safe_publish(topic, payload)
            
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to publish to {topic}. Error: {result.rc}")
                return False
                
            logger.info(f"Successfully published temperature command to {topic}")
            
            # Update device status
            update_device_status(device_id, {"temp": valid_temp})
            
            return True
        except Exception as e:
            logger.error(f"Error in set_temperature: {e}")
            return False
    single_device_mode = isinstance(device_ids, str)
    if single_device_mode:
        device_ids = [device_ids]

    results = await command_queue.add_bulk_command(
        device_ids=device_ids,   
        command_func=set_temperature,
        command_args=[None, temp],
        bypass_queue=True
    )

    if single_device_mode and device_ids:
        return results.get(device_ids[0], False)
    
    return results

async def set_brightness_multiple(device_ids: List[str], brightness: int) -> Dict[str, bool]:
    """Set the same brightness for multiple devices"""
    async def set_brightness(device_id: str, brightness: int) -> bool:
        """Set brightness for a device (0-100) - simplified version"""
        try:
            # Find the device
            devices = load_devices()
            device = next((d for d in devices if d["device_id"] == device_id), None)
            
            if not device:
                logger.error(f"Device {device_id} not found")
                return False
                
            # Ensure brightness is within valid range
            brightness = max(0, min(100, brightness))
                
            # Get shelly_id from the device
            shelly_id = device.get("shelly_id", device_id)
            
            # Create the topic and payload - just sending brightness for all modes
            topic = f"shellies/{shelly_id}/color/0/set"
            
            # Simple approach - send both parameters that could affect brightness
            payload = {
                "brightness": brightness,
            }
            
            # Send the command
            result = mqtt_service.safe_publish(topic, json.dumps(payload))
            
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to publish to {topic}. Error: {result.rc}")
                return False
                
            logger.info(f"Successfully published brightness command to {topic} with payload: {payload}")
            
            # Update device status with both brightness parameters
            update_device_status(device_id, {
                "brightness": brightness,
            })
            
            return True
        except Exception as e:
            logger.error(f"Error in set_brightness: {e}")
            return False
        
    single_device_mode = isinstance(device_ids, str)
    if single_device_mode:
        device_ids = [device_ids]
    
    results = await command_queue.add_bulk_command(
        device_ids=device_ids,
        command_func=set_brightness,
        command_args=[None, brightness],
        bypass_queue=True
    )

    if single_device_mode and device_ids:
        return results.get(device_ids[0], False)
    
    return results


async def set_color(device_id: str, red: int, green: int, blue: int, gain: int = 100) -> bool:
    """Compatibility function that calls set_color_multiple for a single device"""
    results = await set_color_multiple(device_id, red, green, blue, gain)
    return results if isinstance(results, bool) else results.get(device_id, False)

async def set_white(device_id: str, white: int, gain: int = 100, red: int = 0, green: int = 0, blue: int = 0, brightness: int = 100, temp: int = 4750) -> bool:
    """Compatibility function that calls set_white_multiple for a single device"""
    results = await set_white_multiple(device_id, white, gain, red, green, blue, brightness, temp)
    return results if isinstance(results, bool) else results.get(device_id, False)

async def set_temperature(device_id: str, temp: int) -> bool:
    """Compatibility function that calls set_temperature_multiple for a single device"""
    results = await set_temperature_multiple(device_id, temp)
    return results if isinstance(results, bool) else results.get(device_id, False)

async def set_brightness(device_id: str, brightness: int) -> bool:
    """Compatibility function that calls set_brightness_multiple for a single device"""
    results = await set_brightness_multiple(device_id, brightness)
    return results if isinstance(results, bool) else results.get(device_id, False)