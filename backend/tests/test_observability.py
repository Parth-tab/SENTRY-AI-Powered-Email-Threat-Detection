import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.metrics import record_email_processed, get_prometheus_metrics

@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Record a test metric
        record_email_processed("unit_test", "CRITICAL", "phishing", 0.045)
        
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        
        content = response.text
        assert "sentry_emails_ingested_total" in content
        assert "sentry_threat_classifications_total" in content
        assert "sentry_pipeline_duration_seconds" in content
        assert "sentry_active_websocket_connections" in content

@pytest.mark.asyncio
async def test_deep_health_check_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health/deep")
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data
        
        subsystems = data["subsystems"]
        assert subsystems["database"]["status"] == "healthy"
        assert subsystems["evidence_vault"]["status"] == "healthy"
        assert subsystems["ml_engine"]["status"] == "healthy"
        assert subsystems["threat_intel_cache"]["status"] == "healthy"

@pytest.mark.asyncio
async def test_correlation_id_header_propagation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        custom_corr_id = "CORR-TEST-998811"
        response = await client.get("/health", headers={"X-Correlation-ID": custom_corr_id})
        assert response.status_code == 200
        assert response.headers.get("x-correlation-id") == custom_corr_id

@pytest.mark.asyncio
async def test_correlation_id_auto_generation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        corr_id = response.headers.get("x-correlation-id")
        assert corr_id is not None
        assert len(corr_id) >= 16


@pytest.mark.asyncio
async def test_structured_log_file_rotation_and_format():
    import logging
    from logging.handlers import RotatingFileHandler
    from pathlib import Path
    from app.config import settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        custom_corr = "CORR-ROTATION-TEST-12345"
        resp = await client.get("/health", headers={"X-Correlation-ID": custom_corr})
        assert resp.status_code == 200

    # Verify RotatingFileHandler presence and configuration
    sentry_logger = logging.getLogger("sentry")
    rotating_handlers = [h for h in sentry_logger.handlers if isinstance(h, RotatingFileHandler)]
    assert len(rotating_handlers) >= 1, "RotatingFileHandler not attached to sentry logger"
    
    rfh = rotating_handlers[0]
    assert rfh.maxBytes == 10 * 1024 * 1024  # 10MB limit
    assert rfh.backupCount == 5              # 5 backup generations

    # Verify log output file written
    log_file = Path(settings.LOGS_DIR) / "app.log"
    assert log_file.exists(), f"Expected log file {log_file} does not exist"
    log_content = log_file.read_text(encoding="utf-8", errors="replace")
    assert "CORR-ROTATION-TEST-12345" in log_content
    assert "GET /health -> 200" in log_content
