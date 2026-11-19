"""
src/crawl/ingest.py
Local PDF Ingestion and Metadata Synchronization for ViFinRAG.

Scans the data/raw/pdf/ directory, validates all PDF files, computes SHA-256
hashes, counts pages, detects text layers, and synchronizes data/metadata.csv.

Usage:
    # Run ingestion on all PDF files in data/raw/pdf/
    python -m src.crawl.ingest

    # Show help and available options
    python -m src.crawl.ingest --help

    # Dry-run (validate files without modifying metadata.csv)
    python -m src.crawl.ingest --dry-run
"""

from __future__ import annotations

import argparse
import csv
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from src.crawl.utils import (
    DOWNLOAD_DIR,
    METADATA_PATH,
    _METADATA_FIELDS,
    check_text_layer,
    compute_sha256,
    count_pages,
    is_valid_pdf,
    make_doc_id,
)

logger = logging.getLogger(__name__)

FILENAME_PATTERN = re.compile(
    r"^(?P<ticker>[A-Za-z0-9]+)_(?P<doc_type>[A-Za-z]+)_(?P<year>\d{4})\.pdf$",
    re.IGNORECASE,
)


def load_company_lookup(config_path: Path) -> dict[str, dict[str, str]]:
    """Build a lookup mapping from ticker to company metadata."""
    lookup: dict[str, dict[str, str]] = {}
    if not config_path.exists():
        logger.warning("Config %s not found, company names will default to ticker", config_path)
        return lookup

    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    for co in data.get("companies", []):
        ticker = co.get("ticker", "").strip().upper()
        if ticker:
            lookup[ticker] = {
                "company": co.get("name", ticker),
                "industry": co.get("industry", ""),
                "source_name": co.get("priority_source", "ir"),
                "ir_url": co.get("ir_url", ""),
            }
    return lookup


def read_existing_metadata(meta_path: Path) -> dict[str, dict[str, Any]]:
    """Read existing metadata.csv keyed by doc_id."""
    existing: dict[str, dict[str, Any]] = {}
    if not meta_path.exists() or meta_path.stat().st_size == 0:
        return existing

    with open(meta_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_id = row.get("doc_id", "").strip()
            if doc_id:
                existing[doc_id] = row
    return existing


def ingest_all(
    pdf_dir: Path = DOWNLOAD_DIR,
    meta_path: Path = METADATA_PATH,
    config_path: Path = Path("configs/sources.yaml"),
    dry_run: bool = False,
) -> None:
    """Ingest and validate all PDFs in pdf_dir into metadata.csv."""
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    print(f"\nFound {len(pdf_files)} PDF files in {pdf_dir}\n")
    if not pdf_files:
        print("No PDF files found to ingest. Place your files in data/raw/pdf/ first.")
        return

    company_lookup = load_company_lookup(config_path)
    existing_meta = read_existing_metadata(meta_path)

    new_metadata_rows: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()

    valid_count = 0
    invalid_count = 0
    duplicate_count = 0

    for pdf_path in pdf_files:
        filename = pdf_path.name
        match = FILENAME_PATTERN.match(filename)
        if not match:
            logger.warning("SKIP non-standard filename format: %s (expected <TICKER>_<TYPE>_<YEAR>.pdf)", filename)
            invalid_count += 1
            continue

        ticker = match.group("ticker").upper()
        doc_type = match.group("doc_type").upper()
        year = int(match.group("year"))
        doc_id = make_doc_id(ticker, doc_type, year)

        # Validate PDF
        if not is_valid_pdf(pdf_path):
            logger.error("CORRUPT or invalid PDF: %s", filename)
            invalid_count += 1
            continue

        sha256 = compute_sha256(pdf_path)
        if sha256 in seen_hashes:
            logger.warning("DUPLICATE file content detected for %s (sha256=%s)", filename, sha256[:12])
            duplicate_count += 1
            continue
        seen_hashes.add(sha256)

        num_pages = count_pages(pdf_path)
        has_text = check_text_layer(pdf_path)

        co_info = company_lookup.get(ticker, {})
        company_name = co_info.get("company", ticker)
        industry = co_info.get("industry", "")
        source_name = co_info.get("source_name", "ir")
        source_url = co_info.get("ir_url", "")

        # Preserve existing downloaded_at or use now
        downloaded_at = (
            existing_meta.get(doc_id, {}).get("downloaded_at")
            or datetime.now(timezone.utc).isoformat()
        )

        row = {
            "doc_id": doc_id,
            "ticker": ticker,
            "company": company_name,
            "industry": industry,
            "doc_type": doc_type,
            "year": year,
            "num_pages": num_pages,
            "has_text_layer": has_text,
            "source_url": source_url,
            "source_name": source_name,
            "sha256": sha256,
            "downloaded_at": downloaded_at,
        }
        new_metadata_rows.append(row)
        valid_count += 1

    # Write out metadata.csv
    if not dry_run:
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        with open(meta_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_METADATA_FIELDS)
            writer.writeheader()
            for r in new_metadata_rows:
                writer.writerow(r)
        logger.info("Updated %s with %d records", meta_path, len(new_metadata_rows))

    # Print summary table
    print("=" * 80)
    print("INGESTION & METADATA SUMMARY")
    print("=" * 80)
    print(f"{'Doc ID':<18} | {'Pages':>5} | {'Text':>5} | {'Industry':<25} | {'SHA256 (first 8)'}")
    print("-" * 80)
    for r in new_metadata_rows:
        text_str = "YES" if r["has_text_layer"] else "NO"
        ind = (r["industry"][:23] + "..") if len(r["industry"]) > 25 else r["industry"]
        print(f"{r['doc_id']:<18} | {r['num_pages']:>5} | {text_str:>5} | {ind:<25} | {r['sha256'][:8]}")
    print("-" * 80)
    print(f"Total Valid Documents : {valid_count}")
    print(f"Invalid / Corrupted   : {invalid_count}")
    print(f"Duplicate Content     : {duplicate_count}")
    print("=" * 80 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ViFinRAG Ingestion: Validate local PDF files and generate metadata.csv."
    )
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        default=DOWNLOAD_DIR,
        help="Directory containing PDF files (default: data/raw/pdf/)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/sources.yaml"),
        help="Path to sources.yaml (default: configs/sources.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate files without writing metadata.csv",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    ingest_all(
        pdf_dir=args.pdf_dir,
        config_path=args.config,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
