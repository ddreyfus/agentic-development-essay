"""Pydantic models for API requests/responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    """Response for PDF ingestion."""

    ingested: int = Field(..., ge=0)


class SearchRequest(BaseModel):
    """Request payload for similarity search."""

    query: str = Field(..., min_length=1)


class SearchCandidate(BaseModel):
    """Search result candidate."""

    document_id: int
    filename: str
    title: str
    summary: str
    score: float
    explanation: str


class SearchResponse(BaseModel):
    """Response for similarity search."""

    candidates: list[SearchCandidate]


class DocumentDetail(BaseModel):
    """Document details."""

    id: int
    filename: str
    title: str
    content: str
    summary: str
    page_count: int
    word_count: int
    created_at: str


class SelectionRequest(BaseModel):
    """Request payload for confirming selection."""

    document_id: int


class SelectionResponse(BaseModel):
    """Response for confirmed selection."""

    selection_id: int
    document_id: int
    created_at: str


class ReportRequest(BaseModel):
    """Request payload for report generation."""

    document_id: int


class ReportResponse(BaseModel):
    """Response for report generation."""

    document_id: int
    report_path: str
    report_content: str


class AuditEvent(BaseModel):
    """Audit event representation."""

    id: int
    event_type: str
    details: dict[str, Any]
    created_at: str


class AuditResponse(BaseModel):
    """Response wrapper for audit list."""

    events: list[AuditEvent]
