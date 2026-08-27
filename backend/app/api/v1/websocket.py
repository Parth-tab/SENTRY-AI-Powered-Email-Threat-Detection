from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.alerting import alert_manager

router = APIRouter(prefix="", tags=["WebSocket"])

@router.websocket("/dashboard/live")
async def live_dashboard_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time telemetry, threat alerts, and live email stream.
    """
    await alert_manager.connect(websocket)
    try:
        # Send initial confirmation message
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "message": "SENTRY Real-Time Threat Stream Active (Subscribed to Telemetry)"
        })
        while True:
            # Keep-alive ping/pong listener
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        alert_manager.disconnect(websocket)
    except Exception:
        alert_manager.disconnect(websocket)
