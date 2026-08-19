"""
Clarion - Member 2 Extraction Agent

This module takes SourceChunk objects produced by the ingestion stage
and extracts important product fields from their text.

Member 2 responsibilities:
- Read SourceChunk data
- Extract structured product fields
- Preserve the source reference
- Return extraction results for later stages
"""

from dataclasses import asdict, is_dataclass
from typing import Any

from ai.ingestion.schemas import SourceChunk


def source_ref_to_dict(source_ref: Any) -> dict:
    """
    Convert source_ref into a normal dictionary.

    Handles both:
    - SourceRef dataclass
    - dictionary
    """

    if isinstance(source_ref, dict):
        return source_ref

    if is_dataclass(source_ref):
        return asdict(source_ref)

    return {
        "value": str(source_ref)
    }


def extract_fields(chunks: list[SourceChunk]) -> list[dict]:
    """
    Extract important product fields from document chunks.

    Each extracted field keeps:
    - field name
    - extracted value
    - chunk ID
    - source reference
    """

    extracted = []

    for chunk in chunks:

        # Make sure the chunk text is available
        text = chunk.text if chunk.text else ""

        # Convert text to lowercase for easier searching
        text_lower = text.lower()

        # ---------------------------------------------------------
        # Rated Voltage
        # ---------------------------------------------------------
        if "rated voltage" in text_lower:

            extracted.append({
                "field": "rated_voltage",
                "value": text,
                "chunk_id": chunk.chunk_id,
                "source_ref": source_ref_to_dict(chunk.source_ref)
            })

        # ---------------------------------------------------------
        # Model Number
        # ---------------------------------------------------------
        if "model number" in text_lower:

            extracted.append({
                "field": "model_number",
                "value": text,
                "chunk_id": chunk.chunk_id,
                "source_ref": source_ref_to_dict(chunk.source_ref)
            })

        # ---------------------------------------------------------
        # Housing Material
        # ---------------------------------------------------------
        if "housing material" in text_lower:

            extracted.append({
                "field": "housing_material",
                "value": text,
                "chunk_id": chunk.chunk_id,
                "source_ref": source_ref_to_dict(chunk.source_ref)
            })

        # ---------------------------------------------------------
        # Size
        # ---------------------------------------------------------
        if "size" in text_lower:

            extracted.append({
                "field": "size",
                "value": text,
                "chunk_id": chunk.chunk_id,
                "source_ref": source_ref_to_dict(chunk.source_ref)
            })

        # ---------------------------------------------------------
        # Classification Code
        # ---------------------------------------------------------
        if "classification code" in text_lower:

            extracted.append({
                "field": "classification_code",
                "value": text,
                "chunk_id": chunk.chunk_id,
                "source_ref": source_ref_to_dict(chunk.source_ref)
            })

    return extracted


# ================================================================
# Test the Extraction Agent
# ================================================================

if __name__ == "__main__":

    print("Member 2 Extraction Agent started successfully.")

    # ------------------------------------------------------------
    # Create sample SourceChunk objects for testing
    # ------------------------------------------------------------

    from ai.ingestion.schemas import SourceRef

    test_chunks = [

        SourceChunk(
            chunk_id="chunk_001",
            text="Model Number: E2E",
            source_ref=SourceRef(
                doc_id="Test1",
                source_type="pdf",
                page=2
            ),
            source_quality="clean",
            chunk_type="text"
        ),

        SourceChunk(
            chunk_id="chunk_002",
            text="Rated Voltage: 230V",
            source_ref=SourceRef(
                doc_id="Test1",
                source_type="pdf",
                page=2
            ),
            source_quality="clean",
            chunk_type="text"
        ),

        SourceChunk(
            chunk_id="chunk_003",
            text="Housing material and shape: S",
            source_ref=SourceRef(
                doc_id="Test1",
                source_type="pdf",
                page=2
            ),
            source_quality="clean",
            chunk_type="table_row"
        ),

        SourceChunk(
            chunk_id="chunk_004",
            text="Size: 03",
            source_ref=SourceRef(
                doc_id="Test1",
                source_type="pdf",
                page=2
            ),
            source_quality="clean",
            chunk_type="table_row"
        ),

        SourceChunk(
            chunk_id="chunk_005",
            text="Classification Code: S",
            source_ref=SourceRef(
                doc_id="Test1",
                source_type="pdf",
                page=2
            ),
            source_quality="clean",
            chunk_type="table_row"
        )
    ]

    # ------------------------------------------------------------
    # Run extraction
    # ------------------------------------------------------------

    results = extract_fields(test_chunks)

    # ------------------------------------------------------------
    # Display results
    # ------------------------------------------------------------

    print("\nExtracted Fields:")
    print("-----------------")

    for result in results:
        print(result)