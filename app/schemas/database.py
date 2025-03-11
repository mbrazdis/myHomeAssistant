from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import List, Optional

Base = declarative_base()


DATABASE_URL = "sqlite:///./smart_home.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    device_id = Column(String, unique=True, index=True)
    status = Column(String, default="off")

def init_db():
    Base.metadata.create_all(bind=engine)

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
