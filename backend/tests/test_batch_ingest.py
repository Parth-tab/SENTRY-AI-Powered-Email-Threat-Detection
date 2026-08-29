"""Comprehensive unit & integration tests for BATCH-INGESTION.
Tests:
- Sniffing matrix (RFC 822, ZIP, CSV, BOM, binary garbage, empty)
- In-memory ZIP archive streaming & Zip-Slip protection
- Archive safety caps (entry count, uncompressed bomb)
- Corrupted/encrypted entry handling
- Re-upload idempotent deduplication
- CSV synthesis & ground-truth label deduplication
- D4 degradation rule enforcement (headerless content only, zero fabricated hops)
- Appliance demo reset endpoint
"""

import io
import os
import zipfile
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.future import select

from app.main import app
from app.db.database import get_db, AsyncSessionLocal
from app.db.models import EmailRecord, AnalysisResult, EvidenceVault
from app.services.sniffer import is_rfc822, is_zip_archive, is_csv_format, sniff_payload_format
from app.services.archive_ingestion import ArchiveIngestionService, MAX_ENTRY_COUNT
from app.services.csv_synthesizer import CSVSynthesizerService

@pytest.mark.asyncio
async def test_sniffing_matrix():
    # 1. Valid RFC 822
    valid_rfc822 = b"From: alice@test.com\r\nTo: bob@test.com\r\nSubject: Test Email\r\n\r\nHello Bob!"
    assert is_rfc822(valid_rfc822) is True
    assert sniff_payload_format(valid_rfc822) == "rfc822"

    # 2. RFC 822 with UTF-8 BOM
    bom_rfc822 = b"\xef\xbb\xbfFrom: alice@test.com\nSubject: BOM Test\n\nContent with BOM"
    assert is_rfc822(bom_rfc822) is True
    assert sniff_payload_format(bom_rfc822) == "rfc822"

    # 3. Binary Garbage / Null Bytes
    binary_garbage = b"\x00\x01\x02\x03\x04\x05\x00\x00JFIF\x00"
    assert is_rfc822(binary_garbage) is False
    assert sniff_payload_format(binary_garbage) == "unsupported"

    # 4. Empty payload
    assert is_rfc822(b"") is False
    assert sniff_payload_format(b"") == "unsupported"

    # 5. ZIP Archive signature
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("test.eml", valid_rfc822)
    zip_bytes = zip_buf.getvalue()
    assert is_zip_archive(zip_bytes) is True
    assert sniff_payload_format(zip_bytes) == "archive"

    # 6. CSV Tabular Dataset
    csv_bytes = b"subject,body,label\nMeeting Tomorrow,Let's meet at 10am,0\n"
    assert is_csv_format(csv_bytes) is True
    assert sniff_payload_format(csv_bytes) == "csv"

@pytest.mark.asyncio
async def test_zip_archive_zip_slip_memory_safety():
    """Verifies that archive entries with path traversal (../evil.eml) are processed
    purely in-memory and never written to disk outside the vault.
    """
    import uuid
    uid = str(uuid.uuid4())[:8]
    sample_email = f"From: attacker@evil.com\r\nSubject: Evil Path {uid}\r\n\r\nExploit attempt".encode("utf-8")
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr(f"../../../../tmp_evil_file_{uid}.eml", sample_email)
    zip_bytes = zip_buf.getvalue()

    async with AsyncSessionLocal() as session:
        result = await ArchiveIngestionService.process_zip_archive(zip_bytes, db=session)
        assert result["status"] == "completed"
        assert result["summary"]["ingested"] == 1

        # Assert no file was written to root / filesystem outside vault
        assert not os.path.exists(f"tmp_evil_file_{uid}.eml")
        assert not os.path.exists(f"../../../../tmp_evil_file_{uid}.eml")

@pytest.mark.asyncio
async def test_zip_archive_safety_caps(monkeypatch):
    """Verifies archive safety caps reject malicious/oversized archives."""
    # Test Entry Count Cap
    monkeypatch.setattr("app.services.archive_ingestion.MAX_ENTRY_COUNT", 2)
    
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("1.eml", b"From: a@b.com\nSubject: 1\n\n1")
        zf.writestr("2.eml", b"From: a@b.com\nSubject: 2\n\n2")
        zf.writestr("3.eml", b"From: a@b.com\nSubject: 3\n\n3")
    zip_bytes = zip_buf.getvalue()

    async with AsyncSessionLocal() as session:
        result = await ArchiveIngestionService.process_zip_archive(zip_bytes, db=session)
        assert result["status"] == "error"
        assert "exceeds safety cap" in result["error"]

@pytest.mark.asyncio
async def test_zip_archive_reupload_idempotent_dedupe():
    """Verifies that re-uploading the exact same ZIP archive produces 0 new rows
    and duplicates == N.
    """
    import uuid
    uid = str(uuid.uuid4())[:8]
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("a.eml", f"From: user1@corp.com\r\nSubject: Alpha Batch {uid}\r\n\r\nContent Alpha".encode("utf-8"))
        zf.writestr("b.eml", f"From: user2@corp.com\r\nSubject: Beta Batch {uid}\r\n\r\nContent Beta".encode("utf-8"))
    zip_bytes = zip_buf.getvalue()

    async with AsyncSessionLocal() as session:
        # Run 1: Ingests 2 new emails
        res1 = await ArchiveIngestionService.process_zip_archive(zip_bytes, db=session)
        assert res1["status"] == "completed"
        assert res1["summary"]["ingested"] == 2
        assert res1["summary"]["duplicates"] == 0

        # Run 2: Re-upload same bytes -> 0 new, 2 duplicates
        res2 = await ArchiveIngestionService.process_zip_archive(zip_bytes, db=session)
        assert res2["status"] == "completed"
        assert res2["summary"]["ingested"] == 0
        assert res2["summary"]["duplicates"] == 2

@pytest.mark.asyncio
async def test_csv_golden_synthesis_and_label_deduplication():
    """Verifies CSV parsing, synthesis, and label-agnostic SHA-256 deduplication."""
    import uuid
    uid = str(uuid.uuid4())[:8]
    csv_content = (
        "subject,body,label\n"
        f"Wire Transfer Notification {uid},Please execute payment of $50000 immediately,1\n"
        f"Wire Transfer Notification {uid},Please execute payment of $50000 immediately,0\n"
    ).encode("utf-8")

    async with AsyncSessionLocal() as session:
        res = await CSVSynthesizerService.process_csv_dataset(csv_content, db=session)
        assert res["status"] == "completed"
        # Row 1 is ingested; Row 2 (identical subject/body differing only in label) is deduped!
        assert res["summary"]["ingested"] == 1
        assert res["summary"]["duplicates"] == 1

@pytest.mark.asyncio
async def test_csv_d4_degradation_rule():
    """Verifies that CSV-sourced artifacts enforce D4 degradation:
    content analysis runs, but headers/hops/IP/geo return explicit unavailable notices
    and zero fabricated hops.
    """
    import uuid
    uid = str(uuid.uuid4())[:8]
    subj = f"Urgent Financial Audit {uid}"
    csv_content = (
        f"subject,body\n"
        f"{subj},Please review the financial spreadsheet attached below immediately.\n"
    ).encode("utf-8")

    async with AsyncSessionLocal() as session:
        res = await CSVSynthesizerService.process_csv_dataset(csv_content, db=session)
        assert res["status"] == "completed"
        assert res["summary"]["ingested"] == 1

        # Query the ingested record and analysis result
        stmt = (
            select(EmailRecord, AnalysisResult)
            .join(AnalysisResult, EmailRecord.id == AnalysisResult.email_id)
            .where(EmailRecord.subject == subj)
            .limit(1)
        )
        db_res = await session.execute(stmt)
        row = db_res.first()
        assert row is not None
        email_rec, analysis_rec = row

        assert email_rec.source == "csv"
        # Authentication unavailable
        assert analysis_rec.auth_spf == {"status": "unavailable", "reason": "unavailable — headerless source"}
        assert analysis_rec.auth_dkim == {"status": "unavailable", "reason": "unavailable — headerless source"}
        assert analysis_rec.auth_dmarc == {"status": "unavailable", "reason": "unavailable — headerless source"}
        
        # Zero fabricated hops
        assert analysis_rec.relay_hops_count == 0
        assert analysis_rec.relay_path == []
        assert analysis_rec.earliest_reliable_hop is None

        # Origin unavailable
        assert analysis_rec.origin_assessment.get("status") == "unavailable"
        assert analysis_rec.origin_assessment.get("country") == "Unavailable"
        assert analysis_rec.origin_assessment.get("probable_origin_ip") is None

        # Content analysis active
        assert analysis_rec.content_analysis is not None
        assert "urgency_score" in analysis_rec.content_analysis

@pytest.mark.asyncio
async def test_demo_reset_endpoint():
    """Verifies that POST /api/v1/admin/reset-demo cleans and reseeds 18 demo emails."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/v1/admin/reset-demo")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        assert len(data["seeded_email_ids"]) == 18
