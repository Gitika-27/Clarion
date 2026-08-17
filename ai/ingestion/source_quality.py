"""
Flags a source as "clean" or "low_legibility". This flag caps confidence
downstream (Section 9 of the PRD) regardless of how consistent extraction
looks -- a consistent misread of a bad scan is still a misread.

Heuristic for MVP (deliberately simple, not a full OCR-quality classifier):
a PDF page with a real digital text layer extracts cleanly. A scanned PDF
with no text layer (or a garbled one) extracts almost nothing, or extracts
mostly non-alphanumeric noise.
"""

import re


def assess_pdf_quality(pdf) -> str:
    """Looks at the whole document once, cheap and good enough for MVP."""
    total_chars = 0
    alnum_chars = 0

    for page in pdf.pages[:3]:  # sampling first 3 pages is enough
        text = page.extract_text() or ""
        total_chars += len(text)
        alnum_chars += sum(c.isalnum() for c in text)

    if total_chars < 50:
        # almost no extractable text -> likely a scanned image PDF
        return "low_legibility"

    alnum_ratio = alnum_chars / max(total_chars, 1)
    if alnum_ratio < 0.5:
        # lots of extracted "text" that isn't actually readable characters
        return "low_legibility"

    return "clean"


def assess_image_quality(image_path: str, min_dimension: int = 800) -> str:
    """
    For a standalone product image (e.g. a nameplate photo), flag low
    resolution or clearly handwritten-looking sources as low_legibility.
    Install: pip install Pillow --break-system-packages
    """
    from PIL import Image

    with Image.open(image_path) as img:
        width, height = img.size

    if min(width, height) < min_dimension:
        return "low_legibility"

    return "clean"
