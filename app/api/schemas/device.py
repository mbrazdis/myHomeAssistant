from pydantic import BaseModel
from typing import List, Optional

class Device(BaseModel):
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

class MultipleColorPayload(BaseModel):
    device_ids: List[str]
    red: int
    green: int
    blue: int
    gain: int = 100

class DeviceStatus(BaseModel):
    device_id: str
    name: Optional[str] = None
    ison: bool = False
    brightness: Optional[int] = None
    temp: Optional[int] = None
    red: Optional[int] = None
    green: Optional[int] = None
    blue: Optional[int] = None
    gain: Optional[int] = None
    power: Optional[float] = None
    energy: Optional[float] = None
    online: bool = False