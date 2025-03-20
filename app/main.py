# app/main.py
import os
import logging
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.api.routes.devices import router as devices_router
from app.integration.producers.shelly.ShellyDuoRGBW.api import router as shelly_duorgbw_router

# Import services
from app.services.mqtt_service import init_mqtt_client, stop_mqtt_client, MQTTService

from app.integration.registry import device_registry
from app.services.command_queue_service import command_queue
from app.services.websocket_service import ConnectionManager
# Import settings
from app.core.config import settings

from app.services.device_state_machine import DeviceStateMachine

# Creează instanța state machine
state_machine = DeviceStateMachine()

# Creează instanța managerului de conexiuni WebSocket
manager = ConnectionManager(state_machine)

# Creează instanța serviciului MQTT
mqtt_service = MQTTService(state_machine)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for controlling smart home devices",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(devices_router, prefix="/devices", tags=["devices"])
# Include the DuoRGBW router with both prefixes
app.include_router(shelly_duorgbw_router, prefix="/shelly/duorgbw", tags=["devices"])
app.include_router(shelly_duorgbw_router, prefix="/shelly/colorbulb", tags=["devices"])

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time device updates"""
    await manager.connect(websocket)
    try:
        # Trimite starea inițială a dispozitivelor
        devices = device_registry.get_all_devices()
        registry_devices = []

        if not devices:
            # Dacă nu există dispozitive în registru, încearcă să le încarci din JSON
            from app.core.devices_manager import load_devices
            json_devices = load_devices()
            await websocket.send_json({"type": "initial_devices", "data": json_devices})
        else:
            # Trimite dispozitivele din registru
            for device in devices:
                status = device.get_status()
                registry_devices.append({
                    "device_id": device.device_id,
                    "manufacturer": device.manufacturer,
                    "device_type": device.device_type,
                    **status
                })
            await websocket.send_json({"type": "initial_devices", "data": registry_devices})

        # Menține conexiunea deschisă și procesează mesajele primite
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "request_status":
                    # Clientul solicită actualizarea statusului dispozitivelor
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
                    await websocket.send_json({"type": "devices_status", "data": registry_devices})
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
                await websocket.send_text(f"Invalid JSON: {data}")
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                break
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Unexpected WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/")
def root():
    """Root endpoint that returns basic API information"""
    return {
        "api_name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "documentation": "/docs",
        "status": "operational"
    }

@app.on_event("startup")
async def print_routes():
    """Print all registered routes on startup for debugging."""
    print("\nREGISTERED ROUTES:")
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            print(f"{', '.join(route.methods)} {route.path}")
    print("\n")

@app.on_event("startup")
async def startup_event():
    """Initialize services when the application starts"""
    logger.info("Starting up the application")
    
    # Initialize the MQTT client
    init_mqtt_client()
    
    # Set command delay (optional, default 400ms)
    command_queue.set_command_delay(0.4)
    
    # Print registered routes for debugging
    print("\n=== REGISTERED ROUTES ===")
    for route in app.routes:
        if hasattr(route, "path"):
            methods = getattr(route, "methods", ["--"])
            print(f"{', '.join(methods)} {route.path}")
    print("========================\n")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services when the application shuts down"""
    logger.info("Shutting down the application")
    
    # Stop the command queue service
    await command_queue.shutdown()
    
    # Stop the MQTT client
    stop_mqtt_client()