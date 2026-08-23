
import os
import json
from dataclasses import asdict, is_dataclass
from typing import Any

from ai.ingestion.schemas import SourceChunk

try:
    from groq import Groq
    _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    _GROQ_AVAILABLE = True
except Exception:
    _GROQ_AVAILABLE = False

MODEL = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """You extract structured product fields from a fragment of an \
industrial product datasheet. Given the text, identify any real product \
attributes present (e.g. rated_voltage, model_number, housing_material, size, \
classification_code, or any other clearly stated spec). Rules:
- Only extract what's actually stated in the text -- never invent values.
- If nothing meaningful is present, return an empty list.
- Respond with ONLY a JSON object, no other text, no code fences.
Format: {"fields": [{"field": "snake_case_name", "value": "extracted value"}]}
"""


def source_ref_to_dict(source_ref: Any) -> dict:
    if isinstance(source_ref, dict):
        return source_ref
    if is_dataclass(source_ref):
        return asdict(source_ref)
    return {"value": str(source_ref)}


def _keyword_fallback(text: str) -> list[dict]:
    """Safety net only -- used if the live API call fails."""
    text_lower = text.lower()
    found = []
    checks = {
        "rated_voltage": "rated voltage",
        "model_number": "model number",
        "housing_material": "housing material",
        "size": "size",
        "classification_code": "classification code",
    }
    for field_name, keyword in checks.items():
        if keyword in text_lower:
            found.append({"field": field_name, "value": text})
    return found


def _extract_from_chunk_dynamic(text: str) -> list[dict]:
    response = _client.chat.completions.create(
        model=MODEL,
        max_tokens=512,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(raw)
    return parsed.get("fields", [])


def extract_fields(chunks: list[SourceChunk]) -> list[dict]:
    """
    Extracts product fields from document chunks using a live LLM call per
    chunk. Skips chunks with negligible text. Falls back to keyword matching
    only if the API call itself errors out.
    """
    extracted = []

    for chunk in chunks:
        text = (chunk.text or "").strip()
        if len(text) < 8:
            continue  # nothing meaningful to extract from a near-empty chunk

        if _GROQ_AVAILABLE:
            try:
                found_fields = _extract_from_chunk_dynamic(text)
            except Exception:
                found_fields = _keyword_fallback(text)
        else:
            found_fields = _keyword_fallback(text)

        for f in found_fields:
            extracted.append({
                "field": f.get("field", "unknown_field"),
                "value": f.get("value", text),
                "chunk_id": chunk.chunk_id,
                "source_ref": source_ref_to_dict(chunk.source_ref),
            })

    return extracted