"""Archive ingestion service for SENTRY.
Handles in-memory streaming of ZIP archives with corpus-grade denial-of-service caps,
RFC 822 content verification, and throttled batch telemetry.
"""

import io
import time
import zipfile
import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import EmailRecord
from app.services.alerting import alert_manager
from app.services.sniffer import is_rfc822, is_zip_archive

MAX_COMPRESSED_SIZE = 262_144_000      # 250 MB
MAX_UNCOMPRESSED_TOTAL = 524_288_000   # 500 MB
MAX_ENTRY_COUNT = 10_000               # 10,000 entries
MAX_SINGLE_ENTRY_SIZE = 26_214_400     # 25 MB

class ArchiveIngestionService:
    @staticmethod
    async def process_zip_archive(
        archive_bytes: bytes,
        db: AsyncSession,
        source_format: str = "archive"
    ) -> Dict[str, Any]:
        """Ingests all valid RFC 822 email entries within a ZIP archive in-memory."""
        start_time = time.time()
        compressed_size = len(archive_bytes)

        if compressed_size > MAX_COMPRESSED_SIZE:
            return {
                "status": "error",
                "error": f"Compressed archive size ({compressed_size / 1_048_576:.1f}MB) exceeds limit of 250MB."
            }

        try:
            zf = zipfile.ZipFile(io.BytesIO(archive_bytes))
        except Exception as exc:
            return {
                "status": "error",
                "error": f"Corrupted or invalid ZIP archive: {str(exc)}"
            }

        entries = zf.infolist()
        if len(entries) > MAX_ENTRY_COUNT:
            return {
                "status": "error",
                "error": f"Archive entry count ({len(entries)}) exceeds safety cap of {MAX_ENTRY_COUNT} entries."
            }

        uncompressed_total = sum(e.file_size for e in entries)
        if uncompressed_total > MAX_UNCOMPRESSED_TOTAL:
            return {
                "status": "error",
                "error": f"Total uncompressed size ({uncompressed_total / 1_048_576:.1f}MB) exceeds safety cap of 500MB."
            }

        ingested_count = 0
        duplicate_count = 0
        skipped_count = 0
        errors: List[Dict[str, str]] = []
        warnings: List[str] = []

        from app.api.v1.emails import process_and_store_email

        total_files = len(entries)

        for idx, entry in enumerate(entries):
            # 1. Skip directories and macOS / hidden metadata
            base_name = entry.filename.replace("\\", "/").split("/")[-1]
            if entry.is_dir() or entry.filename.endswith("/") or "__MACOSX" in entry.filename or (base_name.startswith(".") and base_name not in (".", "..")):
                skipped_count += 1
                continue

            # 2. Check per-entry size cap
            if entry.file_size > MAX_SINGLE_ENTRY_SIZE:
                errors.append({
                    "entry": entry.filename,
                    "reason": f"Entry exceeds 25MB cap ({entry.file_size / 1_048_576:.1f}MB)"
                })
                continue

            # 3. Handle nested archives
            if entry.filename.lower().endswith(".zip"):
                skipped_count += 1
                warnings.append(f"Skipped nested archive: {entry.filename}")
                continue

            # 4. Decompress entry in-memory
            try:
                entry_bytes = zf.read(entry)
            except Exception as exc:
                errors.append({
                    "entry": entry.filename,
                    "reason": f"Decompression failed: {str(exc)}"
                })
                continue

            if not entry_bytes:
                skipped_count += 1
                continue

            # Check if entry is a nested zip by signature
            if is_zip_archive(entry_bytes):
                skipped_count += 1
                warnings.append(f"Skipped nested archive by signature: {entry.filename}")
                continue

            # 5. Check if it is RFC 822 format
            if not is_rfc822(entry_bytes):
                # Non-RFC822 plain text or binary
                skipped_count += 1
                warnings.append(f"Skipped non-RFC822 entry: {entry.filename}")
                continue

            # 6. Check if SHA-256 already exists in DB before processing
            import hashlib
            entry_sha = hashlib.sha256(entry_bytes).hexdigest()
            stmt = select(EmailRecord.id).where(EmailRecord.sha256_hash == entry_sha).limit(1)
            res = await db.execute(stmt)
            already_exists = res.scalar_one_or_none() is not None

            try:
                await process_and_store_email(entry_bytes, source=source_format, db=db)
                if already_exists:
                    duplicate_count += 1
                else:
                    ingested_count += 1
            except Exception as exc:
                errors.append({
                    "entry": entry.filename,
                    "reason": f"Ingestion error: {str(exc)}"
                })

            # Yield to event loop and broadcast progress every 100 entries
            if (idx + 1) % 100 == 0 or (idx + 1) == total_files:
                await asyncio.sleep(0)
                await alert_manager.broadcast_batch_progress({
                    "type": "archive",
                    "processed": idx + 1,
                    "total": total_files,
                    "ingested": ingested_count,
                    "duplicates": duplicate_count,
                    "skipped": skipped_count,
                    "errors": len(errors)
                })

        elapsed = round(time.time() - start_time, 3)

        return {
            "status": "completed",
            "source_format": source_format,
            "summary": {
                "total_entries": total_files,
                "ingested": ingested_count,
                "duplicates": duplicate_count,
                "skipped": skipped_count,
                "errors_count": len(errors),
                "errors": errors[:50],  # cap returned errors
                "warnings": warnings[:50],
                "elapsed_seconds": elapsed
            }
        }
