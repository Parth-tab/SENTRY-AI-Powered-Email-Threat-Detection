"""CSV dataset ingestion and RFC 822 synthesis engine for SENTRY.
Parses tabular datasets (CSV/TSV), synthesizes deterministic RFC 822 MIME byte streams,
and enforces strict D4 degradation rules (content analysis only; zero fabricated hops).
"""

import io
import csv
import time
import hashlib
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models import EmailRecord
from app.services.alerting import alert_manager

MALICIOUS_LABELS = {"1", "true", "yes", "spam", "phish", "phishing", "malicious", "threat"}
HAM_LABELS = {"0", "false", "no", "ham", "legitimate", "clean", "benign"}

def normalize_label(val: Any) -> Optional[str]:
    if val is None:
        return None
    s = str(val).strip().lower()
    if s in MALICIOUS_LABELS:
        return "malicious"
    if s in HAM_LABELS:
        return "legitimate"
    return s

class CSVSynthesizerService:
    @staticmethod
    def synthesize_rfc822_bytes(
        subject: str,
        body: str,
        sender: str = "csv-import@unknown.local",
        recipient: str = "undisclosed-recipients@local",
        date_str: str = "Thu, 01 Jan 2026 00:00:00 +0000"
    ) -> bytes:
        """Synthesizes a clean, deterministic RFC 822 MIME byte stream from tabular fields.
        Ground-truth labels are excluded from synthesized headers so rows differing
        only in label produce identical SHA-256 byte identity.
        """
        subj_clean = (subject or "[No Subject - CSV Import]").replace("\r", " ").replace("\n", " ")
        sender_clean = (sender or "csv-import@unknown.local").replace("\r", "").replace("\n", "")
        recipient_clean = (recipient or "undisclosed-recipients@local").replace("\r", "").replace("\n", "")

        # Deterministic message ID based on content
        content_hash = hashlib.sha256(f"{subj_clean}|{body}".encode("utf-8")).hexdigest()[:16]
        msg_id = f"<{content_hash}@csv-dataset.sentry>"

        headers = [
            f"From: {sender_clean}",
            f"To: {recipient_clean}",
            f"Subject: {subj_clean}",
            f"Date: {date_str}",
            f"Message-ID: {msg_id}",
            "X-SENTRY-Source: csv_dataset",
            "MIME-Version: 1.0",
            "Content-Type: text/plain; charset=utf-8"
        ]

        raw_text = "\r\n".join(headers) + "\r\n\r\n" + (body or "")
        return raw_text.encode("utf-8")

    @classmethod
    async def process_csv_dataset(
        cls,
        csv_bytes: bytes,
        db: AsyncSession,
        source_format: str = "csv"
    ) -> Dict[str, Any]:
        """Parses CSV dataset, synthesizes RFC 822 payloads, and executes forensic ingestion."""
        start_time = time.time()

        # Encoding fallback: UTF-8 -> Latin-1
        used_encoding = "utf-8"
        try:
            text = csv_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = csv_bytes.decode("latin-1")
            used_encoding = "latin-1"

        if not text.strip():
            return {
                "status": "error",
                "error": "Uploaded CSV file is empty."
            }

        # Detect delimiter
        first_line = text.splitlines()[0]
        delimiter = "\t" if "\t" in first_line and "," not in first_line else ","

        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        if not reader.fieldnames:
            return {
                "status": "error",
                "error": "CSV lacks recognizable header row."
            }

        # Normalize field names
        field_map = {f.strip().lower(): f for f in reader.fieldnames if f}
        
        # Locate body column
        body_col = next((field_map[k] for k in ["body", "text", "content", "message", "email_text", "clean_text"] if k in field_map), None)
        if not body_col:
            return {
                "status": "error",
                "error": f"CSV must contain one of 'body', 'text', 'content', 'message' columns. Found: {list(field_map.keys())}"
            }

        subject_col = next((field_map[k] for k in ["subject", "subj", "title"] if k in field_map), None)
        label_col = next((field_map[k] for k in ["label", "target", "class", "spam", "is_phishing", "category"] if k in field_map), None)
        sender_col = next((field_map[k] for k in ["sender", "from", "from_address"] if k in field_map), None)
        recipient_col = next((field_map[k] for k in ["recipient", "to", "to_address"] if k in field_map), None)
        date_col = next((field_map[k] for k in ["date", "timestamp", "sent_date"] if k in field_map), None)

        unrecognized = [k for k in field_map.keys() if k not in {
            "body", "text", "content", "message", "email_text", "clean_text",
            "subject", "subj", "title", "label", "target", "class", "spam",
            "is_phishing", "category", "sender", "from", "from_address",
            "recipient", "to", "to_address", "date", "timestamp", "sent_date"
        }]

        rows = list(reader)
        total_rows = len(rows)

        ingested_count = 0
        duplicate_count = 0
        skipped_count = 0
        errors: List[Dict[str, str]] = []
        warnings: List[str] = []

        if unrecognized:
            warnings.append(f"Ignored unrecognized columns: {', '.join(unrecognized)}")

        from app.api.v1.emails import process_and_store_email

        # Pre-load known SHA-256 hashes for O(1) deduplication
        stmt_hashes = select(EmailRecord.sha256_hash)
        res_hashes = await db.execute(stmt_hashes)
        known_hashes = set(res_hashes.scalars().all())

        for idx, row in enumerate(rows):
            body_val = row.get(body_col, "").strip()
            if not body_val:
                skipped_count += 1
                continue

            subj_val = row.get(subject_col, "[No Subject - CSV Import]") if subject_col else "[No Subject - CSV Import]"
            sender_val = row.get(sender_col, "csv-import@unknown.local") if sender_col else "csv-import@unknown.local"
            recip_val = row.get(recipient_col, "undisclosed-recipients@local") if recipient_col else "undisclosed-recipients@local"
            date_val = row.get(date_col, "Thu, 01 Jan 2026 00:00:00 +0000") if date_col else "Thu, 01 Jan 2026 00:00:00 +0000"

            synthetic_bytes = cls.synthesize_rfc822_bytes(
                subject=subj_val,
                body=body_val,
                sender=sender_val,
                recipient=recip_val,
                date_str=date_val
            )

            synthetic_sha = hashlib.sha256(synthetic_bytes).hexdigest()
            if synthetic_sha in known_hashes:
                duplicate_count += 1
                continue

            try:
                await process_and_store_email(synthetic_bytes, source=source_format, db=db)
                known_hashes.add(synthetic_sha)
                ingested_count += 1
            except Exception as exc:
                errors.append({
                    "row": str(idx + 1),
                    "reason": f"Ingestion error: {str(exc)}"
                })

            if (idx + 1) % 100 == 0 or (idx + 1) == total_rows:
                await asyncio.sleep(0)
                await alert_manager.broadcast_batch_progress({
                    "type": "csv",
                    "processed": idx + 1,
                    "total": total_rows,
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
                "total_entries": total_rows,
                "ingested": ingested_count,
                "duplicates": duplicate_count,
                "skipped": skipped_count,
                "errors_count": len(errors),
                "errors": errors[:50],
                "warnings": warnings[:50],
                "encoding": used_encoding,
                "elapsed_seconds": elapsed
            }
        }
