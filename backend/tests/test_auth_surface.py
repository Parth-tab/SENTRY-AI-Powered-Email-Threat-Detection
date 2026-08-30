import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import settings

VALID_TOKEN = settings.SENTRY_API_TOKEN
FORGED_TOKEN = "forged_malicious_token_xyz_999"

WRITABLE_ENDPOINTS = [
    ("POST", "/api/v1/emails/upload", {"files": {"file": ("test.eml", b"Subject: test\r\n\r\nbody", "message/rfc822")}}),
    ("POST", "/api/v1/emails/raw", {"content": "Subject: test\r\n\r\nbody", "headers": {"Content-Type": "text/plain"}}),
    ("POST", "/api/v1/emails/batch/archive", {"files": {"file": ("test.zip", b"dummy_zip_content", "application/zip")}}),
    ("POST", "/api/v1/emails/batch/csv", {"files": {"file": ("test.csv", b"subject,sender\ntest,test@test.com", "text/csv")}}),
    ("POST", "/api/v1/samples/seed", {}),
    ("POST", "/api/v1/admin/reset-demo", {"headers": {"X-Sentry-Admin": settings.ADMIN_TOKEN}}),
    ("POST", "/api/v1/evidence/verify/nonexistent-id", {}),
]

@pytest.mark.asyncio
@pytest.mark.parametrize("method,endpoint,kwargs", WRITABLE_ENDPOINTS)
async def test_writable_routes_reject_missing_token_401(method, endpoint, kwargs):
    """Assert that every writable endpoint returns HTTP 401 when Authorization header is absent."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        req_kwargs = kwargs.copy()
        # Ensure no auth header is passed
        headers = req_kwargs.pop("headers", {}).copy()
        headers.pop("Authorization", None)
        
        if method == "POST":
            res = await client.post(endpoint, headers=headers, **req_kwargs)
        elif method == "DELETE":
            res = await client.delete(endpoint, headers=headers, **req_kwargs)
            
        assert res.status_code == 401, f"Expected 401 on unauthenticated {method} {endpoint}, got {res.status_code}"
        data = res.json()
        assert "UNAUTHORIZED" in str(data)

@pytest.mark.asyncio
@pytest.mark.parametrize("method,endpoint,kwargs", WRITABLE_ENDPOINTS)
async def test_writable_routes_reject_forged_token_401(method, endpoint, kwargs):
    """Assert that every writable endpoint returns HTTP 401 when a forged/invalid Bearer token is passed."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        req_kwargs = kwargs.copy()
        headers = req_kwargs.pop("headers", {}).copy()
        headers["Authorization"] = f"Bearer {FORGED_TOKEN}"
        
        if method == "POST":
            res = await client.post(endpoint, headers=headers, **req_kwargs)
        elif method == "DELETE":
            res = await client.delete(endpoint, headers=headers, **req_kwargs)
            
        assert res.status_code == 401, f"Expected 401 on forged token {method} {endpoint}, got {res.status_code}"

@pytest.mark.asyncio
async def test_valid_token_allows_raw_ingest():
    """Assert that a valid Bearer token successfully authorizes ingest."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        raw_eml = (
            "From: analyst@soc.internal\r\n"
            "To: target@internal\r\n"
            "Subject: AUTH-TEST-VALID\r\n"
            "Date: Sun, 30 Aug 2026 01:00:00 +0000\r\n\r\n"
            "Test body content"
        )
        res = await client.post(
            "/api/v1/emails/raw",
            content=raw_eml,
            headers={
                "Content-Type": "text/plain",
                "Authorization": f"Bearer {VALID_TOKEN}"
            }
        )
        assert res.status_code in (200, 201), f"Expected 200/201, got {res.status_code}: {res.text}"

@pytest.mark.asyncio
async def test_read_routes_accessible_unauthenticated():
    """Verify that read telemetry and public diagnostic endpoints remain unauthenticated."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        
        res = await client.get("/api/v1/dashboard/stats")
        assert res.status_code == 200
        
        res = await client.get("/api/v1/emails?limit=5")
        assert res.status_code == 200
        
        res = await client.get("/api/v1/campaigns")
        assert res.status_code == 200
