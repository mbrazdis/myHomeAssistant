import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Smart Home API"
    
    # Debug mode
    DEBUG: bool = False  # Add this line
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost",
    "http://127.0.0.1",
    "http://192.168.100.177:3000",
    "http://127.0.0.1:3000",
    "http://example.com"]
    
    # MQTT settings
    MQTT_BROKER_HOST: str = "192.168.100.177"
    MQTT_BROKER_PORT: int = 1883
    MQTT_CLIENT_ID: str = "smart-home-client"
    MQTT_KEEPALIVE: int = 60

    # Paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    DEVICES_FILE: str = os.path.join(DATA_DIR, "devices.json")
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

# Create settings instance
settings = Settings()

# Ensure data directory exists
os.makedirs(settings.DATA_DIR, exist_ok=True)