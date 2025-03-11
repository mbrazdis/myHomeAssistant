# app/services/mqtt_service.py
import paho.mqtt.client as mqtt
import json
import asyncio
import time
import logging
from typing import Dict, Any, Optional, Callable, List

# Import necessary modules and avoid circular imports
from app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)

class MQTTService:
    """Service for handling MQTT communication with devices"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MQTTService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._mqtt_client = mqtt.Client(client_id=settings.MQTT_CLIENT_ID)
        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_message = self._on_message
        self._mqtt_client.on_disconnect = self._on_disconnect
        self._status_callbacks = []
        self._main_event_loop = None
        self._initialized = True
        self._connected = False
        
        # Auto-connect during initialization
        try:
            logger.info(f"Connecting to MQTT broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
            self._mqtt_client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
            self._mqtt_client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
        
    def register_status_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Register a callback to be called when device status is updated"""
        self._status_callbacks.append(callback)
    
    def start(self):
        """Start the MQTT client and connect to broker"""
        try:
            self._main_event_loop = asyncio.get_event_loop()
            self._mqtt_client.connect(
                settings.MQTT_BROKER_HOST,
                settings.MQTT_BROKER_PORT,
                settings.MQTT_KEEPALIVE
            )
            self._mqtt_client.loop_start()
            logger.info("MQTT client started and connected to broker")
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")
    
    def stop(self):
        """Stop the MQTT client"""
        try:
            self._mqtt_client.disconnect()
            self._mqtt_client.loop_stop()
            logger.info("MQTT client stopped")
        except Exception as e:
            logger.error(f"Error stopping MQTT client: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connecting to MQTT broker"""
        if rc == 0:
            logger.info("Successfully connected to MQTT broker")
            self._connected = True
            # Subscribe to device topics
            client.subscribe("shellies/+/color/0/status")
            client.subscribe("shellies/+/light/0/power")
            client.subscribe("shellies/+/light/0/energy")
            client.subscribe("shellies/+/online")
            client.subscribe("shellies/+/color/0/status") 
            client.subscribe("shellies/+/status")
        else:
            self._connected = False
            logger.error(f"Failed to connect to MQTT broker with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnecting from MQTT broker"""
        self._connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker with code {rc}")
            # Try to reconnect
            try:
                client.reconnect()
            except Exception as e:
                logger.error(f"Failed to reconnect to MQTT broker: {e}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Callback when receiving MQTT messages"""
        try:
            topic_parts = msg.topic.split("/")
            device_id = topic_parts[1]  # Get the Shelly ID from the topic
            
            # Handle different types of messages
            if topic_parts[-1] == "online":
                # Online/offline status
                status = msg.payload.decode().lower() == "true"
                status_data = {"online": status}
                self._notify_status_update(device_id, status_data)
                
                # Import here to avoid circular imports
                from app.core.devices_manager import update_device_status
                update_device_status(device_id, status_data)
            
            elif topic_parts[-1] == "status" and topic_parts[-2] == "0" and topic_parts[-3] == "color":
                # Full device status update
                try:
                    payload_json = json.loads(msg.payload.decode())
                    status_data = {
                        "ison": payload_json.get("ison", False),
                        "mode": payload_json.get("mode", "color"),
                        "brightness": payload_json.get("brightness"),
                        "temp": payload_json.get("temp"),
                        "red": payload_json.get("red"),
                        "green": payload_json.get("green"),
                        "blue": payload_json.get("blue"),
                        "gain": payload_json.get("gain"),
                    }
                    
                    self._notify_status_update(device_id, status_data)
                    
                    # Import here to avoid circular imports
                    from app.core.devices_manager import update_device_status
                    update_device_status(device_id, status_data)
                    
                except json.JSONDecodeError:
                    logger.error(f"Failed to decode JSON status from {msg.topic}")
            
            elif topic_parts[-1] == "power" and topic_parts[-3] == "light":
                # Power consumption update
                try:
                    power = float(msg.payload.decode())
                    status_data = {"power": power}
                    self._notify_status_update(device_id, status_data)
                    
                    # Import here to avoid circular imports
                    from app.core.devices_manager import update_device_status
                    update_device_status(device_id, status_data)
                except ValueError:
                    logger.error(f"Invalid power value: {msg.payload.decode()}")
                
            elif topic_parts[-1] == "energy" and topic_parts[-3] == "light":
                # Energy consumption update
                try:
                    energy = float(msg.payload.decode())
                    status_data = {"energy": energy}
                    self._notify_status_update(device_id, status_data)
                    
                    # Import here to avoid circular imports
                    from app.core.devices_manager import update_device_status
                    update_device_status(device_id, status_data)
                except ValueError:
                    logger.error(f"Invalid energy value: {msg.payload.decode()}")
        
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _notify_status_update(self, device_id: str, status_data: Dict[str, Any]):
        """Notify all registered callbacks about a device status update"""
        for callback in self._status_callbacks:
            try:
                asyncio.run_coroutine_threadsafe(
                    callback(device_id, status_data),
                    self._main_event_loop
                )
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
    
    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> bool:
        """Publish a message to an MQTT topic"""
        try:
            result = self._mqtt_client.publish(topic, payload, qos, retain)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to publish to {topic}. Error: {result.rc}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error publishing to {topic}: {e}")
            return False
    
    def subscribe(self, topic: str, qos: int = 0) -> bool:
        """Subscribe to an MQTT topic"""
        try:
            result = self._mqtt_client.subscribe(topic, qos)
            if result[0] != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to subscribe to {topic}. Error: {result[0]}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error subscribing to {topic}: {e}")
            return False
    
    def unsubscribe(self, topic: str) -> bool:
        """Unsubscribe from an MQTT topic"""
        try:
            result = self._mqtt_client.unsubscribe(topic)
            if result[0] != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"Failed to unsubscribe from {topic}. Error: {result[0]}")
                return False
            return True
        except Exception as e:
            logger.error(f"Error unsubscribing from {topic}: {e}")
            return False

    def get_mqtt_client(self):
        """Get the underlying MQTT client for direct access"""
        return self._mqtt_client

    def is_connected(self) -> bool:
        """Check if connected to MQTT broker"""
        return self._connected and self._mqtt_client.is_connected()
    
    def ensure_connected(self) -> bool:
        """Ensure the client is connected before publishing"""
        if not self._mqtt_client.is_connected():
            try:
                logger.info(f"Reconnecting to MQTT broker at {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")
                self._mqtt_client.reconnect()
                # Give it a moment to connect
                time.sleep(0.5)
                return self._mqtt_client.is_connected()
            except Exception as e:
                logger.error(f"Failed to reconnect to MQTT broker: {e}")
                return False
        return True
        
    # Add a safe_publish method that ensures connection before publishing
    def safe_publish(self, topic: str, payload: Any, qos: int = 0, retain: bool = False) -> mqtt.MQTTMessageInfo:
        """Publish a message, ensuring the client is connected first"""
        if isinstance(payload, dict):
            payload = json.dumps(payload)
            
        if not self.ensure_connected():
            # Create a failed result
            result = mqtt.MQTTMessageInfo(mqtt.MQTT_ERR_NO_CONN)
            return result
            
        return self._mqtt_client.publish(topic, payload, qos, retain)

# Create a singleton instance
mqtt_service = MQTTService()

# Create an exported mqtt_client for backward compatibility
mqtt_client = mqtt_service.get_mqtt_client()

# Simplified backward compatibility functions
def init_mqtt_client():
    if not mqtt_service.is_connected():
        mqtt_service.ensure_connected()

def stop_mqtt_client():
    try:
        mqtt_service._mqtt_client.loop_stop()
        mqtt_service._mqtt_client.disconnect()
    except Exception as e:
        logger.error(f"Error stopping MQTT client: {e}")