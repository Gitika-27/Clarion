"""
Runs identity resolution across a set of ingested documents and writes the
proposals to a JSON file. Person 3's UI reads this file to build the
Merge / Keep separate review screen.
"""

import json
import os
from itertools import combinations
from identity_resolver import propose_match


def generate_identity_proposals(documents: list[dict], output_path: str) -> list[dict]:
    """
    documents: list of {"doc_id": str, "product_name": str}
    Compares every pair and writes out only the pairs that look like a
    possible match -- this is what gets shown to a human for confirmation.
    """
    proposals = []

    for doc_a, doc_b in combinations(documents, 2):
        result = propose_match(
            doc_a["doc_id"], doc_a["product_name"],
            doc_b["doc_id"], doc_b["product_name"],
        )
        if result.proposed_match:
            proposals.append({
                "doc_id_a": result.doc_id_a,
                "doc_id_b": result.doc_id_b,
                "raw_name_a": result.raw_name_a,
                "raw_name_b": result.raw_name_b,
                "similarity": result.similarity,
                "status": "pending_review",  # Person 3's UI changes this to "merged" / "kept_separate"
            })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(proposals, f, indent=2)

    print(f"Wrote {len(proposals)} identity proposal(s) to {output_path}")
    return proposals


if __name__ == "__main__":
    # Example with fake data -- replace with real extracted product names
    # once Person 2's extraction is producing them
    test_documents = [
        {"doc_id": "doc1", "product_name": "E2E-C03SR8"},
        {"doc_id": "doc2", "product_name": "Omron E2E C03SR8 Sensor"},
        {"doc_id": "doc3", "product_name": "E2E-C06S02"},
    ]
    generate_identity_proposals(test_documents, output_path="../../data/processed/identity_proposals.json")