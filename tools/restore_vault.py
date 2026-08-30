#!/usr/bin/env python3
"""SENTRY Hot Restore Tool (D6 / GAP-010).

Restores a snapshot archive and executes mathematical verification
of every restored RFC 3227 hash chain.

Usage:
  python tools/restore_vault.py --snapshot backups/sentry_snapshot_20260830.tar.gz [--db backend/sentry.db] [--vault evidence_vault]
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.backup import BackupService


def main():
    parser = argparse.ArgumentParser(description="SENTRY Hot Restore Tool")
    parser.add_argument("--snapshot", "-s", type=Path, required=True, help="Snapshot archive to restore (.tar.gz)")
    parser.add_argument("--db", type=Path, default=None, help="Target SQLite database path")
    parser.add_argument("--vault", type=Path, default=None, help="Target Evidence Vault directory")
    args = parser.parse_args()

    print(f"[*] Initiating restore from snapshot: {args.snapshot}")
    try:
        report = BackupService.restore_snapshot(
            snapshot_archive=args.snapshot,
            target_db_path=args.db,
            target_vault_dir=args.vault
        )

        if report["status"] == "RESTORE_VERIFIED_PASS":
            print("\n[+] RESTORE VERIFICATION PASSED (PASS):")
            print(f"    Restored Database:       {report['restored_database']}")
            print(f"    Restored Evidence Vault: {report['restored_vault_dir']}")
            print(f"    Restored Vault Files:    {report['restored_vault_files']}")
            print(f"    Verified Hash Chains:    {report['total_chains_verified']} (0 failures)")
            print(f"    Receipt:                 {report['message']}")
            return 0
        else:
            print("\n[!] RESTORE VERIFICATION FAILED:", file=sys.stderr)
            print(f"    Chains Verified: {report.get('chains_verified', 0)}")
            print(f"    Chains Failed:   {report.get('chains_failed', 0)}")
            for err in report.get("errors", []):
                print(f"      - {err}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"\n[!] RESTORE FAILED: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
