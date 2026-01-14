from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class RescanResponse(BaseModel):
    status: str


class DocumentSummary(BaseModel):
    id: int
    k_number: str
    document_name: str
    manufacturer_name: str
    regulatory_class: str


class DocumentListResponse(BaseModel):
    items: List[DocumentSummary]
    total: int


class DocumentDetail(BaseModel):
    id: int
    k_number: str
    document_name: str
    document_type: str
    manufacturer_name: str
    manufacturer_address: str
    regulation_number: str
    regulation_name: str
    regulatory_class: str
    product_codes: str
    indications_for_use: str
    full_text_excerpt: str


class MatchRequest(BaseModel):
    query: str


class MatchCandidate(BaseModel):
    document_id: int
    document_name: str
    k_number: str
    manufacturer_name: str
    score: float
    rationale: str


class MatchResponse(BaseModel):
    match_id: int
    candidates: List[MatchCandidate]


class MatchUpdateRequest(BaseModel):
    selected_document_id: int


class MatchUpdateResponse(BaseModel):
    id: int
    query_text: str
    selected_document_id: Optional[int]
    candidate_document_ids: List[int]
    created_at: str


class MatchHistoryItem(BaseModel):
    id: int
    created_at: str
    query_text: str
    selected_document_id: Optional[int]
    selected_document_name: Optional[str]
    selected_document_k_number: Optional[str]
    report_generated: bool


class MatchHistoryResponse(BaseModel):
    items: List[MatchHistoryItem]
    total: int


class ReportResponse(BaseModel):
    match_id: int
    markdown: str
    created_at: str


class UserCurrentResponse(BaseModel):
    client_name: str
    user_name: str
    user_email: str
    user_role: str


class ErrorResponse(BaseModel):
    error: str
