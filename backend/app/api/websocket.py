"""
KAVACHGRID 3.0 — WebSocket endpoint for real-time dashboard
Phase 5: Complete Implementation

Provides:
    - ConnectionManager: Manages active WebSocket connections
    - /ws/dashboard endpoint: Real-time push to connected dashboards
    - broadcast_update(): Callable from services/engines to push events

Event types pushed to dashboard:
    - telemetry_update: New telemetry data received
    - alert_created: New alert generated
    - risk_updated: Risk scores recalculated
    - device_status: Device online/offline change
    - localization_update: New localization result
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.utils.security import decode_access_token

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """
    Manages active WebSocket connections for real-time dashboard updates.

    Thread-safe connection tracking with broadcast support.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection and add it to the active list."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from the active list."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a JSON message to all connected clients.
        Automatically removes dead connections.
        """
        dead_connections: List[WebSocket] = []

        async with self._lock:
            connections = list(self.active_connections)

        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)

        # Cleanup dead connections
        if dead_connections:
            async with self._lock:
                for conn in dead_connections:
                    if conn in self.active_connections:
                        self.active_connections.remove(conn)

    @property
    def connection_count(self) -> int:
        """Number of active WebSocket connections."""
        return len(self.active_connections)


# Global connection manager instance
ws_manager = ConnectionManager()


async def broadcast_update(
    event_type: str,
    data: Dict[str, Any],
    timestamp: Optional[str] = None,
) -> None:
    """
    Broadcast a real-time event to all connected dashboard clients.

    Usage from anywhere in the app:
        from app.api.websocket import broadcast_update
        await broadcast_update("alert_created", {"id": "...", "severity": "high"})

    Args:
        event_type: Type of event (e.g., telemetry_update, alert_created)
        data: Event payload as a dictionary
        timestamp: Optional ISO timestamp (defaults to current UTC time)
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    message = {
        "event": event_type,
        "data": data,
        "timestamp": timestamp,
    }

    await ws_manager.broadcast(message)


@router.websocket("/ws")
@router.websocket("/ws/dashboard")
async def websocket_dashboard(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="JWT token for auth"),
):
    """
    WebSocket endpoint for real-time dashboard updates.

    Connect with: ws://localhost:8000/ws/dashboard?token=<JWT>

    Authentication is optional but recommended.
    If a token is provided, it will be validated.

    Client messages:
        - "ping"              → server replies with {"event": "pong"}
        - {"subscribe": "..."}  → subscribe to event channel (future use)
    """
    # Validate JWT if provided — must accept connection first per WS protocol
    if token:
        payload = decode_access_token(token)
        if payload is None:
            await websocket.accept()
            await websocket.close(code=4001, reason="Invalid token")
            return

    await ws_manager.connect(websocket)

    try:
        # Send welcome message
        await websocket.send_json({
            "event": "connected",
            "data": {
                "message": "Connected to KAVACHGRID 3.0 real-time feed",
                "active_connections": ws_manager.connection_count,
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Keep connection alive — listen for client messages
        while True:
            raw = await websocket.receive_text()

            # Handle text ping from client
            if raw == "ping":
                await websocket.send_json({
                    "event": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                continue

            # Handle JSON messages (subscribe, etc.)
            try:
                msg = json.loads(raw)
                if "subscribe" in msg:
                    await websocket.send_json({
                        "event": "subscribed",
                        "data": {"channel": msg["subscribe"]},
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
            except (json.JSONDecodeError, TypeError):
                pass  # Ignore malformed messages

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception:
        await ws_manager.disconnect(websocket)
