"""
Clarion - Main API Routes (Member 3)

Provides REST endpoints for upload, pipeline orchestration, catalog records,
traceability receipts, human-in-the-loop review actions, catalog outlier detection,
and structured export.
"""

from __future__ import annotations

import io
import shutil
import uuid
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse, Response, StreamingResponse
from pydantic import BaseModel

from backend.pipeline_engine import PipelineEngine, PROJECT_ROOT, UPLOAD_DIR
from backend.catalog_consistency import CatalogConsistencyChecker


api_router = APIRouter(prefix="/api", tags=["clarion-core"])
engine = PipelineEngine()


# -------------------------------------------------------------
# Request Schemas
# -------------------------------------------------------------

class FieldReviewDecision(BaseModel):
    record_id: str
    field_name: str
    action: Literal["approve", "override"]
    custom_value: str | None = None


class ConflictResolution(BaseModel):
    conflict_id: str
    resolution: Literal["choose_a", "choose_b", "custom"]
    custom_value: str | None = None


# -------------------------------------------------------------
# Ingestion & Upload Endpoints
# -------------------------------------------------------------

@api_router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Uploads a PDF datasheet, CSV dataset, or product image and triggers processing."""
    filename = file.filename or "upload"
    ext = Path(filename).suffix.lower()

    if ext not in {".pdf", ".csv", ".jpg", ".jpeg", ".png"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a .pdf datasheet, .csv dataset, or product image (.jpg, .png)."
        )

    doc_id = f"doc_{uuid.uuid4().hex[:8]}"
    saved_name = f"{doc_id}_{filename}"
    file_path = UPLOAD_DIR / saved_name

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if ext == ".pdf":
        record = engine.process_pdf(str(file_path), doc_id=doc_id)
        return {
            "ok": True,
            "message": "PDF uploaded, parsed, and extracted successfully.",
            "doc_id": doc_id,
            "filename": filename,
            "record": record.to_dict(),
        }
    elif ext == ".csv":
        records = engine.process_csv_dataset(str(file_path), max_rows=50)
        return {
            "ok": True,
            "message": f"CSV dataset uploaded and processed {len(records)} records.",
            "doc_id": doc_id,
            "filename": filename,
            "record_count": len(records),
        }
    else:
        return {
            "ok": True,
            "message": "Product image uploaded.",
            "doc_id": doc_id,
            "filename": filename,
        }


@api_router.post("/pipeline/run-sample")
def run_sample_pipeline():
    """Runs the full Clarion truth layer on sample PDFs and UniHack sample dataset."""
    sample_pdf1 = PROJECT_ROOT / "data" / "samples" / "Test1.pdf"
    sample_pdf4 = PROJECT_ROOT / "data" / "samples" / "Test4.pdf"
    sample_csv = PROJECT_ROOT / "data" / "samples" / "Unihack_Sample_Dataset_Input.csv"

    processed_records = []
    if sample_pdf1.exists():
        rec1 = engine.process_pdf(str(sample_pdf1), doc_id="Test1_Datasheet")
        processed_records.append(rec1.to_dict())

    if sample_pdf4.exists():
        rec4 = engine.process_pdf(str(sample_pdf4), doc_id="Test4_Datasheet")
        processed_records.append(rec4.to_dict())

    if sample_csv.exists():
        csv_recs = engine.process_csv_dataset(str(sample_csv), max_rows=30)
        processed_records.extend([r.to_dict() for r in csv_recs])

    return {
        "ok": True,
        "message": f"Pipeline processed {len(processed_records)} product records from sample assets.",
        "record_count": len(processed_records),
    }


@api_router.get("/pipeline/status")
def get_pipeline_status():
    """Returns overall telemetry, record statistics, review queue items, and outlier flags."""
    records = engine.records
    total_records = len(records)
    auto_published = sum(1 for r in records if r.publication_status == "auto_published")
    needs_review = sum(1 for r in records if r.publication_status == "needs_review")
    human_confirmed = sum(1 for r in records if r.publication_status == "human_confirmed")

    pending_conflicts = [c for c in engine.conflicts if c.status == "pending_review"]
    pending_fields = []
    for r in records:
        for fname, fv in r.fields.items():
            if fv.status == "needs_review":
                pending_fields.append({
                    "record_id": r.record_id,
                    "product_name": r.product_name,
                    "field_name": fname,
                    "raw_value": fv.raw_value,
                    "normalized_value": fv.normalized_value,
                    "confidence": fv.confidence.to_dict(),
                    "source_ref": fv.source_ref,
                })

    anomalies = engine.checker.detect_outliers()

    return {
        "ok": True,
        "status": "operational",
        "pipeline_stages": [
            {"name": "Ingestion Agent", "status": "active", "member": "Member 1 (Gitika)"},
            {"name": "Product Identity Resolver", "status": "active", "member": "Member 1"},
            {"name": "Extraction Agent", "status": "active", "member": "Member 2"},
            {"name": "Normalization & Taxonomy", "status": "active", "member": "Member 2 / 3"},
            {"name": "Verification & Domain Sanity", "status": "active", "member": "Member 2 / 3"},
            {"name": "Conflict Detector", "status": "active", "member": "Member 2 / 3"},
            {"name": "Enrichment Agent", "status": "active", "member": "Member 2"},
            {"name": "4-Factor Confidence & Trust Scoring", "status": "active", "member": "Member 2 / 3"},
            {"name": "Catalog Consistency (Outlier Detection)", "status": "active", "member": "Member 3"},
            {"name": "Structured Export (UniHack 252-col & JSON)", "status": "active", "member": "Member 3"},
        ],
        "metrics": {
            "total_records": total_records,
            "auto_published": auto_published,
            "needs_review": needs_review,
            "human_confirmed": human_confirmed,
            "pending_conflicts": len(pending_conflicts),
            "pending_fields": len(pending_fields),
            "outlier_count": len(anomalies),
            "avg_trust_score": round(sum(r.trust_score for r in records) / max(total_records, 1), 2),
        },
    }


# -------------------------------------------------------------
# Records & Catalog Endpoints
# -------------------------------------------------------------

@api_router.get("/records")
def list_records(
    search: str = Query("", description="Search term"),
    category: str = Query("", description="Category filter"),
    status: str = Query("", description="Status filter"),
    limit: int = Query(100, ge=1, le=500),
):
    """Lists structured product records with optional search and filtering."""
    results = engine.records

    if search:
        s = search.lower()
        results = [
            r for r in results
            if s in r.product_name.lower()
            or s in r.mfg_part_num.lower()
            or s in r.manufacturer.lower()
            or s in r.brand.lower()
            or any(s in str(fv.normalized_value).lower() for fv in r.fields.values())
        ]

    if category:
        results = [r for r in results if r.category.lower() == category.lower()]

    if status:
        results = [r for r in results if r.publication_status == status]

    return {
        "ok": True,
        "count": len(results),
        "records": [r.to_dict() for r in results[:limit]],
    }


@api_router.get("/records/{record_id}")
def get_record(record_id: str):
    """Retrieves a single product record with all field citations and metadata."""
    record = next((r for r in engine.records if r.record_id == record_id), None)
    if not record:
        raise HTTPException(status_code=404, detail="Product record not found.")
    return {"ok": True, "record": record.to_dict()}


@api_router.delete("/records/{record_id}")
def delete_record(record_id: str):
    """Deletes a product record."""
    initial_len = len(engine.records)
    engine.records = [r for r in engine.records if r.record_id != record_id]
    if len(engine.records) == initial_len:
        raise HTTPException(status_code=404, detail="Product record not found.")
    engine._save_records()
    engine._run_outlier_check()
    return {"ok": True, "message": f"Record {record_id} deleted."}


@api_router.post("/records/clear")
def clear_all_records():
    """Clears all stored product records and conflicts."""
    engine.records = []
    engine.conflicts = []
    engine._save_records()
    engine._save_conflicts()
    return {"ok": True, "message": "All records and conflicts cleared."}


# -------------------------------------------------------------
# Traceability & Receipts Endpoint
# -------------------------------------------------------------

@api_router.get("/receipts/{record_id}/{field_name}")
def get_field_receipt(record_id: str, field_name: str):
    """
    Returns exact citation, source chunk, page/paragraph/bbox,
    and the 4-factor confidence score breakdown for an extracted field.
    """
    record = next((r for r in engine.records if r.record_id == record_id), None)
    if not record:
        raise HTTPException(status_code=404, detail="Product record not found.")

    if field_name not in record.fields:
        raise HTTPException(status_code=404, detail=f"Field '{field_name}' not found on record.")

    fv = record.fields[field_name]
    return {
        "ok": True,
        "receipt": {
            "record_id": record.record_id,
            "product_name": record.product_name,
            "field_name": field_name,
            "raw_value": fv.raw_value,
            "normalized_value": fv.normalized_value,
            "status": fv.status,
            "source_ref": fv.source_ref,
            "source_snippet": fv.source_snippet,
            "chunk_id": fv.chunk_id,
            "source_quality": fv.source_quality,
            "confidence_breakdown": fv.confidence.to_dict(),
            "explainability": fv.confidence.explainability,
            "human_override": fv.human_override,
        }
    }


# -------------------------------------------------------------
# Human-in-the-Loop Review Endpoints
# -------------------------------------------------------------

@api_router.get("/review/fields")
def list_pending_fields():
    """Lists low-confidence fields across all records requiring human review."""
    pending = []
    for r in engine.records:
        for fname, fv in r.fields.items():
            if fv.status == "needs_review":
                pending.append({
                    "record_id": r.record_id,
                    "product_name": r.product_name,
                    "field_name": fname,
                    "raw_value": fv.raw_value,
                    "normalized_value": fv.normalized_value,
                    "confidence": fv.confidence.to_dict(),
                    "source_ref": fv.source_ref,
                    "source_snippet": fv.source_snippet,
                    "source_quality": fv.source_quality,
                })
    return {"ok": True, "count": len(pending), "fields": pending}


@api_router.post("/review/fields/decide")
def decide_field_review(decision: FieldReviewDecision):
    """Approves or manually overrides a low-confidence field."""
    record = engine.resolve_field_review(
        record_id=decision.record_id,
        field_name=decision.field_name,
        action=decision.action,
        custom_value=decision.custom_value,
    )
    if not record:
        raise HTTPException(status_code=404, detail="Record or field not found.")
    return {"ok": True, "message": "Field decision saved.", "record": record.to_dict()}


@api_router.get("/review/conflicts")
def list_conflicts():
    """Lists cross-document disagreements where two sources provide differing values."""
    pending = [c.to_dict() for c in engine.conflicts if c.status == "pending_review"]
    resolved = [c.to_dict() for c in engine.conflicts if c.status != "pending_review"]
    return {
        "ok": True,
        "pending_count": len(pending),
        "pending_conflicts": pending,
        "resolved_conflicts": resolved,
    }


@api_router.post("/review/conflicts/resolve")
def resolve_conflict(body: ConflictResolution):
    """Resolves a cross-source conflict by picking Source A, Source B, or entering custom value."""
    conflict = engine.resolve_conflict(
        conflict_id=body.conflict_id,
        resolution=body.resolution,
        custom_value=body.custom_value,
    )
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found.")
    return {"ok": True, "message": "Conflict resolved.", "conflict": conflict.to_dict()}


# -------------------------------------------------------------
# Catalog Consistency & Outlier Detection Endpoints
# -------------------------------------------------------------

@api_router.get("/catalog/outliers")
def get_catalog_outliers(z_threshold: float = Query(2.5, ge=1.0, le=5.0)):
    """Runs statistical outlier detection across all catalog records."""
    engine.checker.set_records([r.to_dict() for r in engine.records])
    anomalies = engine.checker.detect_outliers(z_threshold=z_threshold)
    return {
        "ok": True,
        "count": len(anomalies),
        "z_threshold": z_threshold,
        "anomalies": [a.to_dict() for a in anomalies],
    }


@api_router.get("/catalog/stats/{field_name}")
def get_field_statistics(field_name: str):
    """Returns distribution metrics (mean, std, IQR, Q1, Q3) for a numeric field."""
    engine.checker.set_records([r.to_dict() for r in engine.records])
    stats = engine.checker.compute_field_statistics(field_name)
    return {"ok": True, "stats": stats}


# -------------------------------------------------------------
# Structured Export Endpoints
# -------------------------------------------------------------

@api_router.get("/export/csv")
def export_csv(format: str = Query("unihack", enum=["unihack", "standard"])):
    """Exports product records as CSV (UniHack 252-column or standard format)."""
    csv_content = engine.export_unihack_csv()
    filename = "Clarion_UniHack_Delivery_Format.csv" if format == "unihack" else "Clarion_Catalog_Export.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@api_router.get("/export/json")
def export_json():
    """Exports all product records with complete field citations in JSON format."""
    records_json = engine.export_json()
    return JSONResponse(
        content=records_json,
        headers={"Content-Disposition": 'attachment; filename="Clarion_Product_Catalog.json"'},
    )
