from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_service import manager
from app.services.device_service import device_service
from app.core.logging import logger

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial device states
        devices = device_service.get_all_devices()
        for device in devices:
            await manager.broadcast_device_status(
                device["device_id"], 
                {
                    "ison": device.get("ison", False),
                    "brightness": device.get("brightness"),
                    "temp": device.get("temp"),
                    "red": device.get("red"),
                    "green": device.get("green"),
                    "blue": device.get("blue"),
                    "gain": device.get("gain"),
                    "power": device.get("power"),
                    "energy": device.get("energy"),
                    "online": device.get("online", False)
                }
            )
        
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)