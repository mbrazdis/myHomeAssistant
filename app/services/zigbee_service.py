# app/services/zigbee_service.py
import logging
import asyncio
import time
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class ZigbeeService:
    """Simple service for testing connectivity with Sonoff Zigbee Dongle"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ZigbeeService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self._dongle_path = "/dev/ttyUSB0"  # Default path
        self._connected = False
        self._zigpy_available = False
        self._app = None
        
        # Check if zigpy and zigpy-znp are available
        try:
            import zigpy
            import zigpy_znp
            self._zigpy_available = True
            logger.info("ZigBee libraries found")
        except ImportError:
            logger.warning("ZigBee libraries not found. Install with: pip install zigpy zigpy-znp")
    
    def set_dongle_path(self, path: str):
        """Set the path to the Zigbee dongle"""
        self._dongle_path = path
        logger.info(f"ZigBee dongle path set to: {path}")
    
    async def connect(self):
        """Connect to the Zigbee dongle"""
        if not self._zigpy_available:
            logger.error("Cannot connect: ZigBee libraries not available")
            return False
        
        try:
            # Check if the dongle path exists
            if not os.path.exists(self._dongle_path):
                logger.error(f"ZigBee dongle not found at {self._dongle_path}")
                return False
            
            # Import here to prevent errors if libraries are not installed
            from zigpy_znp.zigbee.application import ControllerApplication
            
            # Basic configuration for the Sonoff Zigbee Dongle
            config = {
                "device": {
                    "path": self._dongle_path,
                },
                "database_path": "zigbee.db",
            }
            
            # Connect to the dongle
            logger.info(f"Connecting to ZigBee dongle at {self._dongle_path}...")
            self._app = await ControllerApplication.new(config)
            
            # Get dongle information
            version_info = await self._app.version()
            logger.info(f"Connected to ZigBee dongle: {version_info}")
            
            # Start the network
            await self._app.startup(auto_form=True)
            network_info = await self._app.get_network_info()
            logger.info(f"ZigBee network information: {network_info}")
            
            self._connected = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to ZigBee dongle: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected to the Zigbee dongle"""
        return self._connected
    
    async def scan_devices(self) -> List[Dict[str, Any]]:
        """Scan for Zigbee devices"""
        if not self._connected or not self._app:
            logger.error("Not connected to ZigBee dongle")
            return []
        
        try:
            devices = []
            # Get all devices from the zigbee network
            for ieee, dev in self._app.devices.items():
                device_info = {
                    "ieee": str(ieee),
                    "nwk": dev.nwk,
                    "manufacturer": dev.manufacturer,
                    "model": dev.model,
                    "name": dev.name or f"ZigBee Device {str(ieee)[-8:]}",
                    "last_seen": dev.last_seen,
                }
                devices.append(device_info)
                logger.info(f"Found ZigBee device: {device_info}")
            
            return devices
        except Exception as e:
            logger.error(f"Error scanning for ZigBee devices: {e}")
            return []
    
    async def disconnect(self):
        """Disconnect from the Zigbee dongle"""
        if self._connected and self._app:
            try:
                await self._app.shutdown()
                self._connected = False
                self._app = None
                logger.info("Disconnected from ZigBee dongle")
                return True
            except Exception as e:
                logger.error(f"Error disconnecting from ZigBee dongle: {e}")
                return False
        return True
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to the Zigbee dongle and return status information"""
        if not self._zigpy_available:
            return {
                "status": "error",
                "message": "ZigBee libraries not available. Install with: pip install zigpy zigpy-znp",
                "dongle_path": self._dongle_path,
                "device_exists": os.path.exists(self._dongle_path),
            }
        
        result = {
            "status": "disconnected",
            "dongle_path": self._dongle_path,
            "device_exists": os.path.exists(self._dongle_path),
        }
        
        # Check if the device exists
        if not os.path.exists(self._dongle_path):
            result["message"] = f"ZigBee dongle not found at {self._dongle_path}"
            return result
        
        # If already connected, return status
        if self._connected and self._app:
            try:
                version_info = await self._app.version()
                network_info = await self._app.get_network_info()
                
                result.update({
                    "status": "connected",
                    "version": str(version_info),
                    "network": str(network_info),
                    "device_count": len(self._app.devices),
                })
                
                return result
            except Exception as e:
                logger.error(f"Error getting ZigBee status: {e}")
                result["status"] = "error"
                result["message"] = str(e)
                return result
        
        # Try to connect
        try:
            success = await self.connect()
            if success:
                version_info = await self._app.version()
                network_info = await self._app.get_network_info()
                
                result.update({
                    "status": "connected",
                    "version": str(version_info),
                    "network": str(network_info),
                    "device_count": len(self._app.devices),
                })
            else:
                result["message"] = "Failed to connect to ZigBee dongle"
            
            return result
        except Exception as e:
            logger.error(f"Error testing ZigBee connection: {e}")
            result["status"] = "error"
            result["message"] = str(e)
            return result

# Create a singleton instance
zigbee_service = ZigbeeService()