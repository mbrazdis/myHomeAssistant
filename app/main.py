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
from app.services.mqtt_service import init_mqtt_client, mqtt_service, stop_mqtt_client
from app.services.websocket_service import manager
from app.integration.registry import device_registry
from app.services.command_queue_service import command_queue

# Import settings
from app.core.config import settings

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

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial device states
        devices = device_registry.get_all_devices()
        if not devices:
            # If no devices in registry, try loading from JSON
            from app.core.devices_manager import load_devices
            json_devices = load_devices()
            await websocket.send_json({"type": "initial_devices", "data": json_devices})
        else:
            # Send devices from registry
            registry_devices = []
            for device in devices:
                status = device.get_status()
                registry_devices.append({
                    "device_id": device.device_id,
                    "manufacturer": device.manufacturer,
                    "device_type": device.device_type,
                    **status
                })
            await websocket.send_json({"type": "initial_devices", "data": registry_devices})
        
        # Keep the connection open and process incoming messages
        while True:
            data = await websocket.receive_text()
            try:
                # Process client messages
                message = json.loads(data)
                if message.get("type") == "request_status":
                    # Client is requesting updated status
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
                await websocket.send_text(f"Message received but not JSON: {data}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
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