import logging
import json
import asyncio
from typing import Dict, Any, Callable

# Import necessary modules and avoid circular imports
from app.core.config import settings
from app.services.device_state_machine import DeviceStateMachine

# Configure logger
logger = logging.getLogger(__name__)

class MQTTService:
    """Service for handling MQTT communication with devices"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MQTTService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, state_machine: DeviceStateMachine):
        if self._initialized:
            return

        self._initialized = True
        self.state_machine = state_machine
        self.client = self._create_mqtt_client()
        self.handlers: Dict[str, Callable[[str, bytes], None]] = {}

    def _create_mqtt_client(self):
        """Create and configure the MQTT client"""
        import paho.mqtt.client as mqtt
        client = mqtt.Client(settings.MQTT_CLIENT_ID)
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        client.on_disconnect = self.on_disconnect
        return client

    def register_handler(self, topic_prefix: str, handler: Callable[[str, bytes], None]):
        """Register a handler for a specific topic prefix"""
        self.handlers[topic_prefix] = handler

    def connect(self):
        """Connect to the MQTT broker"""
        self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, settings.MQTT_KEEPALIVE)
        self.client.loop_start()
        logger.info("Connected to MQTT broker")

    def disconnect(self):
        """Disconnect from the MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker")

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker"""
        if rc == 0:
            logger.info("MQTT connected successfully")
            # Subscribe to all necessary topics
            self.client.subscribe("shellies/#")
        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker"""
        if rc != 0:
            logger.warning("Unexpected MQTT disconnection. Reconnecting...")
            self.connect()

    def on_message(self, client, userdata, msg):
        """Callback for processing incoming MQTT messages"""
        topic = msg.topic
        payload = msg.payload

        logger.info(f"Received MQTT message on topic {topic}: {payload}")

        # Ignore null payloads
        if payload.decode().strip().lower() == "null":
            logger.warning(f"Ignoring null payload for topic {topic}")
            return

        # Process the message using DeviceStateMachine
        asyncio.create_task(self.state_machine.handle_message(topic, payload))

    async def publish(self, topic: str, payload: Dict[str, Any]):
        """Publish a message to a specific topic"""
        try:
            payload_str = json.dumps(payload)
            self.client.publish(topic, payload_str)
            logger.info(f"Published message to {topic}: {payload}")
        except Exception as e:
            logger.error(f"Failed to publish message to {topic}: {e}")