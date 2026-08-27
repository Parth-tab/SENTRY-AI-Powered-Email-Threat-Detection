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
