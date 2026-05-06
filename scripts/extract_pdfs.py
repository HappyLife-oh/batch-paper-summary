"""
batch-paper-summary: PDF Extraction Script
Extracts text, tables, and embedded images from all PDFs in a directory.

Usage:
    python extract_pdfs.py --input <pdf_dir> --output <output_dir>

Output structure:
    output_dir/
    ├── PaperName/
    │   ├── full_text.txt       # Complete extracted text (UTF-8)
    │   ├── page_XX.txt         # Per-page text (optional, with --per-page)
    │   ├── tables/
    │   │   ├── table_01.csv    # Tables in CSV format
    │   │   └── table_01.json   # Tables in JSON format (with --json-tables)
    │   ├── images/
    │   │   ├── figure_001.png  # Embedded images
    │   │   └── figure_002.png
    │   └── metadata.json       # Paper metadata (title, authors, DOI, etc.)
    └── _extraction_log.json    # Global extraction status
"""

import argparse
import json
import logging
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Dependencies check (friendly error messages)
# ---------------------------------------------------------------------------
MISSING = []
try:
    import pdfplumber
except ImportError:
    MISSING.append("pdfplumber")

try:
    import fitz  # pymupdf
except ImportError:
    MISSING.append("pymupdf")

if MISSING:
    print(f"[ERROR] Missing dependencies: {', '.join(MISSING)}")
    print(f"        Install with: pip install {' '.join(MISSING)}")
    print(f"        Or: pip install -r requirements.txt")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("extract_pdfs")


def sanitize_filename(name: str, max_len: int = 80) -> str:
    """Remove or replace characters unsafe for Windows/Linux filenames."""
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    if len(name) > max_len:
        name = name[:max_len].rsplit(" ", 1)[0]
    return name


def extract_text(pdf_path: Path, output_dir: Path, per_page: bool = False) -> Path:
    """Extract full text from PDF using pdfplumber. Returns path to full_text.txt."""
    text_path = output_dir / "full_text.txt"
    pages_dir = output_dir / "pages"
    full_text: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        if per_page:
            pages_dir.mkdir(parents=True, exist_ok=True)

        for i, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text()
            if page_text:
                header = f"\n{'='*60}\nPAGE {i}\n{'='*60}\n"
                full_text.append(header + page_text)

                if per_page:
                    page_path = pages_dir / f"page_{i:04d}.txt"
                    page_path.write_text(page_text, encoding="utf-8")

    combined = "\n".join(full_text)
    text_path.write_text(combined, encoding="utf-8")
    log.info("  -> Text: %d chars across %d pages", len(combined), len(full_text))
    return text_path


def extract_tables(pdf_path: Path, output_dir: Path, json_tables: bool = False) -> int:
    """Extract tables from PDF using pdfplumber. Returns count of tables found."""
    tables_dir = output_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            page_tables = page.extract_tables()
            for j, table in enumerate(page_tables):
                if not table or all(not any(row) for row in table):
                    continue
                count += 1
                # CSV
                csv_path = tables_dir / f"table_{count:02d}_p{i}.csv"
                rows = [[str(c).replace("\n", " ") if c else "" for c in row] for row in table]
                csv_content = "\n".join(",".join(f'"{c}"' for c in row) for row in rows)
                csv_path.write_text(csv_content, encoding="utf-8-sig")

                # JSON (optional)
                if json_tables:
                    json_path = tables_dir / f"table_{count:02d}_p{i}.json"
                    json_path.write_text(
                        json.dumps({"page": i, "table_index": j, "rows": table}, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
    if count:
        log.info("  -> Tables: %d extracted", count)
    return count


def extract_images(pdf_path: Path, output_dir: Path, min_size: int = 1024) -> int:
    """Extract embedded images from PDF using pymupdf. Returns count."""
    images_dir = output_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    count = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        image_list = page.get_images(full=True)
        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            if len(image_bytes) < min_size:
                continue  # skip tiny images (icons, etc.)
            ext = base_image["ext"]
            count += 1
            img_path = images_dir / f"figure_{count:03d}_p{page_num + 1}.{ext}"
            img_path.write_bytes(image_bytes)

    doc.close()
    if count:
        log.info("  -> Images: %d extracted", count)
    return count


def extract_metadata_heuristic(text: str) -> dict:
    """Heuristic extraction of title and first author from paper text."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    title = lines[0] if lines else ""
    # Try to find DOI
    doi_match = re.search(r"(doi\.org/|DOI:?\s*)(10\.\d{4,}/[^\s]+)", text, re.IGNORECASE)
    doi = doi_match.group(2) if doi_match else ""
    return {"title": title[:300], "doi": doi}


def process_pdf(pdf_path: Path, base_output_dir: Path, args) -> dict:
    """Process a single PDF: extract text, tables, images."""
    folder_name = sanitize_filename(pdf_path.stem)
    output_dir = base_output_dir / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    log.info("Processing: %s", pdf_path.name)

    result = {"file": pdf_path.name, "output": str(output_dir), "success": True}

    # Text
    try:
        text_path = extract_text(pdf_path, output_dir, per_page=args.per_page)
        result["text_chars"] = text_path.stat().st_size
    except Exception as e:
        log.error("  Text extraction failed: %s", e)
        result["success"] = False
        result["text_error"] = str(e)
        return result

    # Tables
    try:
        result["tables_count"] = extract_tables(pdf_path, output_dir, json_tables=args.json_tables)
    except Exception as e:
        log.warning("  Table extraction failed: %s", e)
        result["tables_count"] = 0

    # Images
    try:
        result["images_count"] = extract_images(pdf_path, output_dir)
    except Exception as e:
        log.warning("  Image extraction failed: %s", e)
        result["images_count"] = 0

    # Metadata
    try:
        full_text = (output_dir / "full_text.txt").read_text(encoding="utf-8")
        meta = extract_metadata_heuristic(full_text)
        (output_dir / "metadata.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        result["title_guess"] = meta["title"]
    except Exception:
        pass

    return result


def main():
    parser = argparse.ArgumentParser(
        description="batch-paper-summary: Extract text, tables, and images from PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_pdfs.py -i ./papers -o ./_extracted
  python extract_pdfs.py -i ./papers -o ./_extracted --per-page --json-tables
  python extract_pdfs.py -i ./papers -o ./_extracted --skip-images
        """,
    )
    parser.add_argument("-i", "--input", required=True, help="Directory containing PDF files")
    parser.add_argument("-o", "--output", required=True, help="Output directory for extracted content")
    parser.add_argument("--per-page", action="store_true", help="Also save per-page text files")
    parser.add_argument("--json-tables", action="store_true", help="Also save tables as JSON (default: CSV only)")
    parser.add_argument("--skip-images", action="store_true", help="Skip image extraction (faster)")
    parser.add_argument("--skip-tables", action="store_true", help="Skip table extraction")
    args = parser.parse_args()

    input_dir = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        log.error("Input directory does not exist: %s", input_dir)
        sys.exit(1)

    pdf_files = sorted(input_dir.glob("*.pdf"))
    if not pdf_files:
        log.error("No PDF files found in: %s", input_dir)
        sys.exit(1)

    log.info("=" * 50)
    log.info("Found %d PDF(s) in: %s", len(pdf_files), input_dir)
    log.info("Output directory: %s", output_dir)
    log.info("=" * 50)

    results = []
    for pdf_path in pdf_files:
        r = process_pdf(pdf_path, output_dir, args)
        results.append(r)

    # Summary
    success = sum(1 for r in results if r["success"])
    total_tables = sum(r.get("tables_count", 0) for r in results)
    total_images = sum(r.get("images_count", 0) for r in results)

    log.info("=" * 50)
    log.info("Done: %d/%d succeeded, %d tables, %d images", success, len(results), total_tables, total_images)

    # Write log
    log_path = output_dir / "_extraction_log.json"
    log_path.write_text(
        json.dumps({"total": len(results), "success": success, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log.info("Log saved: %s", log_path)


if __name__ == "__main__":
    main()
