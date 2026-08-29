import json
from typing import List, Dict, Any
from fastapi import WebSocket

class AlertManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        try:
            from app.services.metrics import ACTIVE_WEBSOCKET_CONNECTIONS
            ACTIVE_WEBSOCKET_CONNECTIONS.set(len(self.active_connections))
        except Exception:
            pass

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            try:
                from app.services.metrics import ACTIVE_WEBSOCKET_CONNECTIONS
                ACTIVE_WEBSOCKET_CONNECTIONS.set(len(self.active_connections))
            except Exception:
                pass

    async def broadcast_alert(self, alert_data: Dict[str, Any]):
        """Broadcasts a high-priority threat alert to all active WebSocket clients."""
        payload = json.dumps({
            "type": "NEW_ALERT",
            "data": alert_data
        })
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

    async def broadcast_email_analyzed(self, email_data: Dict[str, Any], analysis_data: Dict[str, Any]):
        """Broadcasts completed email analysis for live dashboard updates."""
        payload = json.dumps({
            "type": "EMAIL_ANALYZED",
            "data": {
                "email": email_data,
                "analysis": analysis_data
            }
        })
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                disconnected.append(connection)
        
    async def broadcast_batch_progress(self, progress_data: Dict[str, Any]):
        """Broadcasts throttled batch ingestion progress to all active WebSocket clients."""
        payload = json.dumps({
            "type": "BATCH_PROGRESS",
            "data": progress_data
        })
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

alert_manager = AlertManager()
