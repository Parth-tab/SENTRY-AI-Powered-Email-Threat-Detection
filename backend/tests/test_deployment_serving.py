import pytest
from httpx import AsyncClient, ASGITransport
from pathlib import Path
from app.config import settings
from app.main import app

@pytest.mark.asyncio
async def test_deployment_api_precedence():
    """Ensure API endpoints take routing precedence over mounted static files."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"

        metrics_res = await client.get("/metrics")
        assert metrics_res.status_code == 200
        assert "sentry_" in metrics_res.text

@pytest.mark.asyncio
async def test_single_origin_static_mount_serving():
    """Ensure static SPA index.html is served when static mount is active."""
    dist_dir = Path(settings.FRONTEND_DIST_DIR)
    if not (dist_dir / "index.html").exists():
        pytest.skip("frontend/dist not built")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/")
        assert res.status_code == 200
        # If mounted as static SPA, response content type contains html and has SENTRY title
        if "text/html" in res.headers.get("content-type", ""):
            assert "SENTRY" in res.text
            assert "<div id=\"root\">" in res.text

@pytest.mark.asyncio
async def test_deployment_mode_configuration():
    """Verify settings properties for deployment mode."""
    assert hasattr(settings, "SERVE_STATIC")
    assert hasattr(settings, "BUILD_MODE")
    assert hasattr(settings, "FRONTEND_DIST_DIR")
    assert hasattr(settings, "SENTRY_API_TOKEN")
