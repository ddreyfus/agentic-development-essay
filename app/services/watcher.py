from __future__ import annotations

from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.services.ingest import PdfIngestService


class _PdfEventHandler(FileSystemEventHandler):
    def __init__(self, ingest_service: PdfIngestService) -> None:
        super().__init__()
        self._ingest_service = ingest_service

    def on_created(self, event) -> None:  # type: ignore[override]
        self._handle(event)

    def on_modified(self, event) -> None:  # type: ignore[override]
        self._handle(event)

    def _handle(self, event) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() != ".pdf":
            return
        self._ingest_service.ingest_file(path)


class Watcher:
    def __init__(self, pdf_dir: str, ingest_service: PdfIngestService) -> None:
        self._pdf_dir = pdf_dir
        self._ingest_service = ingest_service
        self._observer: Optional[Observer] = None

    def start(self) -> None:
        if self._observer:
            return
        handler = _PdfEventHandler(self._ingest_service)
        observer = Observer()
        observer.schedule(handler, self._pdf_dir, recursive=True)
        observer.daemon = True
        observer.start()
        self._observer = observer

    def stop(self) -> None:
        if not self._observer:
            return
        self._observer.stop()
        self._observer.join(timeout=5)
        self._observer = None
