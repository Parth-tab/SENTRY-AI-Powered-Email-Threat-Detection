"""Content-sniffing engine for forensic email ingestion.
Inspects payload bytes (first 4KB) according to RFC 822 header grammar,
ZIP archive signatures, and CSV tabular headers.
Sniffing takes precedence over file extension checks.
"""

import io
import re
import csv
import zipfile
from typing import Tuple, Optional

HEADER_REGEX = re.compile(r"^[A-Za-z0-9-]+:\s*.+", re.MULTILINE)

CSV_KNOWN_COLUMNS = {
    "subject", "body", "text", "content", "message", "label",
    "target", "class", "spam", "is_phishing", "sender", "from",
    "to", "recipient", "date", "message_id"
}

def is_rfc822(data: bytes) -> bool:
    """Inspects first 4KB of payload to verify RFC 822 / 5322 header grammar.
    Requires at least one valid header (e.g. 'From:', 'Subject:', 'Received:')
    before the first empty line, and zero null bytes.
    """
    if not data:
        return False
    
    sample = data[:4096]
    # Binary / null byte check
    if b"\x00" in sample[:512]:
        return False
    
    # Strip BOM if present
    if sample.startswith(b"\xef\xbb\xbf"):
        sample = sample[3:]
    elif sample.startswith(b"\xff\xfe") or sample.startswith(b"\xfe\xff"):
        sample = sample[2:]

    try:
        text = sample.decode("utf-8", errors="replace")
    except Exception:
        try:
            text = sample.decode("latin-1", errors="replace")
        except Exception:
            return False

    # Extract header block (before first blank line)
    parts = re.split(r"\r?\n\r?\n", text, maxsplit=1)
    header_block = parts[0] if parts else text

    lines = [line.strip() for line in header_block.splitlines() if line.strip()]
    if not lines:
        return False

    # Check for at least one RFC-compliant header line
    return any(HEADER_REGEX.match(line) for line in lines)

def is_zip_archive(data: bytes) -> bool:
    """Checks if payload is a valid ZIP archive."""
    if not data or len(data) < 4:
        return False
    if data.startswith(b"PK\x03\x04") or data.startswith(b"PK\x05\x06") or data.startswith(b"PK\x07\x08"):
        return True
    try:
        return zipfile.is_zipfile(io.BytesIO(data))
    except Exception:
        return False

def is_csv_format(data: bytes) -> bool:
    """Checks if payload is a delimited tabular CSV/TSV with recognizable email columns."""
    if not data:
        return False
    if b"\x00" in data[:512]:
        return False

    sample = data[:4096]
    if sample.startswith(b"\xef\xbb\xbf"):
        sample = sample[3:]

    try:
        text = sample.decode("utf-8", errors="replace")
    except Exception:
        try:
            text = sample.decode("latin-1", errors="replace")
        except Exception:
            return False

    first_line = text.splitlines()[0] if text.splitlines() else ""
    if not ("," in first_line or "\t" in first_line or ";" in first_line):
        return False

    try:
        reader = csv.reader(io.StringIO(first_line))
        headers = [h.strip().lower().replace('"', '').replace("'", "") for h in next(reader, []) if h.strip()]
        if len(headers) >= 2 and any(h in CSV_KNOWN_COLUMNS for h in headers):
            return True
    except Exception:
        pass
    return False

def sniff_payload_format(data: bytes, filename: str = "") -> str:
    """Classifies payload into 'archive', 'csv', 'rfc822', or 'unsupported'.
    Content sniffing takes priority over filename extension.
    """
    if not data:
        return "unsupported"

    # 1. Check ZIP Archive signature
    if is_zip_archive(data) or (filename and filename.lower().endswith(".zip")):
        if is_zip_archive(data):
            return "archive"

    # 2. Check CSV Dataset grammar
    if is_csv_format(data) or (filename and filename.lower().endswith((".csv", ".tsv"))):
        if is_csv_format(data):
            return "csv"

    # 3. Check RFC 822 Email grammar (extensionless, .eml, .msg, .mbox, .txt)
    if is_rfc822(data):
        return "rfc822"

    # Fallback to extension hint if content is plain text
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    if ext in ("eml", "msg", "mbox", "txt"):
        return "rfc822"
    if ext == "csv":
        return "csv"
    if ext == "zip":
        return "archive"

    return "unsupported"
