"""Member 3 identity-proposal review API and review-page route."""

import json
import os
import tempfile
import threading
from hashlib import sha256
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


PROJECT_ROOT = Path(__file__).resolve().parent.parent
IDENTITY_PROPOSALS_PATH = PROJECT_ROOT / "data" / "processed" / "identity_proposals.json"
REVIEW_PAGE_PATH = Path(__file__).resolve().parent / "static" / "identity_review.html"
ALLOWED_STATUSES = {"pending_review", "merged", "kept_separate"}
_store_lock = threading.Lock()

identity_router = APIRouter(tags=["identity-review"])


def proposal_id_for(doc_id_a: str, doc_id_b: str) -> str:
    """Create a deterministic ID while keeping the shared proposal schema unchanged."""
    pair = "|".join(sorted((str(doc_id_a), str(doc_id_b))))
    return f"proposal_{sha256(pair.encode('utf-8')).hexdigest()[:16]}"


def _validate_proposal(proposal: Any) -> dict[str, Any]:
    if not isinstance(proposal, dict):
        raise ValueError("Each proposal must be an object.")

    required = ("doc_id_a", "doc_id_b", "raw_name_a", "raw_name_b", "similarity", "status")
    if any(field not in proposal for field in required):
        raise ValueError("A proposal is missing required fields.")
    if proposal["status"] not in ALLOWED_STATUSES:
        raise ValueError("A proposal has an unsupported status.")
    if not isinstance(proposal["similarity"], (int, float)):
        raise ValueError("Proposal similarity must be numeric.")

    copy = dict(proposal)
    copy.setdefault("proposal_id", proposal_id_for(copy["doc_id_a"], copy["doc_id_b"]))
    return copy


def _load_proposals() -> list[dict[str, Any]]:
    if not IDENTITY_PROPOSALS_PATH.exists():
        return []
    try:
        with IDENTITY_PROPOSALS_PATH.open(encoding="utf-8") as file:
            payload = json.load(file)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail="Identity proposal storage is malformed.") from exc

    if not isinstance(payload, list):
        raise HTTPException(status_code=500, detail="Identity proposal storage must contain a list.")
    try:
        return [_validate_proposal(proposal) for proposal in payload]
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=f"Invalid identity proposal storage: {exc}") from exc


def _write_proposals(proposals: list[dict[str, Any]]) -> None:
    IDENTITY_PROPOSALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=IDENTITY_PROPOSALS_PATH.parent,
            prefix="identity_proposals_", suffix=".tmp", delete=False,
        ) as file:
            temp_name = file.name
            json.dump(proposals, file, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_name, IDENTITY_PROPOSALS_PATH)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)


def _find_proposal(proposals: list[dict[str, Any]], proposal_id: str) -> dict[str, Any]:
    for proposal in proposals:
        if proposal["proposal_id"] == proposal_id:
            return proposal
    raise HTTPException(status_code=404, detail="Identity proposal not found.")


@identity_router.get("/api/identity/proposals")
def list_pending_proposals() -> list[dict[str, Any]]:
    with _store_lock:
        return [proposal for proposal in _load_proposals() if proposal["status"] == "pending_review"]


@identity_router.get("/api/identity/proposals/{proposal_id}")
def get_proposal(proposal_id: str) -> dict[str, Any]:
    with _store_lock:
        return _find_proposal(_load_proposals(), proposal_id)


def _decide(proposal_id: str, decision: str) -> dict[str, Any]:
    with _store_lock:
        proposals = _load_proposals()
        proposal = _find_proposal(proposals, proposal_id)
        if proposal["status"] != "pending_review":
            raise HTTPException(status_code=409, detail="This proposal has already been reviewed.")
        proposal["status"] = decision
        _write_proposals(proposals)
        return proposal


@identity_router.post("/api/identity/proposals/{proposal_id}/merge")
def merge_proposal(proposal_id: str) -> dict[str, Any]:
    return _decide(proposal_id, "merged")


@identity_router.post("/api/identity/proposals/{proposal_id}/keep-separate")
def keep_separate(proposal_id: str) -> dict[str, Any]:
    return _decide(proposal_id, "kept_separate")


@identity_router.get("/identity-review", include_in_schema=False)
def identity_review_page() -> FileResponse:
    return FileResponse(REVIEW_PAGE_PATH, media_type="text/html")
