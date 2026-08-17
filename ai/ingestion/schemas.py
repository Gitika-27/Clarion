"""
Shared data contract for Clarion's ingestion output.

IMPORTANT: This file is the interface between your work (ingestion) and
Person 2's work (extraction). Push this file FIRST, even before your
parsing logic is done, so Person 2 can start building against it without
waiting for you.
"""

from dataclasses import dataclass, field, asdict
from typing import Literal, Optional
import json


@dataclass
class SourceRef:
    """Points to exactly where a piece of text/image came from."""
    doc_id: str
    source_type: Literal["pdf", "image"]
    page: Optional[int] = None          # for PDFs
    paragraph: Optional[int] = None     # for PDFs
    bbox: Optional[list] = None         # for images: [x, y, w, h]


@dataclass
class SourceChunk:
    """
    One unit of extracted content, ready for the Extraction Agent to read.
    A single document produces many of these.
    """
    chunk_id: str
    text: str                                   # extracted text (empty for pure images)
    source_ref: SourceRef
    source_quality: Literal["clean", "low_legibility"]
    chunk_type: Literal["text", "table_row", "image"]
    image_data: Optional[str] = None

    def to_dict(self):
        d = asdict(self)
        return d


@dataclass
class IdentityMatchProposal:
    """
    Output of the identity resolver when two documents look like they
    describe the same product. This does NOT auto-merge -- it's shown
    to a human (Person 3's UI) for Merge / Keep separate.
    """
    doc_id_a: str
    doc_id_b: str
    raw_name_a: str
    raw_name_b: str
    normalized_name_a: str
    normalized_name_b: str
    similarity: float          # 0.0-1.0
    proposed_match: bool       # True if similarity crosses your threshold


def chunks_to_json(chunks: list[SourceChunk]) -> str:
    """Serialize a list of chunks for handoff to the extraction stage."""
    return json.dumps([c.to_dict() for c in chunks], indent=2)
