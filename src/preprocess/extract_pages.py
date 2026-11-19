"""
src/preprocess/extract_pages.py
PDF Preprocessing: Render page images (DPI 150-200) and extract structured text.

Converts each PDF document in data/raw/pdf/ into:
  1. Rendered page images: data/pages/<doc_id>/p<page_num>.png (for Vision-native ColPali / VLM)
  2. Plain text per page:  data/text/<doc_id>/p<page_num>.txt  (for BM25 / Quick inspection)
  3. Structured Markdown:  data/text/<doc_id>/p<page_num>.md   (with headings & Markdown tables)
  4. Structured JSON:      data/text/<doc_id>/p<page_num>.json (blocks with bounding boxes [x0, y0, x1, y1])

Usage:
    # Run preprocessing on all PDFs in data/raw/pdf/
    python -m src.preprocess.extract_pages

    # Show help and available options
    python -m src.preprocess.extract_pages --help

    # Process only a specific document with 200 DPI
    python -m src.preprocess.extract_pages --doc-id VNM_BCTN_2024 --dpi 200

    # Process only a specific company ticker
    python -m src.preprocess.extract_pages --ticker FPT

    # Force re-processing existing pages
    python -m src.preprocess.extract_pages --force
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import logging
import sys
from pathlib import Path
from typing import Any

import pymupdf
from tqdm import tqdm

logger = logging.getLogger(__name__)

# Default project paths relative to workspace root
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PDF_DIR = _PROJECT_ROOT / "data" / "raw" / "pdf"
DEFAULT_PAGES_DIR = _PROJECT_ROOT / "data" / "pages"
DEFAULT_TEXT_DIR = _PROJECT_ROOT / "data" / "text"


def extract_page_content(
    page: pymupdf.Page,
    page_num: int,
) -> tuple[str, str, dict[str, Any]]:
    """Extract plain text, structured markdown, and detailed JSON with bounding boxes.

    Parameters
    ----------
    page:
        PyMuPDF Page object.
    page_num:
        1-indexed page number.

    Returns
    -------
    tuple[str, str, dict[str, Any]]
        (plain_text, markdown_text, page_json)
    """
    # 1. Plain text extraction
    plain_text = page.get_text("text")

    # 2. Dimensions
    rect = page.rect
    width, height = round(rect.width, 2), round(rect.height, 2)

    # 3. Table detection and Markdown formatting
    tables_data: list[dict[str, Any]] = []
    table_bboxes: list[list[float]] = []

    try:
        tabs = page.find_tables()
        for tab in tabs:
            t_bbox = [round(c, 2) for c in tab.bbox]
            table_bboxes.append(tab.bbox)
            md_table = ""

            try:
                if hasattr(tab, "to_markdown"):
                    md_table = tab.to_markdown()
                else:
                    rows = tab.extract()
                    if rows and len(rows) > 0:
                        header = "| " + " | ".join(str(c or "").strip() for c in rows[0]) + " |"
                        sep = "| " + " | ".join("---" for _ in rows[0]) + " |"
                        body = [
                            "| " + " | ".join(str(c or "").strip() for c in r) + " |"
                            for r in rows[1:]
                        ]
                        md_table = "\n".join([header, sep] + body)
            except Exception:
                md_table = ""

            tables_data.append(
                {
                    "bbox": t_bbox,
                    "rows": getattr(tab, "row_count", len(tab.extract() or [])),
                    "cols": getattr(tab, "col_count", 0),
                    "markdown": md_table,
                    "data": tab.extract(),
                }
            )
    except Exception as exc:
        logger.debug("Table detection error on page %d: %s", page_num, exc)

    # 4. Structured blocks with bounding boxes and font sizes
    blocks_data: list[dict[str, Any]] = []
    md_elements: list[str] = []

    text_dict = page.get_text("dict")
    for block in text_dict.get("blocks", []):
        b_type = "image" if block.get("type") == 1 else "text"
        bbox = [round(c, 2) for c in block.get("bbox", [0, 0, 0, 0])]

        # Check if block falls inside any detected table bbox
        is_inside_table = False
        for t_bbox in table_bboxes:
            if (
                bbox[0] >= t_bbox[0] - 5
                and bbox[1] >= t_bbox[1] - 5
                and bbox[2] <= t_bbox[2] + 5
                and bbox[3] <= t_bbox[3] + 5
            ):
                is_inside_table = True
                break

        if b_type == "text":
            block_lines: list[str] = []
            max_font_size = 0.0
            is_bold = False

            for line in block.get("lines", []):
                line_text = ""
                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    line_text += span_text
                    sz = span.get("size", 0.0)
                    if sz > max_font_size:
                        max_font_size = sz
                    flags = span.get("flags", 0)
                    if flags & 2 != 0 or "bold" in span.get("font", "").lower():
                        is_bold = True
                if line_text.strip():
                    block_lines.append(line_text.strip())

            block_text = "\n".join(block_lines).strip()
            if not block_text:
                continue

            blocks_data.append(
                {
                    "bbox": bbox,
                    "type": "text",
                    "font_size": round(max_font_size, 1),
                    "is_bold": is_bold,
                    "text": block_text,
                    "is_inside_table": is_inside_table,
                }
            )

            # Assemble into markdown lines (if not redundant with table)
            if not is_inside_table:
                if max_font_size >= 16:
                    md_elements.append(f"## {block_text}")
                elif max_font_size >= 13 and is_bold:
                    md_elements.append(f"### {block_text}")
                else:
                    md_elements.append(block_text)

        elif b_type == "image":
            blocks_data.append(
                {
                    "bbox": bbox,
                    "type": "image",
                    "text": "",
                    "is_inside_table": is_inside_table,
                }
            )

    # Append detected markdown tables
    for tab_info in tables_data:
        if tab_info.get("markdown"):
            md_elements.append(tab_info["markdown"])

    markdown_text = "\n\n".join(md_elements).strip()
    if not markdown_text:
        markdown_text = plain_text

    page_json = {
        "page": page_num,
        "width": width,
        "height": height,
        "total_blocks": len(blocks_data),
        "total_tables": len(tables_data),
        "blocks": blocks_data,
        "tables": tables_data,
    }

    return plain_text, markdown_text, page_json


def _is_valid_file(p: Path) -> bool:
    """Check if file exists and has content (> 0 bytes)."""
    try:
        return p.exists() and p.stat().st_size > 0
    except OSError:
        return False


def process_document(
    pdf_path: Path,
    pages_dir: Path = DEFAULT_PAGES_DIR,
    text_dir: Path = DEFAULT_TEXT_DIR,
    dpi: int = 150,
    render_images: bool = True,
    extract_text: bool = True,
    force: bool = False,
    show_page_progress: bool = True,
) -> dict[str, Any]:
    """Process a single PDF: render page images and extract text (.txt, .md, .json).

    Parameters
    ----------
    pdf_path:
        Path to the source PDF file (e.g. data/raw/pdf/VNM_BCTN_2024.pdf).
    pages_dir:
        Output base directory for page images.
    text_dir:
        Output base directory for page text files.
    dpi:
        Resolution for rendering page images (150-200 recommended).
    render_images:
        Whether to render PNG images for each page.
    extract_text:
        Whether to extract text (.txt, .md, .json) for each page.
    force:
        If True, re-generate files even if they already exist on disk.
    show_page_progress:
        Whether to show a page-level progress bar (disable for multiprocessing).

    Returns
    -------
    dict[str, Any]
        Summary containing doc_id, total_pages, images_created, text_created, skipped.
    """
    doc_id = pdf_path.stem
    doc_pages_dir = pages_dir / doc_id
    doc_text_dir = text_dir / doc_id

    if render_images:
        doc_pages_dir.mkdir(parents=True, exist_ok=True)
    if extract_text:
        doc_text_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "doc_id": doc_id,
        "total_pages": 0,
        "images_created": 0,
        "text_created": 0,
        "md_created": 0,
        "json_created": 0,
        "skipped": 0,
        "status": "success",
        "error": "",
    }

    try:
        with pymupdf.open(pdf_path) as doc:
            num_pages = len(doc)
            stats["total_pages"] = num_pages

            # Iterate pages with optional progress bar
            page_iter = range(num_pages)
            page_pbar = None
            if show_page_progress:
                page_pbar = tqdm(
                    total=num_pages,
                    desc=f"  ↳ {doc_id}",
                    unit="page",
                    leave=False,
                )

            for page_idx in page_iter:
                page_num = page_idx + 1  # 1-indexed
                page_label = f"p{page_num}"

                img_dest = doc_pages_dir / f"{page_label}.png"
                txt_dest = doc_text_dir / f"{page_label}.txt"
                md_dest = doc_text_dir / f"{page_label}.md"
                json_dest = doc_text_dir / f"{page_label}.json"

                # Robust idempotency: verify file exists AND is not empty (> 0 bytes)
                need_img = render_images and (force or not _is_valid_file(img_dest))
                need_txt = extract_text and (
                    force
                    or not _is_valid_file(txt_dest)
                    or not _is_valid_file(md_dest)
                    or not _is_valid_file(json_dest)
                )

                # Skip if already fully generated
                if not need_img and not need_txt:
                    stats["skipped"] += 1
                    if page_pbar:
                        page_pbar.update(1)
                    continue

                page = doc[page_idx]

                # 1. Render PNG image if needed
                if need_img:
                    pixmap = page.get_pixmap(dpi=dpi)
                    pixmap.save(img_dest)
                    stats["images_created"] += 1

                # 2. Extract plain text, markdown, and structured JSON if needed
                if need_txt:
                    plain_txt, md_txt, page_json = extract_page_content(page, page_num)

                    txt_dest.write_text(plain_txt, encoding="utf-8")
                    stats["text_created"] += 1

                    md_dest.write_text(md_txt, encoding="utf-8")
                    stats["md_created"] += 1

                    json_dest.write_text(
                        json.dumps(page_json, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    stats["json_created"] += 1

                if page_pbar:
                    page_pbar.update(1)

            if page_pbar:
                page_pbar.close()

    except Exception as exc:
        logger.error("[%s] Error processing %s: %s", doc_id, pdf_path.name, exc)
        stats["status"] = "error"
        stats["error"] = str(exc)

    return stats


def _process_doc_worker(kwargs: dict[str, Any]) -> dict[str, Any]:
    """Helper for ProcessPoolExecutor."""
    kwargs["show_page_progress"] = False
    return process_document(**kwargs)


def process_all_documents(
    pdf_dir: Path = DEFAULT_PDF_DIR,
    pages_dir: Path = DEFAULT_PAGES_DIR,
    text_dir: Path = DEFAULT_TEXT_DIR,
    doc_id_filter: str | None = None,
    ticker_filter: str | None = None,
    dpi: int = 150,
    render_images: bool = True,
    extract_text: bool = True,
    force: bool = False,
    workers: int = 1,
) -> list[dict[str, Any]]:
    """Scan and process all PDF documents according to configuration filters.

    Parameters
    ----------
    pdf_dir:
        Directory containing input PDF files.
    pages_dir:
        Output directory for rendered page images.
    text_dir:
        Output directory for extracted text files.
    doc_id_filter:
        Optional specific doc_id to process (e.g. "VNM_BCTN_2024").
    ticker_filter:
        Optional stock ticker to filter by (e.g. "FPT").
    dpi:
        Resolution for rendered images (default: 150).
    render_images:
        Whether to generate page PNGs.
    extract_text:
        Whether to generate page TXTs, MDs, and JSONs.
    force:
        Whether to overwrite existing files.
    workers:
        Number of parallel worker processes (default: 1).

    Returns
    -------
    list[dict[str, Any]]
        List of statistics per processed document.
    """
    if not pdf_dir.exists():
        logger.error("Input PDF directory does not exist: %s", pdf_dir)
        return []

    pdf_files = sorted(pdf_dir.glob("*.pdf"))

    # Apply filters
    if doc_id_filter:
        target_id = doc_id_filter.strip().lower()
        pdf_files = [f for f in pdf_files if f.stem.lower() == target_id]
    elif ticker_filter:
        prefix = f"{ticker_filter.strip().upper()}_"
        pdf_files = [f for f in pdf_files if f.stem.upper().startswith(prefix)]

    if not pdf_files:
        logger.warning("No PDF files matching criteria found in %s", pdf_dir)
        return []

    logger.info(
        "Starting preprocessing | files=%d dpi=%d images=%s text=%s force=%s workers=%d",
        len(pdf_files),
        dpi,
        render_images,
        extract_text,
        force,
        workers,
    )

    all_stats: list[dict[str, Any]] = []

    if workers > 1 and len(pdf_files) > 1:
        num_workers = min(workers, len(pdf_files))
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as executor:
            future_to_doc = {
                executor.submit(
                    _process_doc_worker,
                    {
                        "pdf_path": pdf_path,
                        "pages_dir": pages_dir,
                        "text_dir": text_dir,
                        "dpi": dpi,
                        "render_images": render_images,
                        "extract_text": extract_text,
                        "force": force,
                    },
                ): pdf_path.stem
                for pdf_path in pdf_files
            }
            with tqdm(
                total=len(future_to_doc),
                desc=f"Processing PDFs ({num_workers} parallel workers)",
                unit="doc",
            ) as pbar:
                for future in concurrent.futures.as_completed(future_to_doc):
                    doc_id = future_to_doc[future]
                    try:
                        stat = future.result()
                        all_stats.append(stat)
                        pbar.set_postfix_str(f"{doc_id} ({stat.get('total_pages', 0)}p)")
                    except Exception as exc:
                        logger.error("Worker failed on %s: %s", doc_id, exc)
                        all_stats.append(
                            {
                                "doc_id": doc_id,
                                "total_pages": 0,
                                "images_created": 0,
                                "text_created": 0,
                                "md_created": 0,
                                "json_created": 0,
                                "skipped": 0,
                                "status": "error",
                                "error": str(exc),
                            }
                        )
                    pbar.update(1)
    else:
        pbar = tqdm(pdf_files, desc="Preprocessing PDFs", unit="doc")
        for pdf_path in pbar:
            doc_id = pdf_path.stem
            pbar.set_postfix_str(doc_id)
            stat = process_document(
                pdf_path=pdf_path,
                pages_dir=pages_dir,
                text_dir=text_dir,
                dpi=dpi,
                render_images=render_images,
                extract_text=extract_text,
                force=force,
            )
            all_stats.append(stat)

    # Print summary table
    total_pages = sum(s["total_pages"] for s in all_stats)
    total_imgs = sum(s["images_created"] for s in all_stats)
    total_txts = sum(s["text_created"] for s in all_stats)
    total_mds = sum(s["md_created"] for s in all_stats)
    total_jsons = sum(s["json_created"] for s in all_stats)
    total_skips = sum(s["skipped"] for s in all_stats)
    error_docs = [s for s in all_stats if s["status"] == "error"]

    print("\n" + "=" * 70)
    print("PREPROCESSING EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Total PDFs Processed   : {len(all_stats)}")
    print(f"Total Pages in Corpus  : {total_pages}")
    print(f"Page Images Generated  : {total_imgs} (DPI={dpi})")
    print(f"Text Files (.txt)      : {total_txts}")
    print(f"Markdown Files (.md)   : {total_mds}")
    print(f"Structured JSON (.json): {total_jsons}")
    print(f"Pages Skipped (Cached) : {total_skips}")
    print(f"Failed Documents       : {len(error_docs)}")
    if error_docs:
        for err in error_docs:
            print(f"  - {err['doc_id']}: {err['error']}")
    print("=" * 70 + "\n")

    return all_stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ViFinRAG Preprocessing: Render PDF pages to images and extract text (TXT, MD, JSON with BBoxes)."
    )
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        default=DEFAULT_PDF_DIR,
        help="Directory containing PDF files (default: data/raw/pdf)",
    )
    parser.add_argument(
        "--pages-dir",
        type=Path,
        default=DEFAULT_PAGES_DIR,
        help="Directory to save rendered page images (default: data/pages)",
    )
    parser.add_argument(
        "--text-dir",
        type=Path,
        default=DEFAULT_TEXT_DIR,
        help="Directory to save extracted text files (default: data/text)",
    )
    parser.add_argument(
        "--doc-id",
        type=str,
        default=None,
        help="Process only a specific document ID (e.g. VNM_BCTN_2024).",
    )
    parser.add_argument(
        "--ticker",
        type=str,
        default=None,
        help="Process all documents for a specific ticker (e.g. FPT).",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
        choices=[100, 150, 200, 300],
        help="Rendering resolution DPI (default: 150, recommended: 150-200).",
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip rendering page PNG images (only extract text/md/json).",
    )
    parser.add_argument(
        "--skip-text",
        action="store_true",
        help="Skip extracting text (only render images).",
    )
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=1,
        help="Number of parallel worker processes (default: 1, recommended: 4-6 on multi-core CPUs).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing page images and text files.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable DEBUG logging output.",
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    process_all_documents(
        pdf_dir=args.pdf_dir,
        pages_dir=args.pages_dir,
        text_dir=args.text_dir,
        doc_id_filter=args.doc_id,
        ticker_filter=args.ticker,
        dpi=args.dpi,
        render_images=not args.skip_images,
        extract_text=not args.skip_text,
        force=args.force,
        workers=args.workers,
    )


if __name__ == "__main__":
    main()
