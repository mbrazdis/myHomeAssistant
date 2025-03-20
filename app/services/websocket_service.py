from fastapi import WebSocket
from typing import List, Dict, Any
import logging
import asyncio
from app.services.device_state_machine import DeviceStateMachine

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self, state_machine: DeviceStateMachine):
        self.active_connections: List[WebSocket] = []
        self.broadcast_task = None
        self.state_machine = state_machine

    async def connect(self, websocket: WebSocket):
        """Connect a new client and add them to the list of active connections"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")
        
        if not self.broadcast_task:
            self.broadcast_task = asyncio.create_task(self.broadcast_device_status())

    def disconnect(self, websocket: WebSocket):
        """Disconnect a client and remove them from the list of active connections"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
        
        # Stop the broadcast task if no clients are connected
        if not self.active_connections and self.broadcast_task:
            self.broadcast_task.cancel()
            self.broadcast_task = None

    async def broadcast_device_status(self):
        """Broadcast device status to all connected clients every second"""
        while True:
            try:
                # Obține statusurile tuturor dispozitivelor
                statuses = await self.state_machine.get_all_devices()
                logger.info(f"Broadcasting statuses to {len(self.active_connections)} clients")

                # Pregătește mesajul
                message = {
                    "type": "device_status",
                    "data": statuses
                }
                
                # Trimite mesajul către toți clienții conectați
                for connection in self.active_connections:
                    if connection.client_state == "CONNECTED":  # Verifică dacă conexiunea este activă
                        try:
                            await connection.send_json(message)
                        except Exception as e:
                            logger.error(f"Error sending WebSocket message: {e}")
                    else:
                        logger.warning("Skipping disconnected client")
                
                # Așteaptă 1 secundă înainte de următoarea transmisie
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("Broadcast task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in broadcast_device_status: {e}")