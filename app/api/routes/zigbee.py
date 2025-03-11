# app/api/routes/zigbee.py
from fastapi import APIRouter, HTTPException
import logging
import glob
import os

from app.services.zigbee_service import zigbee_service

router = APIRouter(prefix="/zigbee", tags=["zigbee"])
logger = logging.getLogger(__name__)

@router.get("/test")
async def test_zigbee_connection():
    """Test the connection to the Zigbee dongle"""
    result = await zigbee_service.test_connection()
    return result

@router.get("/scan")
async def scan_zigbee_devices():
    """Scan for Zigbee devices"""
    if not zigbee_service.is_connected():
        connected = await zigbee_service.connect()
        if not connected:
            raise HTTPException(status_code=500, detail="Failed to connect to ZigBee dongle")
    
    devices = await zigbee_service.scan_devices()
    return {"devices": devices, "count": len(devices)}

@router.post("/dongle_path")
async def set_zigbee_dongle_path(path: str):
    """Set the path to the Zigbee dongle"""
    zigbee_service.set_dongle_path(path)
    return {"message": f"ZigBee dongle path set to: {path}"}

@router.get("/list_ports")
async def list_serial_ports():
    """List all available serial ports"""
    try:
        # Get all serial ports on macOS
        tty_ports = glob.glob("/dev/tty.*")
        cu_ports = glob.glob("/dev/cu.*")
        all_ports = tty_ports + cu_ports
        
        # Get details about each port
        port_details = []
        for port in all_ports:
            details = {
                "path": port,
                "exists": os.path.exists(port),
                "is_symlink": os.path.islink(port),
            }
            if os.path.islink(port):
                details["link_target"] = os.readlink(port)
            port_details.append(details)
        
        return {
            "tty_ports": tty_ports,
            "cu_ports": cu_ports,
            "port_details": port_details
        }
    except Exception as e:
        logger.error(f"Error listing serial ports: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing serial ports: {str(e)}")