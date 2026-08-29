import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import pytest

from app.services.backup import BackupService
from app.services.reporting import ReportingService

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent


def create_test_db_and_vault(db_path: Path, vault_dir: Path):
    """Creates an initialized SQLite DB and Evidence Vault with valid RFC 3227 chains."""
    vault_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE email_records (
        id VARCHAR(36) PRIMARY KEY,
        message_id VARCHAR(255),
        subject VARCHAR(500),
        sender VARCHAR(255),
        sender_domain VARCHAR(255),
        recipient VARCHAR(255),
        date DATETIME,
        raw_content TEXT,
        raw_content_path VARCHAR(500),
        raw_headers JSON,
        sha256_hash VARCHAR(64),
        source VARCHAR(50),
        ingested_at DATETIME,
        status VARCHAR(50)
    )
    """)

    cursor.execute("""
    CREATE TABLE evidence_vault (
        id VARCHAR(36) PRIMARY KEY,
        email_id VARCHAR(36) UNIQUE,
        sha256_hash VARCHAR(64),
        stored_path VARCHAR(500),
        chain_of_custody_id VARCHAR(50),
        chain_entries JSON,
        last_entry_hash VARCHAR(64),
        is_sealed BOOLEAN,
        created_at DATETIME
    )
    """)

    # Populate 3 test emails with evidence
    for i in range(1, 4):
        email_id = f"test-email-id-00{i}"
        raw_payload = f"From: attacker{i}@evil.com\nSubject: Phishing Probe {i}\n\nMalicious lure {i}".encode("utf-8")
        raw_sha256 = BackupService.compute_file_sha256(Path(tempfile.gettempdir())) if False else "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        
        # Write actual payload to vault
        vault_file = vault_dir / f"payload_{i}.eml"
        vault_file.write_bytes(raw_payload)
        file_sha256 = BackupService.compute_file_sha256(vault_file)

        # Generate valid RFC 3227 chain
        coc_id, entries, h0 = ReportingService.initialize_chain_of_custody(email_id, file_sha256, source="unit_test")
        entries, h1 = ReportingService.append_chain_entry(
            entries,
            action="AUTOMATED_FORENSIC_ANALYSIS",
            actor="SENTRY_CLASSIFIER_V1",
            details="Extracted 47 features, classified as CRITICAL (0.98)"
        )

        cursor.execute("""
        INSERT INTO email_records (id, message_id, subject, sender, sha256_hash, ingested_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (email_id, f"<msg-{i}@test.com>", f"Phishing Probe {i}", f"attacker{i}@evil.com", file_sha256, datetime.now(timezone.utc).isoformat()))

        cursor.execute("""
        INSERT INTO evidence_vault (id, email_id, sha256_hash, stored_path, chain_of_custody_id, chain_entries, last_entry_hash, is_sealed, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (f"ev-{i}", email_id, file_sha256, str(vault_file), coc_id, json.dumps(entries), h1, True, datetime.now(timezone.utc).isoformat()))

    conn.commit()
    conn.close()


def test_backup_restore_verifies_chain_integrity():
    """
    D6 / GAP-010 Core Soul Test:
    1. Seed DB and Vault with valid RFC 3227 cryptographic chains.
    2. Execute Backup snapshot.
    3. Corrupt/wipe active DB and Vault.
    4. Restore from snapshot.
    5. Assert RESTORE_VERIFIED_PASS with 100% intact hash chains.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "live_sentry.db"
        vault_dir = tmp_path / "live_vault"
        archive_path = tmp_path / "backups" / "test_snapshot.tar.gz"

        create_test_db_and_vault(db_path, vault_dir)

        # 1. Take Snapshot
        backup_result = BackupService.create_snapshot(
            db_path=db_path,
            vault_dir=vault_dir,
            output_archive=archive_path
        )
        assert backup_result["status"] == "SNAPSHOT_SUCCESS"
        assert backup_result["total_email_records"] == 3
        assert backup_result["total_evidence_records"] == 3
        assert backup_result["total_vault_files"] == 3
        assert archive_path.exists()

        # 2. Corrupt / Wipe Live State
        conn = sqlite3.connect(str(db_path))
        conn.execute("DELETE FROM evidence_vault")
        conn.commit()
        conn.close()
        for f in vault_dir.glob("*.eml"):
            f.unlink()

        # Confirm live state is corrupted
        conn = sqlite3.connect(str(db_path))
        assert conn.execute("SELECT count(*) FROM evidence_vault").fetchone()[0] == 0
        conn.close()
        assert len(list(vault_dir.glob("*.eml"))) == 0

        # 3. Restore from Snapshot
        restore_result = BackupService.restore_snapshot(
            snapshot_archive=archive_path,
            target_db_path=db_path,
            target_vault_dir=vault_dir
        )

        # 4. Verify Cryptographic Receipt
        assert restore_result["status"] == "RESTORE_VERIFIED_PASS"
        assert restore_result["total_chains_verified"] == 3
        assert restore_result["chains_failed"] == 0
        assert restore_result["restored_vault_files"] == 3

        # 5. Direct verification of restored chains in database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT chain_entries, last_entry_hash FROM evidence_vault")
        rows = cursor.fetchall()
        assert len(rows) == 3
        for raw_entries, last_entry_hash in rows:
            entries = json.loads(raw_entries)
            is_valid, msg = ReportingService.verify_chain_integrity(entries)
            assert is_valid is True, f"Hash chain failed verification: {msg}"
            assert entries[-1]["entry_hash"] == last_entry_hash
        conn.close()


def test_restore_tampered_payload_fails_safely():
    """
    Verifies that if a payload file inside a backup is tampered with,
    the restore process detects hash mismatch and rejects the restore.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "live_sentry.db"
        vault_dir = tmp_path / "live_vault"
        archive_path = tmp_path / "test_snapshot.tar.gz"

        create_test_db_and_vault(db_path, vault_dir)

        # Take valid snapshot
        BackupService.create_snapshot(
            db_path=db_path,
            vault_dir=vault_dir,
            output_archive=archive_path
        )

        # Tamper with archive: unpack, modify sentry.db or payload, repack
        tamper_dir = tmp_path / "tamper_scratch"
        tamper_dir.mkdir()
        import tarfile
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=tamper_dir)

        # Tamper with DB
        db_tampered = tamper_dir / "sentry.db"
        conn = sqlite3.connect(str(db_tampered))
        conn.execute("UPDATE evidence_vault SET last_entry_hash = 'tampered_bad_hash'")
        conn.commit()
        conn.close()

        # Re-pack with tampered DB but unchanged manifest.json
        archive_tampered = tmp_path / "tampered_snapshot.tar.gz"
        with tarfile.open(archive_tampered, "w:gz") as tar:
            tar.add(db_tampered, arcname="sentry.db")
            tar.add(tamper_dir / "evidence_vault", arcname="evidence_vault")
            tar.add(tamper_dir / "manifest.json", arcname="manifest.json")

        # Attempt restore -> Must raise ValueError for DB hash mismatch
        with pytest.raises(ValueError, match="Database hash mismatch"):
            BackupService.restore_snapshot(
                snapshot_archive=archive_tampered,
                target_db_path=db_path,
                target_vault_dir=vault_dir
            )


def test_backup_and_restore_cli_tools():
    """Verifies that tools/backup_vault.py and tools/restore_vault.py execute cleanly from CLI."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "cli_sentry.db"
        vault_dir = tmp_path / "cli_vault"
        archive_path = tmp_path / "cli_backup.tar.gz"

        create_test_db_and_vault(db_path, vault_dir)

        # CLI Backup
        res_backup = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "backup_vault.py"),
             "--output", str(archive_path), "--db", str(db_path), "--vault", str(vault_dir)],
            capture_output=True,
            text=True
        )
        assert res_backup.returncode == 0, f"Backup CLI failed: {res_backup.stderr}"
        assert "SNAPSHOT GENERATED SUCCESSFULLY" in res_backup.stdout
        assert archive_path.exists()

        # CLI Restore
        res_restore = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "restore_vault.py"),
             "--snapshot", str(archive_path), "--db", str(db_path), "--vault", str(vault_dir)],
            capture_output=True,
            text=True
        )
        assert res_restore.returncode == 0, f"Restore CLI failed: {res_restore.stderr}"
        assert "RESTORE VERIFICATION PASSED (PASS)" in res_restore.stdout
        assert "Verified Hash Chains:    3 (0 failures)" in res_restore.stdout


def test_restore_post_backup_probe_isolation():
    """
    P4-2: Verifies that records ingested AFTER a backup was created do NOT
    leak or persist into the restored state (Point-in-Time Isolation).
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / "live_sentry.db"
        vault_dir = tmp_path / "live_vault"
        archive_path = tmp_path / "backups" / "point_in_time.tar.gz"

        create_test_db_and_vault(db_path, vault_dir)

        # 1. Take Snapshot with 3 baseline emails
        backup_result = BackupService.create_snapshot(
            db_path=db_path,
            vault_dir=vault_dir,
            output_archive=archive_path
        )
        assert backup_result["status"] == "SNAPSHOT_SUCCESS"
        assert backup_result["total_email_records"] == 3

        # 2. Ingest a 4th post-backup probe email
        post_backup_email_id = "post-backup-probe-004"
        post_payload = b"From: attacker4@evil.com\nSubject: Post-Backup Injection\n\nLure"
        post_vault_file = vault_dir / "payload_4_post_backup.eml"
        post_vault_file.write_bytes(post_payload)
        post_sha256 = BackupService.compute_file_sha256(post_vault_file)

        coc_id4, entries4, h4 = ReportingService.initialize_chain_of_custody(post_backup_email_id, post_sha256, source="post_backup_test")

        conn = sqlite3.connect(str(db_path))
        conn.execute("""
        INSERT INTO email_records (id, message_id, subject, sender, sha256_hash, ingested_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (post_backup_email_id, "<msg-4@post.com>", "Post-Backup Injection", "attacker4@evil.com", post_sha256, datetime.now(timezone.utc).isoformat()))

        conn.execute("""
        INSERT INTO evidence_vault (id, email_id, sha256_hash, stored_path, chain_of_custody_id, chain_entries, last_entry_hash, is_sealed, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("ev-4", post_backup_email_id, post_sha256, str(post_vault_file), coc_id4, json.dumps(entries4), h4, True, datetime.now(timezone.utc).isoformat()))
        conn.commit()
        conn.close()

        # Confirm 4th email exists prior to restore
        conn = sqlite3.connect(str(db_path))
        assert conn.execute("SELECT count(*) FROM email_records").fetchone()[0] == 4
        conn.close()

        # 3. Execute Restore from Snapshot
        restore_result = BackupService.restore_snapshot(
            snapshot_archive=archive_path,
            target_db_path=db_path,
            target_vault_dir=vault_dir
        )
        assert restore_result["status"] == "RESTORE_VERIFIED_PASS"
        assert restore_result["total_chains_verified"] == 3

        # 4. Assert Post-Backup Email is completely absent in restored state
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM email_records WHERE id = ?", (post_backup_email_id,))
        assert cursor.fetchone()[0] == 0, "Post-backup email leaked into restored database state!"
        cursor.execute("SELECT count(*) FROM email_records")
        assert cursor.fetchone()[0] == 3
        conn.close()
