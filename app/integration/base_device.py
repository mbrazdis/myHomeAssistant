from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class BaseDevice(ABC):
    """Base abstract class for device implementations"""
    
    @property
    @abstractmethod
    def device_id(self) -> str:
        """Get the device ID"""
        pass
    
    @property
    @abstractmethod
    def device_type(self) -> str:
        """Get the device type"""
        pass
    
    @property
    @abstractmethod
    def manufacturer(self) -> str:
        """Get the manufacturer"""
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get the device status"""
        pass
    
    @abstractmethod
    def update_status(self, status_data: Dict[str, Any]) -> bool:
        """Update the device status"""
        pass