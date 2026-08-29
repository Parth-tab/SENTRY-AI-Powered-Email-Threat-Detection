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

    # Test Uncompressed Size Cap
    monkeypatch.setattr("app.services.archive_ingestion.MAX_ENTRY_COUNT", 1000)
    monkeypatch.setattr("app.services.archive_ingestion.MAX_UNCOMPRESSED_TOTAL", 50)
    zip_buf2 = io.BytesIO()
    with zipfile.ZipFile(zip_buf2, "w") as zf:
        zf.writestr("big.eml", b"A" * 100)
    async with AsyncSessionLocal() as session:
        result2 = await ArchiveIngestionService.process_zip_archive(zip_buf2.getvalue(), db=session)
        assert result2["status"] == "error"
        assert "exceeds safety cap" in result2["error"]

@pytest.mark.asyncio
async def test_zip_archive_encrypted_or_corrupt_entry_graceful_handling(monkeypatch):
    """Verifies that an encrypted/corrupt ZIP entry generates a per-entry error while
    allowing other valid entries in the archive to be ingested safely without crashing.
    """
    import uuid
    uid = str(uuid.uuid4())[:8]
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        zf.writestr("valid.eml", f"From: valid@corp.com\r\nSubject: Valid Email {uid}\r\n\r\nContent".encode("utf-8"))
        zf.writestr("corrupted.eml", b"Some data")
    
    zip_bytes = zip_buf.getvalue()
    
    # Mock zf.read to simulate RuntimeError on corrupted/encrypted entry
    orig_read = zipfile.ZipFile.read
    def mock_read(self, name, pwd=None):
        entry_name = name.filename if isinstance(name, zipfile.ZipInfo) else name
        if entry_name == "corrupted.eml":
            raise RuntimeError("File is encrypted, password required")
        return orig_read(self, name, pwd=pwd)
    
    monkeypatch.setattr(zipfile.ZipFile, "read", mock_read)

    async with AsyncSessionLocal() as session:
        result = await ArchiveIngestionService.process_zip_archive(zip_bytes, db=session)
        assert result["status"] == "completed"
        # Valid entry ingested
        assert result["summary"]["ingested"] == 1
        # Corrupted entry captured as per-entry error
        assert result["summary"]["errors_count"] == 1
        assert any("Decompression failed" in e.get("reason", "") for e in result["summary"]["errors"])

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

@pytest.mark.asyncio
async def test_csv_synthesizer_preserves_raw_bytes_verbatim():
    """B-1: Verifies that CSV synthesizer preserves raw field bytes VERBATIM without
    import-time mutation or prepending apostrophes to '-', '=', '+', '@' characters.
    """
    subject_raw = "=CMD|'dir'!A0"
    body_raw = "-This is a minus-prefixed body\r\n=calc\r\n+addition\r\n@formula"
    
    synth_bytes = CSVSynthesizerService.synthesize_rfc822_bytes(
        subject=subject_raw,
        body=body_raw,
        sender="+attacker@evil.com",
        recipient="-victim@corp.com"
    )
    
    # Assert exact byte preservation (unmodified)
    assert b"Subject: =CMD|'dir'!A0" in synth_bytes
    assert b"From: +attacker@evil.com" in synth_bytes
    assert b"To: -victim@corp.com" in synth_bytes
    assert b"-This is a minus-prefixed body\r\n=calc\r\n+addition\r\n@formula" in synth_bytes
    # Assert NO evidence-corrupting prepended apostrophe
    assert b"Subject: '=CMD" not in synth_bytes
    assert b"From: '+attacker" not in synth_bytes

    # Ingest and verify stored record has exact unmodified bytes
    import uuid
    uid = str(uuid.uuid4())[:8]
    csv_data = f'subject,body\n"-Financial Warning {uid}","-Please review immediately: urgency payment required."'.encode("utf-8")
    
    async with AsyncSessionLocal() as session:
        res = await CSVSynthesizerService.process_csv_dataset(csv_data, db=session)
        assert res["status"] == "completed"
        assert res["summary"]["ingested"] == 1
        
        stmt = select(EmailRecord, AnalysisResult).join(AnalysisResult, EmailRecord.id == AnalysisResult.email_id).where(EmailRecord.subject == f"-Financial Warning {uid}").limit(1)
        row = (await session.execute(stmt)).first()
        assert row is not None
        rec, analysis = row
        assert rec.subject == f"-Financial Warning {uid}"
        assert "-Please review immediately" in rec.raw_content
        # Content analysis works accurately on verbatim text
        assert analysis.content_analysis["urgency_score"] > 0

def test_csv_export_writer_owasp_formula_neutralization():
    """B-1: Verifies that CSV export writers apply write-time OWASP formula neutralization
    to prevent spreadsheet execution while preserving database evidence fidelity.
    """
    from app.services.reporting import ReportingService
    
    # Unit checks on sanitize_csv_cell
    assert ReportingService.sanitize_csv_cell("=cmd|'/C calc'!A0") == "'=cmd|'/C calc'!A0"
    assert ReportingService.sanitize_csv_cell("-2+3+cmd|' /C calc'!A0") == "'-2+3+cmd|' /C calc'!A0"
    assert ReportingService.sanitize_csv_cell("+1+1") == "'+1+1"
    assert ReportingService.sanitize_csv_cell("@SUM(1+1)") == "'@SUM(1+1)"
    assert ReportingService.sanitize_csv_cell("\t=cmd") == "'\t=cmd"
    assert ReportingService.sanitize_csv_cell("\r=cmd") == "'\r=cmd"
    assert ReportingService.sanitize_csv_cell("Normal Subject") == "Normal Subject"
    assert ReportingService.sanitize_csv_cell(None) == ""
    assert ReportingService.sanitize_csv_cell(123) == "123"

    # Export generation check
    test_records = [
        {
            "id": "=EVIL-ID",
            "subject": "-Financial Fraud Campaign",
            "sender": "+attacker@malicious.com",
            "sender_domain": "@evil.com",
            "threat_level": "CRITICAL",
            "threat_score": 0.99,
            "origin_ip": "1.2.3.4"
        }
    ]
    csv_out = ReportingService.generate_ioc_csv_report(test_records)
    assert "'=EVIL-ID" in csv_out
    assert "'-Financial Fraud Campaign" in csv_out
    assert "'+attacker@malicious.com" in csv_out
    assert "'@evil.com" in csv_out
    assert "CRITICAL" in csv_out

