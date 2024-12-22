from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from devices_manager import (
    load_devices,
    save_devices,
    initialize_device,
    update_device_status,
)
from devices.mqtt_handler import (
    init_mqtt_client,
    stop_mqtt_client,
    turn_on,
    turn_off,
    set_brightness,
    set_temp,
    set_color,
    monitor_status_updates,
)
import logging
import asyncio


class Device(BaseModel):
    name: str
    device_id: str
    shelly_id: str

app = FastAPI()


origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_mqtt_client()
    asyncio.create_task(monitor_status_updates())


@app.on_event("shutdown")
def shutdown_event():
    stop_mqtt_client()

@app.post("/devices/")
def add_device(device: Device):
    devices = load_devices()
    if any(d["device_id"] == device.device_id for d in devices):
        raise HTTPException(status_code=400, detail="Device ID already exists.")

    new_device = device.dict()
    devices.append(new_device)
    save_devices(devices)
    return {"message": "Device added successfully", "device": new_device}

@app.get("/devices/")
def get_devices():
    devices = load_devices()
    if not devices:
        return {"message": "No devices found"}
    return devices

@app.put("/devices/{device_id}")
def edit_device(device_id: str, updated_device: Device):
    devices = load_devices()
    device_index = next((index for (index, d) in enumerate(devices) if d["device_id"] == device_id), None)

    if device_index is None:
        raise HTTPException(status_code=404, detail="Device not found")

    devices[device_index]["name"] = updated_device.name
    save_devices(devices)
    return {"message": f"Device {device_id} updated successfully"}

@app.delete("/devices/{device_id}")
def delete_device(device_id: str):
    devices = load_devices()
    device_to_delete = next((device for device in devices if device["device_id"] == device_id), None)

    if not device_to_delete:
        raise HTTPException(status_code=404, detail="Device not found")

    devices = [device for device in devices if device["device_id"] != device_id]
    save_devices(devices)
    return {"message": f"Device {device_id} deleted successfully"}

@app.post("/devices/{device_id}/on")
def device_on(device_id: str):
    devices = load_devices()
    device = next((d for d in devices if d["device_id"] == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    shelly_id = device["shelly_id"]
    turn_on(shelly_id)
    update_device_status(device_id, {"ison": True})

    return {"message": f"Turn on command sent to device {device_id}"}

@app.post("/devices/{device_id}/off")
def device_off(device_id: str):
    devices = load_devices()
    device = next((d for d in devices if d["device_id"] == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    shelly_id = device["shelly_id"]
    turn_off(shelly_id)
    update_device_status(device_id, {"ison": False})

    return {"message": f"Turn off command sent to device {device_id}"}
