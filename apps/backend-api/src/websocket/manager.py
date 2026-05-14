import asyncio
import json
import logging
from typing import Dict, Any
from broadcaster import Broadcast
from fastapi import WebSocket, WebSocketDisconnect
from src.core.config import settings

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Enterprise WebSocket Manager backed by Redis Pub/Sub (via Broadcaster).
    Allows horizontal scaling of API nodes while broadcasting Celery worker events
    to the correct client connected to any node.
    """
    def __init__(self):
        self.broadcast = Broadcast(settings.REDIS_URL)
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client {client_id} connected.")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected.")

    async def subscribe_to_room(self, websocket: WebSocket, room_name: str):
        """
        Subscribes the websocket to a specific Redis channel (room).
        """
        async with self.broadcast.subscribe(channel=room_name) as subscriber:
            try:
                async for event in subscriber:
                    await websocket.send_text(event.message)
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected from room {room_name}")

    async def broadcast_to_room(self, room_name: str, message: Dict[str, Any]):
        """
        Publishes a message to a Redis channel. 
        Can be called from Celery workers or API nodes.
        """
        payload = json.dumps(message)
        await self.broadcast.publish(channel=room_name, message=payload)

manager = ConnectionManager()
