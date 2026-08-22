"""
Clarion - Multi-Agent Industrial Product Truth Layer
FastAPI Application Entrypoint (Member 3)
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.identity_routes import identity_router
from backend.api_routes import api_router


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"
INDEX_HTML_PATH = STATIC_DIR / "index.html"


app = FastAPI(
    title="Clarion API & Truth Layer",
    description="Multi-Agent Industrial Product Data Intelligence Platform with complete field traceability, 4-factor confidence scoring, and human review routing.",
    version="1.0.0",
)

# Enable CORS for local development and web integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(identity_router)
app.include_router(api_router)

# Mount Static assets if needed
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def serve_dashboard():
    """Serves the Clarion Executive Truth Layer Dashboard."""
    if INDEX_HTML_PATH.exists():
        return FileResponse(INDEX_HTML_PATH, media_type="text/html")
    return {"name": "Clarion API", "status": "running"}


@app.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "clarion-api"}
