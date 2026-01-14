from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

import pdfplumber


@dataclass
class ExtractionResult:
    fields: Dict[str, str]
    full_text: str


class ExtractionService:
    REQUIRED_FIELDS = {
        "document_name",
        "k_number",
        "regulation_number",
        "regulation_name",
        "regulatory_class",
        "product_codes",
        "manufacturer_name",
        "indications_for_use",
        "full_text",
    }

    def __init__(self, rules: Dict[str, List[re.Pattern[str]]]) -> None:
        self._rules = rules

    @staticmethod
    def load_rules(raw_rules: Iterable[Dict[str, str]]) -> Dict[str, List[re.Pattern[str]]]:
        grouped: Dict[str, List[re.Pattern[str]]] = {}
        for rule in raw_rules:
            field = rule["field_name"]
            pattern = rule["pattern"]
            compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            grouped.setdefault(field, []).append(compiled)
        return grouped

    def extract(self, pdf_path: Path) -> ExtractionResult:
        full_text = self._extract_full_text(pdf_path)
        fields = self._apply_rules(full_text)
        fields["indications_for_use"] = self._extract_indications(full_text)
        fields["full_text"] = full_text
        self._validate_required(fields)
        return ExtractionResult(fields=fields, full_text=full_text)

    def _extract_full_text(self, pdf_path: Path) -> str:
        text_parts: List[str] = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text_parts.append(page_text)
        return "\n".join(text_parts).strip()

    def _apply_rules(self, full_text: str) -> Dict[str, str]:
        fields: Dict[str, str] = {}
        for field, patterns in self._rules.items():
            for pattern in patterns:
                match = pattern.search(full_text)
                if match and "value" in match.groupdict():
                    fields[field] = match.group("value").strip()
                    break
        return fields

    def _extract_indications(self, full_text: str) -> str:
        match = re.search(r"Indications for Use", full_text, re.IGNORECASE)
        if not match:
            return ""
        start = match.end()
        snippet = full_text[start : start + 800]
        return " ".join(snippet.split()).strip()

    def _validate_required(self, fields: Dict[str, str]) -> None:
        missing = [field for field in self.REQUIRED_FIELDS if not fields.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(sorted(missing))}")
