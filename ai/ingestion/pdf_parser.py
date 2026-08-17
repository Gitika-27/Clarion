"""
Parses a PDF into SourceChunks: text paragraphs + table rows, each tagged
with its page number so every downstream field can cite exactly where it
came from.

Install: pip install pdfplumber --break-system-packages
"""

import pdfplumber
from schemas import SourceChunk, SourceRef
from source_quality import assess_pdf_quality


def parse_pdf(pdf_path: str, doc_id: str) -> list[SourceChunk]:
    chunks = []
    chunk_counter = 0

    with pdfplumber.open(pdf_path) as pdf:
        quality = assess_pdf_quality(pdf)  # "clean" or "low_legibility"

        for page_num, page in enumerate(pdf.pages, start=1):
            # --- text paragraphs ---
            text = page.extract_text() or ""
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            for para_num, para in enumerate(paragraphs, start=1):
                chunk_counter += 1
                chunks.append(SourceChunk(
                    chunk_id=f"{doc_id}_c{chunk_counter}",
                    text=para,
                    source_ref=SourceRef(
                        doc_id=doc_id, source_type="pdf",
                        page=page_num, paragraph=para_num
                    ),
                    source_quality=quality,
                    chunk_type="text",
                ))

            # --- tables (specs are often in tables, not prose) ---
            for table in page.extract_tables():
                for row in table:
                    row_text = " | ".join(cell or "" for cell in row)
                    meaningful_chars = row_text.replace("|", "").strip()
                    if len(meaningful_chars) < 4:
                        continue
                    chunk_counter += 1
                    chunks.append(SourceChunk(
                        chunk_id=f"{doc_id}_c{chunk_counter}",
                        text=row_text,
                        source_ref=SourceRef(
                            doc_id=doc_id, source_type="pdf", page=page_num
                        ),
                        source_quality=quality,
                        chunk_type="table_row",
                    ))

    return chunks


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pdf_parser.py <path_to_pdf>")
        sys.exit(1)

    result = parse_pdf(sys.argv[1], doc_id="test_doc_1")
    print(f"Extracted {len(result)} chunks:\n")
    for c in result[:5]:
        print(f"[{c.chunk_type}] page {c.source_ref.page}: {c.text[:80]}")
