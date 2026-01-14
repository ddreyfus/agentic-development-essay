"""FastAPI entrypoint for document matching system."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.db import (
    fetch_all_audits,
    fetch_document,
    fetch_documents,
    init_db,
    insert_audit_event,
    insert_documents,
    insert_selection,
    clear_documents,
)
from app.services.ingestion import ingest_pdfs
from app.services.reporting import generate_report
from app.services.search import rank_documents

PDF_DIR = Path("pdfs")
REPORT_DIR = Path("reports")

app = FastAPI(title="Document Matcher", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.on_event("startup")
def startup() -> None:
    """Initialize resources on startup."""
    init_db()


def get_pdf_dir() -> Path:
    """Dependency for the PDF source directory."""
    return PDF_DIR


def get_report_dir() -> Path:
    """Dependency for the report output directory."""
    return REPORT_DIR


def get_document_or_404(document_id: int) -> dict[str, Any]:
    """Dependency that fetches a document or raises 404."""
    document = fetch_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return dict(document)


@app.post("/api/ingest", response_model=models.IngestResponse)
def ingest(pdf_dir: Path = Depends(get_pdf_dir)) -> models.IngestResponse:
    """Ingest PDFs and persist structured data."""
    if not pdf_dir.exists():
        raise HTTPException(status_code=404, detail="PDF directory not found")
    clear_documents()
    extracted = list(ingest_pdfs(pdf_dir))
    inserted = insert_documents([doc.__dict__ for doc in extracted])
    insert_audit_event(
        "ingest",
        {
            "count": inserted,
            "filenames": [doc.filename for doc in extracted],
        },
    )
    return models.IngestResponse(ingested=inserted)


@app.post("/api/search", response_model=models.SearchResponse)
def search(request: models.SearchRequest) -> models.SearchResponse:
    """Search for similar documents based on query."""
    documents = fetch_documents()
    candidates = rank_documents(request.query, documents)
    insert_audit_event(
        "search",
        {
            "query": request.query,
            "result_count": len(candidates),
            "document_ids": [candidate.document_id for candidate in candidates],
        },
    )
    return models.SearchResponse(
        candidates=[
            models.SearchCandidate(
                document_id=candidate.document_id,
                filename=candidate.filename,
                title=candidate.title,
                summary=candidate.summary,
                score=candidate.score,
                explanation=candidate.explanation,
            )
            for candidate in candidates
        ]
    )


@app.get("/api/documents/{document_id}", response_model=models.DocumentDetail)
def get_document(document: dict[str, Any] = Depends(get_document_or_404)) -> models.DocumentDetail:
    """Return document details for inspection."""
    return models.DocumentDetail(**document)


@app.post("/api/selection", response_model=models.SelectionResponse)
def confirm_selection(
    request: models.SelectionRequest,
) -> models.SelectionResponse:
    """Confirm a document as the final match."""
    document = fetch_document(request.document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    selection = insert_selection(request.document_id)
    insert_audit_event(
        "selection",
        {
            "document_id": request.document_id,
            "selection_id": selection["id"],
        },
    )
    return models.SelectionResponse(
        selection_id=selection["id"],
        document_id=request.document_id,
        created_at=selection["created_at"],
    )


@app.post("/api/report", response_model=models.ReportResponse)
def create_report(
    request: models.ReportRequest,
    report_dir: Path = Depends(get_report_dir),
) -> models.ReportResponse:
    """Generate a report for the confirmed document."""
    document = fetch_document(request.document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    report = generate_report(document, report_dir)
    insert_audit_event(
        "report_generation",
        {
            "document_id": request.document_id,
            "report_path": report.report_path,
        },
    )
    return models.ReportResponse(
        document_id=report.document_id,
        report_path=report.report_path,
        report_content=report.content,
    )


@app.get("/api/audit", response_model=models.AuditResponse)
def audit_log() -> models.AuditResponse:
    """Return audit events."""
    events = fetch_all_audits()
    parsed_events = [
        models.AuditEvent(
            id=event["id"],
            event_type=event["event_type"],
            details=json.loads(event["details"]),
            created_at=event["created_at"],
        )
        for event in events
    ]
    return models.AuditResponse(events=parsed_events)
