import io
import pytest

@pytest.mark.asyncio
async def test_upload_eml_file_endpoint_success(client):
    """Verifies multipart .eml upload endpoint (ING-001 regression protection)."""
    raw_eml = b"""From: alerts@security-service.com
To: user@enterprise.local
Subject: SEC-TEST: RFC 5322 Ingestion Verification
Date: Sat, 29 Aug 2026 12:00:00 +0000
Received: from [198.51.100.25] by mx.enterprise.local with ESMTP; Sat, 29 Aug 2026 12:00:00 +0000
Content-Type: text/plain; charset=utf-8

Please review this security notification.
"""
    files = {
        "file": ("verification_test.eml", io.BytesIO(raw_eml), "message/rfc822")
    }
    res = await client.post("/api/v1/emails/upload", files=files)
    assert res.status_code == 201, f"Expected 201 Created, got {res.status_code}: {res.text}"
    
    data = res.json()
    assert data["subject"] == "SEC-TEST: RFC 5322 Ingestion Verification"
    assert data["sender"] == "alerts@security-service.com"
    assert "analysis" in data and data["analysis"] is not None
    assert "threat_level" in data["analysis"]
    assert "overall_threat_score" in data["analysis"]
    assert "evidence" in data and data["evidence"] is not None
    assert data["evidence"]["chain_of_custody_id"].startswith("COC-")
    assert data["evidence"]["is_sealed"] is True

@pytest.mark.asyncio
async def test_submit_raw_rfc5322_endpoint_success(client):
    """Verifies raw RFC 5322 text ingestion endpoint (ING-001 regression protection)."""
    raw_text = """From: "System Administrator" <admin@corp-secure.net>
To: ops@company.com
Subject: URGENT: Infrastructure Health Check
Date: Sat, 29 Aug 2026 14:00:00 +0000
Received: from [203.0.113.50] by mx.company.com with SMTP; Sat, 29 Aug 2026 14:00:00 +0000

Mandatory password reset required immediately.
"""
    res = await client.post(
        "/api/v1/emails/raw",
        content=raw_text,
        headers={"Content-Type": "text/plain"}
    )
    assert res.status_code == 201, f"Expected 201 Created, got {res.status_code}: {res.text}"
    
    data = res.json()
    assert data["subject"] == "URGENT: Infrastructure Health Check"
    assert data["sender_domain"] == "corp-secure.net"
    assert data["analysis"]["threat_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL", "CLEAN"]
    assert data["evidence"]["sha256_hash"] is not None

@pytest.mark.asyncio
async def test_upload_invalid_file_extension_rejected(client):
    """Verifies unsupported file extensions are rejected with 400 Bad Request."""
    files = {
        "file": ("malware.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")
    }
    res = await client.post("/api/v1/emails/upload", files=files)
    assert res.status_code == 400
    assert "Unsupported file type" in res.json().get("detail", "")
