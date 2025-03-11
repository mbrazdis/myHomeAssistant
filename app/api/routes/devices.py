# app/api/routes/devices.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging

from app.api.models.schemas import DeviceIDs
from app.integration.registry import device_registry
from app.core.devices_manager import load_devices, update_device_status

# Import device-specific API routers
from app.integration.producers.shelly.ShellyDuoRGBW.api import router as shelly_duorgbw_router

router = APIRouter()
logger = logging.getLogger(__name__)

# Include the device-specific routers
router.include_router(shelly_duorgbw_router, prefix="/shelly/duorgbw")

@router.get("/")
def get_all_devices():
    """Get all devices (legacy method)"""
    # You can choose to either:
    # 1. Return devices from the registry (recommended for new code)
    devices_from_registry = [
        {
            "device_id": device.device_id,
            "manufacturer": device.manufacturer,
            "device_type": device.device_type,
            **device.get_status()
        }
        for device in device_registry.get_all_devices()
    ]
    
    # 2. Or keep using the old method for backward compatibility
    devices_from_json = load_devices()
    
    # Return either the new or old format based on your needs
    return devices_from_json  # or devices_from_registry

@router.get("/{device_id}")
def get_device(device_id: str):
    """Get a single device by ID (legacy method)"""
    # Try to get from registry first (new approach)
    device_from_registry = device_registry.get_device(device_id)
    if device_from_registry:
        return {
            "device_id": device_from_registry.device_id,
            "manufacturer": device_from_registry.manufacturer,
            "device_type": device_from_registry.device_type,
            **device_from_registry.get_status()
        }
    
    # Fall back to old method if not found in registry
    devices = load_devices()
    device = next((d for d in devices if d["device_id"] == device_id or d["shelly_id"] == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.get("/status")
async def get_all_devices_status():
    """Get all devices with their current status"""
    # Get devices from registry
    devices = device_registry.get_all_devices()
    registry_devices = []
    for device in devices:
        status = device.get_status()
        registry_devices.append({
            "device_id": device.device_id,
            "manufacturer": device.manufacturer,
            "device_type": device.device_type,
            **status
        })
    
    # If no devices in registry, try loading from JSON
    if not registry_devices:
        from app.core.devices_manager import load_devices
        registry_devices = load_devices()
    
    return registry_devices

