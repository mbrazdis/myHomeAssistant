import asyncio
import logging
from typing import Dict, Any
import json

logger = logging.getLogger(__name__)

class DeviceStateMachine:
    def __init__(self):
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()  # Pentru a preveni accesul concurent

    async def update_device(self, device_id: str, status: Dict[str, Any]):
        """Actualizează starea unui dispozitiv"""
        async with self.lock:
            if device_id not in self.devices:
                self.devices[device_id] = {}
            self.devices[device_id].update(status)
            logger.info(f"Updated state for device {device_id}: {status}")

    async def get_device_status(self, device_id: str) -> Dict[str, Any]:
        """Obține statusul unui dispozitiv"""
        async with self.lock:
            return self.devices.get(device_id, {})

    async def get_all_devices(self) -> Dict[str, Dict[str, Any]]:
        """Obține statusul tuturor dispozitivelor"""
        async with self.lock:
            return self.devices.copy()

    async def handle_message(self, topic: str, payload: bytes):
        """Procesează mesajele primite de la MQTT și actualizează starea dispozitivelor"""
        try:
            payload_json = json.loads(payload.decode())
            device_id = topic.split("/")[1]  # Extrage ID-ul dispozitivului din topic

            # Determină tipul dispozitivului pe baza topicului
            if "light" in topic:
                status_data = {
                    "ison": payload_json.get("ison", False),
                    "brightness": payload_json.get("brightness"),
                    "temp": payload_json.get("temp"),
                    "red": payload_json.get("red"),
                    "green": payload_json.get("green"),
                    "blue": payload_json.get("blue"),
                }
                logger.info(f"Processed light status for {device_id}: {status_data}")
                await self.update_device(device_id, status_data)

            elif "sensor" in topic:
                status_data = {
                    "temperature": payload_json.get("temperature"),
                    "humidity": payload_json.get("humidity"),
                    "motion": payload_json.get("motion", False),
                }
                logger.info(f"Processed sensor status for {device_id}: {status_data}")
                await self.update_device(device_id, status_data)

            else:
                logger.warning(f"Unhandled topic type for {topic}")

        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON for topic {topic}. Raw payload: {payload}")
        except Exception as e:
            logger.error(f"Unexpected error processing message for topic {topic}: {e}")