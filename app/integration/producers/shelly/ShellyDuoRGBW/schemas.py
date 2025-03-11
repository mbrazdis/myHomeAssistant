# app/integrations/shelly/colorbulb/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List

class ColorBulbStatus(BaseModel):
    ison: bool = False
    mode: str = "color"
    brightness: int = 100
    temp: int = 4750
    red: int = 255
    green: int = 255
    blue: int = 255
    gain: int = 100
    power: float = 0
    energy: float = 0
    online: bool = False

class BrightnessPayload(BaseModel):
    brightness: int = Field(..., ge=0, le=100)

class ColorPayload(BaseModel):
    red: int = Field(..., ge=0, le=255)
    green: int = Field(..., ge=0, le=255)
    blue: int = Field(..., ge=0, le=255)
    gain: int = Field(100, ge=0, le=100)
    white: int = 0

class BulkColorPayload(BaseModel):
    device_ids: List[str]
    red: int = Field(..., ge=0, le=255, description="Red component (0-255)")
    green: int = Field(..., ge=0, le=255, description="Green component (0-255)")
    blue: int = Field(..., ge=0, le=255, description="Blue component (0-255)")
    gain: int = Field(100, ge=0, le=100, description="Color intensity (0-100)")
    white: int = 0

class TemperaturePayload(BaseModel):
    temperature: int = Field(..., ge=2700, le=6500)

class WhitePayload(BaseModel):
    white: int = Field(..., ge=0, le=100, description="White level (0-100)")
    gain: int = 100
    red: int = 0
    green: int = 0
    blue: int = 0
    brightness: int = 100
    temp: int = 4750

class BulkWhitePayload(BaseModel):
    device_ids: List[str]
    white: int = Field(..., ge=0, le=100, description="White level (0-100)")
    gain: int = 100
    red: int = 0
    green: int = 0
    blue: int = 0
    brightness: int = 100
    temp: int = 4750

class TemperaturePayload(BaseModel):
    temp: int = Field(..., ge=2700, le=6500, description="Color temperature in Kelvin (2700-6500)")

class BulkTemperaturePayload(BaseModel):
    device_ids: List[str]
    temp: int = Field(..., ge=2700, le=6500, description="Color temperature in Kelvin (2700-6500)")

class BrightnessPayload(BaseModel):
    brightness: int = Field(..., ge=0, le=100, description="Brightness percentage (0-100)")

class BulkBrightnessPayload(BaseModel):
    device_ids: List[str]
    brightness: int = Field(..., ge=0, le=100, description="Brightness percentage (0-100)")

class DeviceIDs(BaseModel):
    device_ids: List[str]