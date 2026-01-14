from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: str
    pdf_dir: str
    static_dir: str


def get_settings() -> Settings:
    db_path = os.getenv("DB_PATH", str(Path("data") / "document_matcher.db"))
    pdf_dir = os.getenv("PDF_DIR", "/pdfs")
    static_dir = os.getenv("STATIC_DIR", str(Path("static")))
    return Settings(db_path=db_path, pdf_dir=pdf_dir, static_dir=static_dir)
