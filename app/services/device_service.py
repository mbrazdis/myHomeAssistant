# app/services/device_service.py
from typing import List, Dict, Any, Optional
import logging
from app.repositories.device_repository import DeviceRepository
from app.services.mqtt_service import mqtt_service
from app.services.websocket_service import manager
from app.integration.registry import device_registry

logger = logging.getLogger(__name__)

class DeviceService:
    def __init__(self):
        self._device_repository = DeviceRepository()
        # Register WebSocket broadcast as a callback for MQTT status updates
        mqtt_service.register_status_callback(self._on_device_status_update)
        
    async def _on_device_status_update(self, device_id: str, status: Dict[str, Any]):
        # Update device in registry if it exists
        device = device_registry.get_device(device_id)
        if device:
            device.update_status(status)
        
        # Broadcast status to WebSocket clients
        await manager.broadcast_device_status(device_id, status)
        
    def get_all_devices(self) -> List[Dict[str, Any]]:
        return self._device_repository.load_devices()
        
    def get_device_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        return self._device_repository.get_device_by_id(device_id)
        
    def update_device(self, device_id: str, updates: Dict[str, Any]) -> bool:
        return self._device_repository.update_device(device_id, updates)

# Singleton instance
device_service = DeviceService()