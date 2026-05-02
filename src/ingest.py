#!/usr/bin/env python3
"""
src/ingest.py – BIS SP-21 PDF Ingestion & Chunking Pipeline

Parses the BIS SP 21 PDF (Summaries of Indian Standards for Building Materials),
chunks the content intelligently, and builds a searchable index.

Usage:
    python src/ingest.py --pdf data/BIS_SP21.pdf --output data/chunks.json

Dependencies:
    pip install pdfplumber
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any


# ── Regex patterns for BIS standard headers ──────────────────────────────────
IS_HEADER_RE = re.compile(
    r"\b(IS\s*[\d]+(?:\s*[\(\-]\s*(?:PART|Part)\s*\d+\s*[\)\-])?)\b",
    re.IGNORECASE,
)

SECTION_HEADERS = ["scope", "material", "physical requirements", "chemical requirements",
                   "test", "sampling", "marking", "packing", "definitions"]


def _extract_text_pdfplumber(pdf_path: str) -> List[Dict]:
    """Extract text page by page using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        print("pdfplumber not installed. Run: pip install pdfplumber", file=sys.stderr)
        sys.exit(1)

    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            pages.append({"page": i, "text": text})
    return pages


def _chunk_by_standard(pages: List[Dict]) -> List[Dict]:
    """
    Chunk text so that each chunk corresponds to one BIS standard summary.
    Strategy: split on IS XXXX header occurrences.
    """
    full_text = "\n".join(p["text"] for p in pages)
    # Split on IS standard numbers
    parts = IS_HEADER_RE.split(full_text)

    chunks = []
    i = 1
    while i < len(parts) - 1:
        std_id = parts[i].strip()
        content = parts[i + 1] if i + 1 < len(parts) else ""
        # Trim to next IS header
        chunk_text = f"{std_id}\n{content.strip()[:2000]}"
        chunks.append({
            "chunk_id": f"chunk_{len(chunks)+1:04d}",
            "standard": std_id.upper().replace(" ", " "),
            "text": chunk_text,
            "char_len": len(chunk_text),
        })
        i += 2

    return chunks


def _sliding_window_chunks(pages: List[Dict], window: int = 512, overlap: int = 64) -> List[Dict]:
    """
    Fallback: sliding window chunking over full page text.
    """
    chunks = []
    for page in pages:
        text = page["text"]
        tokens = text.split()
        start = 0
        while start < len(tokens):
            end = min(start + window, len(tokens))
            chunk_text = " ".join(tokens[start:end])
            chunks.append({
                "chunk_id": f"p{page['page']}_c{len(chunks)+1:04d}",
                "page": page["page"],
                "text": chunk_text,
                "char_len": len(chunk_text),
            })
            if end == len(tokens):
                break
            start += window - overlap
    return chunks


def ingest(pdf_path: str, output_path: str, strategy: str = "by_standard") -> None:
    print(f"[ingest] Reading PDF: {pdf_path}")
    pages = _extract_text_pdfplumber(pdf_path)
    print(f"[ingest] Extracted {len(pages)} pages")

    if strategy == "by_standard":
        chunks = _chunk_by_standard(pages)
        print(f"[ingest] Created {len(chunks)} standard-based chunks")
    else:
        chunks = _sliding_window_chunks(pages)
        print(f"[ingest] Created {len(chunks)} sliding-window chunks")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"[ingest] Saved chunks to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="BIS SP-21 PDF Ingestion")
    parser.add_argument("--pdf", required=True, help="Path to BIS SP21 PDF")
    parser.add_argument("--output", default="data/chunks.json", help="Output chunks JSON")
    parser.add_argument("--strategy", choices=["by_standard", "sliding_window"],
                        default="by_standard", help="Chunking strategy")
    args = parser.parse_args()
    ingest(args.pdf, args.output, args.strategy)


if __name__ == "__main__":
    main()
