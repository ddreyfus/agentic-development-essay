from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.models.schemas import (
    DocumentDetail,
    DocumentListResponse,
    ErrorResponse,
    HealthResponse,
    MatchHistoryResponse,
    MatchRequest,
    MatchResponse,
    MatchUpdateRequest,
    MatchUpdateResponse,
    ReportResponse,
    RescanResponse,
    UserCurrentResponse,
)
from app.services.app_services import AppServices, create_services


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    services = create_services(settings)
    app.state.services = services
    services.ingest_service.ingest_all()
    services.watcher.start()
    try:
        yield
    finally:
        services.watcher.stop()
        services.conn.close()


app = FastAPI(lifespan=lifespan)


def get_services(request: Request) -> AppServices:
    return request.app.state.services


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/ingest/rescan", response_model=RescanResponse, status_code=202)
def ingest_rescan(services: AppServices = Depends(get_services)) -> RescanResponse:
    services.ingest_service.ingest_all()
    return RescanResponse(status="scheduled")


@app.get("/documents", response_model=DocumentListResponse)
def list_documents(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    services: AppServices = Depends(get_services),
) -> DocumentListResponse:
    data = services.document_service.list_documents(limit=limit, offset=offset)
    return DocumentListResponse(**data)


@app.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: int, services: AppServices = Depends(get_services)
) -> DocumentDetail:
    try:
        doc = services.document_service.get_document(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DocumentDetail(**doc)


@app.post("/match", response_model=MatchResponse)
def create_match(
    request: MatchRequest, services: AppServices = Depends(get_services)
) -> MatchResponse:
    result = services.matching_service.match(request.query)
    return MatchResponse(**result)


@app.put("/matches/{match_id}", response_model=MatchUpdateResponse)
def update_match(
    match_id: int,
    request: MatchUpdateRequest,
    services: AppServices = Depends(get_services),
) -> MatchUpdateResponse:
    try:
        result = services.matching_service.confirm_match(match_id, request.selected_document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return MatchUpdateResponse(**result)


@app.get("/matches", response_model=MatchHistoryResponse)
def list_matches(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    services: AppServices = Depends(get_services),
) -> MatchHistoryResponse:
    data = services.history_service.list_matches(limit=limit, offset=offset)
    return MatchHistoryResponse(**data)


@app.get("/matches/{match_id}/report", response_model=ReportResponse)
def get_report(
    match_id: int, services: AppServices = Depends(get_services)
) -> ReportResponse:
    try:
        report = services.report_workflow.generate(match_id)
    except ValueError as exc:
        message = str(exc)
        status_code = 400 if "no selected" in message else 404
        raise HTTPException(status_code=status_code, detail=message) from exc
    return ReportResponse(**report)


@app.get("/user/current", response_model=UserCurrentResponse)
def user_current(services: AppServices = Depends(get_services)) -> UserCurrentResponse:
    identity = services.user_service.current_user()
    return UserCurrentResponse(**identity)


@app.exception_handler(HTTPException)
def http_exception_handler(_, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content=ErrorResponse(error=exc.detail).model_dump())


static_dir = Path(settings.static_dir)
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
