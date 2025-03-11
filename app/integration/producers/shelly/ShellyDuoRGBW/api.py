from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging

from app.services.mqtt_service import mqtt_client  
from app.integration.registry import device_registry
from app.integration.producers.shelly.ShellyDuoRGBW.schemas import (
    ColorBulbStatus, 
    BrightnessPayload, 
    ColorPayload,
    TemperaturePayload,
    DeviceIDs,
    BulkColorPayload,
    BulkTemperaturePayload,
    BulkBrightnessPayload,
    BulkWhitePayload,
    WhitePayload
)
from app.core.devices_manager import update_device_status
from app.integration.producers.shelly.ShellyDuoRGBW.device import (
    getStatus, 
    turn_off, 
    turn_on, 
    load_devices, 
    set_color,
    set_color_multiple,
    set_white,    
    set_white_multiple,
    set_temperature,
    set_temperature_multiple,
    set_brightness,
    set_brightness_multiple)

router = APIRouter(tags=["shelly", "duorgbw"])
logger = logging.getLogger(__name__)

async def get_bulb_duo(device_id: str) -> str:
    """Get device ID if it exists"""
    devices = load_devices()
    device = next((d for d in devices if d["device_id"] == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device_id

@router.get("/{device_id}/status")
async def get_bulb_duo_status(device_id: str):

    status = await getStatus(device_id)
    if not status:
        raise HTTPException(status_code=404, detail="Device status not found")
    return status

@router.get("/status")
async def get_all_devices_status():
    """Get all Shelly DuoRGBW devices with their status"""
    devices = device_registry.get_all_devices()
    shelly_devices = [
        {
            "device_id": device.device_id,
            "manufacturer": device.manufacturer,
            "device_type": device.device_type,
            **device.get_status()
        }
        for device in devices
        if device.manufacturer == "shelly" and device.device_type in ["duorgbw", "colorbulb"]
    ]
    
    # If no devices in registry, try loading from JSON
    if not shelly_devices:
        devices = load_devices()
        shelly_devices = [
            device for device in devices
            if device.get("manufacturer", "shelly") == "shelly"
        ]
    
    return shelly_devices

@router.post("/{device_id}/turn_on")
async def turn_on_bulb_duo(device_id: str):
    """Turn on a device"""
    try:
        # Just make sure device exists
        _ = await get_bulb_duo(device_id)
        
        # Use the function directly with error handling
        success = await turn_on(device_id)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to turn on device {device_id}")
            
        return {"message": f"Device {device_id} turned on successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error turning on device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{device_id}/turn_off")
async def turn_off_bulb_duo(device_id: str):
    """Turn off a device"""
    try:
        # Just make sure device exists
        _ = await get_bulb_duo(device_id)
        
        # Use the function directly with error handling
        success = await turn_off(device_id)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to turn off device {device_id}")
            
        return {"message": f"Device {device_id} turned off successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error turning off device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/on_multiple")
async def turn_on_multiple_bulb_duo(payload: DeviceIDs):
    """Turn on multiple devices at once"""
    try:
        results = []
        success_count = 0
        failure_count = 0
        
        # Process each device ID
        for device_id in payload.device_ids:
            try:
                # Verify device exists
                try:
                    _ = await get_bulb_duo(device_id)
                except HTTPException:
                    results.append({
                        "device_id": device_id,
                        "success": False,
                        "error": "Device not found"
                    })
                    failure_count += 1
                    continue
                
                # Turn on the device
                device_success = await turn_on(device_id)
                
                if device_success:
                    results.append({
                        "device_id": device_id,
                        "success": True
                    })
                    success_count += 1
                else:
                    results.append({
                        "device_id": device_id,
                        "success": False,
                        "error": "Failed to turn on device"
                    })
                    failure_count += 1
            
            except Exception as e:
                logger.error(f"Error processing device {device_id}: {e}")
                results.append({
                    "device_id": device_id,
                    "success": False,
                    "error": str(e)
                })
                failure_count += 1
        
        # Return a summary with individual results
        return {
            "message": f"Processed {len(payload.device_ids)} devices with {success_count} successful and {failure_count} failed operations",
            "success_count": success_count,
            "failure_count": failure_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in turn_on_multiple_bulb_duo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/off_multiple")
async def turn_off_multiple_bulb_duo(payload: DeviceIDs):
    """Turn off multiple devices at once"""
    try:
        results = []
        success_count = 0
        failure_count = 0
        
        # Process each device ID
        for device_id in payload.device_ids:
            try:
                # Verify device exists
                try:
                    _ = await get_bulb_duo(device_id)
                except HTTPException:
                    results.append({
                        "device_id": device_id,
                        "success": False,
                        "error": "Device not found"
                    })
                    failure_count += 1
                    continue
                
                # Turn off the device
                device_success = await turn_off(device_id)
                
                if device_success:
                    results.append({
                        "device_id": device_id,
                        "success": True
                    })
                    success_count += 1
                else:
                    results.append({
                        "device_id": device_id,
                        "success": False,
                        "error": "Failed to turn off device"
                    })
                    failure_count += 1
            
            except Exception as e:
                logger.error(f"Error processing device {device_id}: {e}")
                results.append({
                    "device_id": device_id,
                    "success": False,
                    "error": str(e)
                })
                failure_count += 1
        
        # Return a summary with individual results
        return {
            "message": f"Processed {len(payload.device_ids)} devices with {success_count} successful and {failure_count} failed operations",
            "success_count": success_count,
            "failure_count": failure_count,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in turn_off_multiple_bulb_duo: {e}")
        raise HTTPException(status_code=500, detail=str(e))   

@router.post("/{device_id}/color")
async def set_device_color(device_id: str, payload: ColorPayload):
    """Set the color of a device"""
    try:
        # Just make sure device exists
        _ = await get_bulb_duo(device_id)
        
        # Use the imported set_color function from device.py
        success = await set_color(
            device_id, 
            payload.red, 
            payload.green, 
            payload.blue, 
            payload.gain,
            payload.white
        )
            
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to set color for device {device_id}")
            
        return {"message": f"Color set for device {device_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting color for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/{device_id}/white")
async def set_device_white(device_id: str, payload: WhitePayload):
    """Set the white level of a device"""
    try:
        # Just make sure device exists
        _ = await get_bulb_duo(device_id)
        
        # Use the imported set_white function from device.py
        success = await set_white(
            device_id, 
            payload.white,
            payload.gain,
            payload.red,
            payload.green,
            payload.blue,  
            payload.brightness,
            payload.temp
        )
            
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to set white level for device {device_id}")
            
        return {"message": f"White level set for device {device_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting white level for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/white_multiple")
async def set_white_multiple_bulb_duo(payload: BulkWhitePayload):
    """Set the white level for multiple devices at once"""
    try:
        # Extract white values from payload
        white = payload.white
        gain = payload.gain
        red = payload.red
        green = payload.green
        blue = payload.blue
        brightness = payload.brightness
        temp = payload.temp
        
        # Validate that devices exist
        valid_device_ids = []
        for device_id in payload.device_ids:
            try:
                _ = await get_bulb_duo(device_id)
                valid_device_ids.append(device_id)
            except HTTPException:
                # Skip invalid devices
                continue
        
        if not valid_device_ids:
            raise HTTPException(status_code=404, detail="No valid devices found")
        
        # Use the bulk operation
        results_dict = await set_white_multiple(valid_device_ids, white, gain, red, green, blue, brightness, temp)
            
        # Format results
        results = [
            {
                "device_id": device_id,
                "success": success,
                "white" if success else "error": {
                    "white": white,
                    "gain": gain,
                    "red": red,
                    "green": green,
                    "blue": blue,
                    "brightness": brightness,
                    "temp": temp
                } if success else "Failed to set white level"
            }
            for device_id, success in results_dict.items()
        ]
            
        success_count = sum(1 for r in results if r.get("success", False))
        failure_count = len(results) - success_count
        
        # Return formatted response
        white_info = f"White:{white}, Gain:{gain}"
        return {
            "message": f"Set white level {white_info} for {len(valid_device_ids)} devices with {success_count} successful and {failure_count} failed operations",
            "success_count": success_count,
            "failure_count": failure_count,
            "white": {
                "white": white,
                "gain": gain,
                "red": red,
                "green": green,
                "blue": blue,
                "brightness": brightness,
                "temp": temp
            },
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in set_white_multiple_bulb_duo: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/{device_id}/temperature")
async def set_device_temperature(device_id: str, payload: TemperaturePayload):
    """Set the color temperature of a device"""
    try:
        # Just make sure device exists
        _ = await get_bulb_duo(device_id)
        
        # Use the imported set_temperature function from device.py
        success = await set_temperature(
            device_id, 
            payload.temperature
        )
            
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to set temperature for device {device_id}")
            
        return {"message": f"Temperature set to {payload.temperature}K for device {device_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting temperature for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/temperature_multiple")
async def set_temperature_multiple_bulb_duo(payload: BulkTemperaturePayload):
    """Set the color temperature for multiple devices at once"""
    try:
        # Extract temperature value from payload
        temperature = payload.temperature
        
        # Validate that devices exist
        valid_device_ids = []
        for device_id in payload.device_ids:
            try:
                _ = await get_bulb_duo(device_id)
                valid_device_ids.append(device_id)
            except HTTPException:
                # Skip invalid devices
                continue
        
        if not valid_device_ids:
            raise HTTPException(status_code=404, detail="No valid devices found")
        
        # Use the bulk operation
        results_dict = await set_temperature_multiple(valid_device_ids, temperature)
            
        # Format results
        results = [
            {
                "device_id": device_id,
                "success": success,
                "temperature" if success else "error": temperature if success else "Failed to set temperature"
            }
            for device_id, success in results_dict.items()
        ]
            
        success_count = sum(1 for r in results if r.get("success", False))
        failure_count = len(results) - success_count
        
        # Return formatted response
        return {
            "message": f"Set temperature to {temperature}K for {len(valid_device_ids)} devices with {success_count} successful and {failure_count} failed operations",
            "success_count": success_count,
            "failure_count": failure_count,
            "temperature": temperature,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in set_temperature_multiple_bulb_duo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{device_id}/brightness")
async def set_device_brightness(device_id: str, payload: BrightnessPayload):
    """Set the brightness of a device"""
    try:
        # Just make sure device exists
        _ = await get_bulb_duo(device_id)
        
        # Use the imported set_brightness function from device.py
        success = await set_brightness(
            device_id, 
            payload.brightness
        )
            
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to set brightness for device {device_id}")
            
        return {"message": f"Brightness set to {payload.brightness}% for device {device_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting brightness for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/brightness_multiple")
async def set_brightness_multiple_bulb_duo(payload: BulkBrightnessPayload):
    """Set the brightness for multiple devices at once"""
    try:
        # Extract brightness value from payload
        brightness = payload.brightness
        
        # Validate that devices exist
        valid_device_ids = []
        for device_id in payload.device_ids:
            try:
                _ = await get_bulb_duo(device_id)
                valid_device_ids.append(device_id)
            except HTTPException:
                # Skip invalid devices
                continue
        
        if not valid_device_ids:
            raise HTTPException(status_code=404, detail="No valid devices found")
        
        # Use the bulk operation
        results_dict = await set_brightness_multiple(valid_device_ids, brightness)
            
        # Format results
        results = [
            {
                "device_id": device_id,
                "success": success,
                "brightness" if success else "error": brightness if success else "Failed to set brightness"
            }
            for device_id, success in results_dict.items()
        ]
            
        success_count = sum(1 for r in results if r.get("success", False))
        failure_count = len(results) - success_count
        
        # Return formatted response
        return {
            "message": f"Set brightness to {brightness}% for {len(valid_device_ids)} devices with {success_count} successful and {failure_count} failed operations",
            "success_count": success_count,
            "failure_count": failure_count,
            "brightness": brightness,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in set_brightness_multiple_bulb_duo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/color_multiple")
async def set_color_multiple_bulb_duo(payload: BulkColorPayload):
    """Set the same color for multiple devices at once"""
    try:
        # Extract color values
        red = payload.red
        green = payload.green
        blue = payload.blue
        gain = payload.gain
        white = payload.white
        
        # Validate that devices exist
        valid_device_ids = []
        for device_id in payload.device_ids:
            try:
                _ = await get_bulb_duo(device_id)
                valid_device_ids.append(device_id)
            except HTTPException:
                # Skip invalid devices
                continue
        
        if not valid_device_ids:
            raise HTTPException(status_code=404, detail="No valid devices found")
        
        # Use the bulk operation if available
        if 'set_color_multiple' in globals():
            results_dict = await set_color_multiple(valid_device_ids, red, green, blue, gain, white)
            
            # Format results
            results = [
                {
                    "device_id": device_id,
                    "success": success,
                    "color" if success else "error": {
                        "red": red,
                        "green": green,
                        "blue": blue,
                        "gain": gain,
                        "white": white
                    } if success else "Failed to set color"
                }
                for device_id, success in results_dict.items()
            ]
            
            success_count = sum(1 for r in results if r["success"])
            failure_count = len(results) - success_count
        else:
            # Fall back to individual operations
            results = []
            success_count = 0
            failure_count = 0
            
            for device_id in valid_device_ids:
                try:
                    success = await set_color(device_id, red, green, blue, gain, white)
                    
                    if success:
                        results.append({
                            "device_id": device_id,
                            "success": True,
                            "color": {
                                "red": red,
                                "green": green,
                                "blue": blue,
                                "gain": gain,
                                "white": white
                            }
                        })
                        success_count += 1
                    else:
                        results.append({
                            "device_id": device_id,
                            "success": False,
                            "error": "Failed to set color"
                        })
                        failure_count += 1
                except Exception as e:
                    logger.error(f"Error setting color for device {device_id}: {e}")
                    results.append({
                        "device_id": device_id,
                        "success": False,
                        "error": str(e)
                    })
                    failure_count += 1
        
        # Return formatted response
        color_info = f"R:{red}, G:{green}, B:{blue}, Gain:{gain}"
        return {
            "message": f"Set color {color_info} for {len(valid_device_ids)} devices with {success_count} successful and {failure_count} failed operations",
            "success_count": success_count,
            "failure_count": failure_count,
            "color": {
                "red": red,
                "green": green,
                "blue": blue,
                "gain": gain,
                "white": white 
            },
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error in set_color_multiple_bulb_duo: {e}")
        raise HTTPException(status_code=500, detail=str(e))