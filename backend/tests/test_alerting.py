import pytest
from unittest.mock import AsyncMock
from app.services.alerting import AlertManager, alert_manager

@pytest.mark.asyncio
async def test_alert_manager_connection_and_broadcast():
    manager = AlertManager()
    mock_ws = AsyncMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_text = AsyncMock()

    await manager.connect(mock_ws)
    assert len(manager.active_connections) == 1

    alert_payload = {
        "email_id": "test-123",
        "threat_level": "CRITICAL",
        "subject": "Phishing Attempt"
    }

    await manager.broadcast_alert(alert_payload)
    assert mock_ws.send_text.called

    manager.disconnect(mock_ws)
    assert len(manager.active_connections) == 0

@pytest.mark.asyncio
async def test_global_alert_manager_instance():
    assert alert_manager is not None
    assert isinstance(alert_manager, AlertManager)
