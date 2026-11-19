"""
src/crawl/utils.py
Utility functions for file validation, hashing, and writing to CSV logs.
"""

from __future__ import annotations

import csv
import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pymupdf as fitz

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths (resolved relative to project root at import time)
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
METADATA_PATH = _PROJECT_ROOT / "data" / "metadata.csv"
CRAWL_LOG_PATH = _PROJECT_ROOT / "data" / "crawl_log.csv"
DOWNLOAD_DIR = _PROJECT_ROOT / "data" / "raw" / "pdf"

# Column order must match the CSV headers created manually
_METADATA_FIELDS = [
    "doc_id",
    "ticker",
    "company",
    "industry",
    "doc_type",
    "year",
    "num_pages",
    "has_text_layer",
    "source_url",
    "source_name",
    "sha256",
    "downloaded_at",
]

_CRAWL_LOG_FIELDS = [
    "timestamp",
    "ticker",
    "doc_type",
    "year",
    "source_url",
    "status",
    "error_reason",
    "file_path",
    "sha256",
]


# ---------------------------------------------------------------------------
# File validation helpers
# ---------------------------------------------------------------------------


def compute_sha256(filepath: Path) -> str:
    """Return the SHA-256 hex digest of a file, read in 64 KiB chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def count_pages(filepath: Path) -> int:
    """Return the number of pages in a PDF file.

    Returns 0 if the file cannot be opened as a PDF.
    """
    try:
        with fitz.open(str(filepath)) as doc:
            return doc.page_count
    except Exception as exc:
        logger.warning("count_pages failed for %s: %s", filepath.name, exc)
        return 0


def check_text_layer(filepath: Path, sample_pages: int = 3) -> bool:
    """Return True if at least one of the first `sample_pages` pages has extractable text.

    A PDF exported digitally almost always has a text layer; a scanned/imaged
    PDF typically does not (or has very little text per page).
    """
    try:
        with fitz.open(str(filepath)) as doc:
            pages_to_check = min(sample_pages, doc.page_count)
            for i in range(pages_to_check):
                page = doc.load_page(i)
                if page.get_text("text").strip():
                    return True
        return False
    except Exception as exc:
        logger.warning("check_text_layer failed for %s: %s", filepath.name, exc)
        return False


def is_valid_pdf(filepath: Path) -> bool:
    """Return True if the file exists, is non-empty, and opens without errors."""
    if not filepath.exists() or filepath.stat().st_size == 0:
        return False
    try:
        with fitz.open(str(filepath)) as doc:
            return doc.page_count > 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


def is_already_downloaded(ticker: str, doc_type: str, year: int) -> bool:
    """Return True if a metadata row already exists for this (ticker, doc_type, year).

    Checks the metadata CSV to avoid re-downloading files that are already
    on disk and validated. Idempotent crawler runs depend on this check.
    """
    if not METADATA_PATH.exists():
        return False
    with open(METADATA_PATH, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if (
                row.get("ticker") == ticker
                and row.get("doc_type") == doc_type
                and str(row.get("year")) == str(year)
            ):
                return True
    return False


def make_doc_id(ticker: str, doc_type: str, year: int) -> str:
    """Return a canonical document ID, e.g. ``VCB_BCTN_2024``."""
    return f"{ticker}_{doc_type}_{year}"


def make_filename(ticker: str, doc_type: str, year: int) -> str:
    """Return the canonical PDF filename, e.g. ``VCB_BCTN_2024.pdf``."""
    return f"{make_doc_id(ticker, doc_type, year)}.pdf"


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------


def _ensure_csv_header(path: Path, fields: list[str]) -> None:
    """Create the CSV with headers if it doesn't already exist."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=fields)
            writer.writeheader()
        logger.debug("Created %s with headers", path.name)


def append_metadata(row: dict[str, Any]) -> None:
    """Append one validated document's metadata to ``data/metadata.csv``.

    Missing keys are filled with empty strings.
    """
    _ensure_csv_header(METADATA_PATH, _METADATA_FIELDS)
    record = {field: row.get(field, "") for field in _METADATA_FIELDS}
    with open(METADATA_PATH, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_METADATA_FIELDS)
        writer.writerow(record)
    logger.debug(
        "metadata: wrote %s %s %s", record["ticker"], record["doc_type"], record["year"]
    )


def append_crawl_log(row: dict[str, Any]) -> None:
    """Append one crawl event (success or failure) to ``data/crawl_log.csv``.

    Always stamps the current UTC time in the ``timestamp`` field.
    """
    _ensure_csv_header(CRAWL_LOG_PATH, _CRAWL_LOG_FIELDS)
    record = {field: row.get(field, "") for field in _CRAWL_LOG_FIELDS}
    record["timestamp"] = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    with open(CRAWL_LOG_PATH, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CRAWL_LOG_FIELDS)
        writer.writerow(record)
