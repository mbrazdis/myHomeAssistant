from fastapi import WebSocket
from typing import List, Dict, Any
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Connect a new client and add them to the list of active connections"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a client from the list of active connections"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Remaining connections: {len(self.active_connections)}")

    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast a generic message to all connected clients"""
        if not self.active_connections:
            return
            
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

    async def broadcast_device_status(self, device_id: str, status: Dict[str, Any]):
        """Send device status update to all connected clients"""
        if not self.active_connections:
            return
            
        # Create a standardized status message
        message = {
            "type": "device_update",
            "device_id": device_id,
            "status": status
        }
        
        # Send to all connected clients
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                # Connection might be closed, don't remove it here to avoid modifying the list during iteration

# Create a singleton instance
manager = ConnectionManager()