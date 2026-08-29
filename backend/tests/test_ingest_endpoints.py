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

@pytest.mark.asyncio
async def test_ingest_sha256_deduplication_upload_and_raw(client):
    """ING-002: Ingesting identical bytes returns the existing record; asserts single row and stable id."""
    raw_eml = b"""From: dedupe-test@domain.com
To: recipient@domain.com
Subject: DEDUPE-TEST: Idempotent Ingestion Check
Date: Sat, 29 Aug 2026 15:00:00 +0000
Message-ID: <dedupe-test-001@domain.com>
Received: from [198.51.100.99] by mx.domain.com with ESMTP; Sat, 29 Aug 2026 15:00:00 +0000
Content-Type: text/plain; charset=utf-8

Testing multi-vector deduplication across general ingest endpoints.
"""
    # 1. First upload
    files_1 = {"file": ("dedupe_sample.eml", io.BytesIO(raw_eml), "message/rfc822")}
    res1 = await client.post("/api/v1/emails/upload", files=files_1)
    assert res1.status_code in [200, 201]
    data1 = res1.json()
    email_id_1 = data1["id"]
    sha256_1 = data1["sha256_hash"]

    # 2. Second upload of identical bytes
    files_2 = {"file": ("dedupe_sample.eml", io.BytesIO(raw_eml), "message/rfc822")}
    res2 = await client.post("/api/v1/emails/upload", files=files_2)
    assert res2.status_code in [200, 201]
    data2 = res2.json()
    email_id_2 = data2["id"]
    sha256_2 = data2["sha256_hash"]

    # Assert stable ID and identical SHA-256
    assert email_id_2 == email_id_1, f"Expected stable ID {email_id_1}, got duplicate {email_id_2}"
    assert sha256_2 == sha256_1

    # 3. Third ingest via raw text of identical RFC 5322 payload
    raw_str = raw_eml.decode("utf-8")
    res3 = await client.post("/api/v1/emails/raw", content=raw_str, headers={"Content-Type": "text/plain"})
    assert res3.status_code in [200, 201]
    data3 = res3.json()
    assert data3["id"] == email_id_1, f"Expected stable ID {email_id_1}, got {data3['id']}"
    assert data3["sha256_hash"] == sha256_1

    # 4. Check total emails count
    res_list = await client.get("/api/v1/emails")
    assert res_list.status_code == 200
    all_emails = res_list.json()
    matching_ids = [e["id"] for e in all_emails if e["id"] == email_id_1]
    assert len(matching_ids) == 1, "Expected exactly 1 database row for deduplicated email"

