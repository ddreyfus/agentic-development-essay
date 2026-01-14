from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.db import apply_schema, get_connection
from app.repositories.document_repository import DocumentRepository
from app.services.audit import AuditLogger
from app.services.documents import DocumentService
from app.services.extraction import ExtractionService
from app.services.history import MatchHistoryService
from app.services.ingest import PdfIngestService
from app.services.matching import MatchingService
from app.services.rationale import RationaleService
from app.services.report import ReportService
from app.services.reporting import ReportWorkflow
from app.services.search import SearchBackend
from app.services.user import UserService
from app.services.watcher import Watcher


@dataclass
class AppServices:
    conn: object
    repository: DocumentRepository
    audit_logger: AuditLogger
    extraction_service: ExtractionService
    ingest_service: PdfIngestService
    search_backend: SearchBackend
    matching_service: MatchingService
    document_service: DocumentService
    history_service: MatchHistoryService
    report_workflow: ReportWorkflow
    user_service: UserService
    watcher: Watcher


def create_services(settings: Settings) -> AppServices:
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(settings.db_path)
    apply_schema(conn, Path(__file__).parents[1] / "schema.sql")
    repo = DocumentRepository(conn)
    rules = repo.list_parsing_rules(client_id=1)
    extraction_service = ExtractionService(ExtractionService.load_rules(rules))
    audit_logger = AuditLogger(repo)
    ingest_service = PdfIngestService(
        repo, extraction_service, audit_logger, pdf_dir=settings.pdf_dir
    )
    search_backend = SearchBackend(conn)
    rationale_service = RationaleService()
    matching_service = MatchingService(repo, search_backend, rationale_service, audit_logger)
    document_service = DocumentService(repo)
    history_service = MatchHistoryService(repo)
    report_renderer = ReportService(str(Path(__file__).parents[1] / "templates"))
    report_workflow = ReportWorkflow(repo, report_renderer, audit_logger)
    user_service = UserService(repo)
    watcher = Watcher(settings.pdf_dir, ingest_service)

    return AppServices(
        conn=conn,
        repository=repo,
        audit_logger=audit_logger,
        extraction_service=extraction_service,
        ingest_service=ingest_service,
        search_backend=search_backend,
        matching_service=matching_service,
        document_service=document_service,
        history_service=history_service,
        report_workflow=report_workflow,
        user_service=user_service,
        watcher=watcher,
    )
