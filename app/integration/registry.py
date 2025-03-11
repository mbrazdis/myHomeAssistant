# app/integrations/registry.py
from typing import Dict, List, Type, Optional, Any
import importlib
import logging
from app.integration.base_device import BaseDevice

logger = logging.getLogger(__name__)

class DeviceRegistry:
    """Registry for managing device implementations"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DeviceRegistry, cls).__new__(cls)
            cls._instance._device_types = {}  # {manufacturer: {device_type: device_class}}
            cls._instance._devices = {}  # {device_id: device_instance}
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._load_device_types()
    
    def _load_device_types(self):
        """Load all device types from integrations"""
        try:
            # This could be made more dynamic by discovering modules
            # For now, we'll manually register known integrations
            
            # Shelly integrations
            from app.integration.producers.shelly.ShellyDuoRGBW import ShellyColorBulb
            self.register_device_type(ShellyColorBulb)
            
            # You would add more here as they are created
            # from app.integrations.shelly.plug.device import ShellyPlug
            # self.register_device_type(ShellyPlug)
            
        except Exception as e:
            logger.error(f"Error loading device types: {e}")
    
    def register_device_type(self, device_class: Type[BaseDevice]):
        """Register a device type with the registry"""
        try:
            manufacturer = device_class.manufacturer
            device_type = device_class.device_type
            
            if manufacturer not in self._device_types:
                self._device_types[manufacturer] = {}
            
            self._device_types[manufacturer][device_type] = device_class
            logger.info(f"Registered device type: {manufacturer}/{device_type}")
            
        except Exception as e:
            logger.error(f"Error registering device type {device_class.__name__}: {e}")
    
    def get_device_class(self, manufacturer: str, device_type: str) -> Optional[Type[BaseDevice]]:
        """Get a device class by manufacturer and type"""
        return self._device_types.get(manufacturer, {}).get(device_type)
    
    def register_device_instance(self, device: BaseDevice):
        """Register a device instance with the registry"""
        self._devices[device.device_id] = device
    
    def get_device(self, device_id: str) -> Optional[BaseDevice]:
        """Get a device instance by ID"""
        return self._devices.get(device_id)
    
    def get_all_devices(self) -> List[BaseDevice]:
        """Get all registered device instances"""
        return list(self._devices.values())
    
    def create_device(self, manufacturer: str, device_type: str, device_id: str, **kwargs) -> Optional[BaseDevice]:
        """Create and register a new device instance"""
        device_class = self.get_device_class(manufacturer, device_type)
        if not device_class:
            logger.error(f"No device class found for {manufacturer}/{device_type}")
            return None
        
        try:
            device = device_class(device_id=device_id, **kwargs)
            self.register_device_instance(device)
            return device
        except Exception as e:
            logger.error(f"Error creating device {device_id}: {e}")
            return None

# Create a singleton instance
device_registry = DeviceRegistry()