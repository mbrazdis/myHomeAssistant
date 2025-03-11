# app/api/models/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class DeviceBase(BaseModel):
    name: str
    device_id: str
    shelly_id: str

class DeviceIDs(BaseModel):
    device_ids: List[str]

class BrightnessPayload(BaseModel):
    brightness: int

class ColorPayload(BaseModel):
    red: int
    green: int
    blue: int
    gain: int = 100
    device_ids: Optional[List[str]] = None

class DevicePayload(BaseModel):
    name: str
    device_id: str
    shelly_id: str