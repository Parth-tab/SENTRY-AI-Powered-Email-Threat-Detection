#!/usr/bin/env python3
"""SENTRY Hot Backup Tool (D6 / GAP-010).

Creates an atomic, consistent hot snapshot of the SQLite database
and RFC 3227 Evidence Vault into a signed, checksummed archive.

Usage:
  python tools/backup_vault.py [--output backups/my_backup.tar.gz] [--db backend/sentry.db] [--vault evidence_vault]
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.backup import BackupService


def main():
    parser = argparse.ArgumentParser(description="SENTRY Hot Backup Tool")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output archive path (.tar.gz)")
    parser.add_argument("--db", type=Path, default=None, help="Source SQLite database path")
    parser.add_argument("--vault", type=Path, default=None, help="Source Evidence Vault directory")
    args = parser.parse_args()

    print("[*] Initiating SENTRY evidentiary hot snapshot...")
    try:
        report = BackupService.create_snapshot(
            db_path=args.db,
            vault_dir=args.vault,
            output_archive=args.output
        )
        print("\n[+] SNAPSHOT GENERATED SUCCESSFULLY:")
        print(f"    Archive Path:     {report['archive_path']}")
        print(f"    Archive SHA-256:  {report['archive_sha256']}")
        print(f"    Database SHA-256: {report['database_sha256']}")
        print(f"    Email Records:    {report['total_email_records']}")
        print(f"    Evidence Chains:  {report['total_evidence_records']}")
        print(f"    Vault Files:      {report['total_vault_files']}")
        print(f"    Timestamp (UTC):  {report['created_at']}")
        return 0
    except Exception as e:
        print(f"\n[!] SNAPSHOT CREATION FAILED: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
