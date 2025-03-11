import json
import os
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger

class DeviceRepository:
    def __init__(self, file_path: str = settings.DEVICES_JSON_PATH):
        self.file_path = file_path
        
    def load_devices(self) -> List[Dict[str, Any]]:
        try:
            if not os.path.exists(self.file_path):
                logger.warning(f"Devices file not found: {self.file_path}, creating empty file")
                self.save_devices([])
                
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load devices: {e}")
            return []
            
    def save_devices(self, devices: List[Dict[str, Any]]) -> bool:
        try:
            with open(self.file_path, 'w') as f:
                json.dump(devices, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Failed to save devices: {e}")
            return False
            
    def get_device_by_id(self, device_id: str) -> Optional[Dict[str, Any]]:
        devices = self.load_devices()
        return next((d for d in devices if d.get("device_id") == device_id or d.get("shelly_id") == device_id), None)
        
    def update_device(self, device_id: str, updates: Dict[str, Any]) -> bool:
        devices = self.load_devices()
        
        for i, device in enumerate(devices):
            if device.get("device_id") == device_id or device.get("shelly_id") == device_id:
                devices[i] = {**device, **updates}
                logger.info(f"Updating device {device_id} with details {updates}")
                return self.save_devices(devices)
                
        logger.error(f"Device not found for update: {device_id}")
        return False