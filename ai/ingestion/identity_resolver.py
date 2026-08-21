"""
Rule-based identity resolution: decides whether two documents' product
names/model numbers likely refer to the same product. Never auto-merges --
produces a proposal that Person 3's UI shows the human for confirmation.
"""

import re
from difflib import SequenceMatcher
from ai.ingestion.schemas import IdentityMatchProposal

SIMILARITY_THRESHOLD = 0.85


def normalize(name: str) -> str:
    """'HP-500' / 'HP500' / 'Hydraulic Pump HP 500' -> comparable form."""
    name = name.lower()
    name = re.sub(r"[^a-z0-9]", "", name)  # strip spaces, hyphens, punctuation
    return name


def propose_match(doc_id_a: str, name_a: str, doc_id_b: str, name_b: str) -> IdentityMatchProposal:
    norm_a = normalize(name_a)
    norm_b = normalize(name_b)

    ratio_similarity = SequenceMatcher(None, norm_a, norm_b).ratio()

    # Containment check: catches "HP500" inside "HydraulicPumpHP500", which
    # a plain ratio badly underscores since the strings differ a lot in length.
    shorter, longer = sorted([norm_a, norm_b], key=len)
    contains_match = len(shorter) >= 4 and shorter in longer

    similarity = 1.0 if contains_match else ratio_similarity

    return IdentityMatchProposal(
        doc_id_a=doc_id_a,
        doc_id_b=doc_id_b,
        raw_name_a=name_a,
        raw_name_b=name_b,
        normalized_name_a=norm_a,
        normalized_name_b=norm_b,
        similarity=round(similarity, 3),
        proposed_match=similarity >= SIMILARITY_THRESHOLD,
    )


if __name__ == "__main__":
    # quick sanity test
    examples = [
        ("HP-500", "HP500"),
        ("HP-500", "Hydraulic Pump HP 500"),
        ("HP-500", "HP-700"),  # should NOT match
    ]
    for name_a, name_b in examples:
        result = propose_match("docA", name_a, "docB", name_b)
        print(f"{name_a!r} vs {name_b!r} -> similarity={result.similarity}, match={result.proposed_match}")
