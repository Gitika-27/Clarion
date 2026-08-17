"""
Prepares a product image for the Extraction Agent. This does NOT read the
image's content -- that happens later in Person 2's Extraction Agent using
a vision model. Your job is only to: load the image, flag its quality,
encode it, and wrap it in the shared SourceChunk format.

Install: pip install Pillow --break-system-packages
"""

import base64
from PIL import Image
from schemas import SourceChunk, SourceRef
from source_quality import assess_image_quality


def parse_image(image_path: str, doc_id: str) -> list[SourceChunk]:
    quality = assess_image_quality(image_path)

    with Image.open(image_path) as img:
        width, height = img.size

    with open(image_path, "rb") as f:
        image_bytes = f.read()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    chunk = SourceChunk(
        chunk_id=f"{doc_id}_c1",
        text="",  # empty on purpose -- nothing has "read" the image yet
        source_ref=SourceRef(
            doc_id=doc_id,
            source_type="image",
            bbox=[0, 0, width, height],  # whole image, for now
        ),
        source_quality=quality,
        chunk_type="image",
        image_data=image_b64,
    )

    return [chunk]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python image_handler.py <path_to_image>")
        sys.exit(1)

    result = parse_image(sys.argv[1], doc_id="test_image_1")
    for c in result:
        print(f"quality={c.source_quality}")
        print(f"bbox={c.source_ref.bbox}")
        print(f"image_data length={len(c.image_data)} characters (this is normal -- it's the full encoded image)")