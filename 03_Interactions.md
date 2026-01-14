<!-- @format -->

# 03_Interactions.md

This document is **normative**: it defines the architectural dynamics (components + messages)
used to satisfy the use cases in `02_Use_Cases.md`.

It does not redefine API payloads (`04_API.md`) or persistence contracts (`05_Schema.md`).
It names components and calls out required sequencing, ownership, and boundaries.

---

## Component model (normative)

The backend is decomposed into components with explicit boundaries:

- **ApiRouter** (FastAPI routes)

  - Translates HTTP to service calls.
  - Contains no business logic.

- **PdfIngestService**

  - Orchestrates ingest workflows (startup scan, watcher events, rescan hook).

- **ExtractionService**

  - Extracts `full_text` and required structured fields from a PDF.
  - Loads parsing rules from `field_parsing_rules`.

- **DocumentRepository**

  - Owns all persistence for `documents`, `document_attributes`, `pdf_files`.
  - Is the domain-facing wrapper over `SqlStore` and contains no embedded SQL.

- **SearchBackend**

  - Queries FTS index and returns ranked document IDs + scores.

- **MatchingService**

  - Orchestrates `/match` and `/matches/{id}` behaviors.
  - Persists `matches` via repository boundary.

- **RationaleService** (POC stub)

  - Generates deterministic rationale strings for candidate results.

- **ReportService**

  - Renders markdown from a Jinja2 template using match + document data.

- **AuditLogger**

  - Writes `audit_events` for externally meaningful actions.
  - Called exactly once per action occurrence.

- **Watcher**
  - Subscribes to filesystem events under `/pdfs` and invokes ingest.

---

## Boundary rules (normative)

- ApiRouter may call only services, never repositories directly.
- Only `DocumentRepository` executes SQL.
- Only `ExtractionService` parses PDFs.
- Only `SearchBackend` issues FTS queries.
- Only `AuditLogger` writes audit rows.
- Every externally meaningful action calls `AuditLogger` exactly once.

---

## Interaction: UC-INGEST-STARTUP (startup ingest)

**Trigger**

- App startup.

**Sequence**

1. ApiRouter/Startup hook → PdfIngestService.ingest_all()
2. PdfIngestService lists `*.pdf` under `/pdfs`
3. For each file:
   - PdfIngestService → DocumentRepository.get_pdf_file(client_id, file_path)
   - If absent: treat as new ingest
   - If present: compare stored `last_modified` to current filesystem mtime
     - If unchanged: skip
     - If increased: treat as new version
4. For each ingest/version:
   - PdfIngestService → ExtractionService.extract(pdf_path, client_id)
     - ExtractionService loads `field_parsing_rules` for client
     - ExtractionService returns extracted fields + `full_text`
   - PdfIngestService → DocumentRepository.insert_document_version(extraction)
   - PdfIngestService → DocumentRepository.upsert_pdf_file_pointer(file_path, last_modified, document_id, version)
   - PdfIngestService → AuditLogger.log(event_type=`INGEST`, document_id, payload_json)

**Satisfies**

- `UC-INGEST-STARTUP`
- `UC-AUDIT` (INGEST)

---

## Interaction: UC-INGEST-WATCHER (watcher ingest)

**Trigger**

- Watcher receives create/modify event for a PDF under `/pdfs`.

**Sequence**

1. Watcher → PdfIngestService.ingest_file(file_path)
2. PdfIngestService performs the same idempotency/version check as startup ingest
3. If ingest/version:
   - ExtractionService.extract(...)
   - DocumentRepository.insert_document_version(...)
   - DocumentRepository.upsert_pdf_file_pointer(...)
   - AuditLogger.log(`INGEST`, ...)

**Satisfies**

- `UC-INGEST-WATCHER`
- `UC-AUDIT` (INGEST)

---

## Interaction: POST /ingest/rescan (operational/test hook)

**Trigger**

- HTTP `POST /ingest/rescan`

**Sequence**

1. ApiRouter → PdfIngestService.ingest_all()
2. Return `202 { "status": "scheduled" }`

Notes:

- This interaction is identical to startup ingest; it exists to make ingest testable and operable.

---

## Interaction: UC-DOCS (browse documents)

**Trigger**

- HTTP `GET /documents` or `GET /documents/{id}`

**Sequence**

1. ApiRouter → DocumentRepository.list_documents(client_id, pagination)
2. ApiRouter → DocumentRepository.get_document(client_id, id)
3. Return JSON per `04_API.md`

**Satisfies**

- `UC-DOCS`

---

## Interaction: UC-MATCH (match creation)

**Trigger**

- HTTP `POST /match { query }`

**Sequence**

1. ApiRouter → MatchingService.match(query, client_id)
2. MatchingService → SearchBackend.search(query, limit=2, client_id)
   - SearchBackend queries `documents_fts` and returns ranked doc IDs + scores
3. MatchingService loads required fields for those docs:
   - MatchingService → DocumentRepository.get_documents_by_ids(client_id, ids)
4. MatchingService → RationaleService.generate(query, doc) for each candidate
5. MatchingService → DocumentRepository.insert_match(query_text, candidate_ids_json)
6. MatchingService → AuditLogger.log(event_type=`SEARCH`, match_id, payload_json includes candidate_ids + scores)
7. Return `{ match_id, candidates[...] }` per `04_API.md`

**Satisfies**

- `UC-MATCH`
- `UC-AUDIT` (SEARCH)

---

## Interaction: UC-CONFIRM (confirm match)

**Trigger**

- HTTP `PUT /matches/{id} { selected_document_id }`

**Sequence**

1. ApiRouter → MatchingService.confirm_match(match_id, selected_document_id, client_id)
2. MatchingService → DocumentRepository.update_match_selection(match_id, selected_document_id)
3. MatchingService → AuditLogger.log(event_type=`SELECT`, match_id, document_id=selected_document_id, payload_json)
4. Return updated match record per `04_API.md`

**Satisfies**

- `UC-CONFIRM`
- `UC-AUDIT` (SELECT)

---

## Interaction: UC-REPORT (generate report)

**Trigger**

- HTTP `GET /matches/{id}/report`

**Sequence**

1. ApiRouter → ReportService.generate_report(match_id, client_id)
2. ReportService → DocumentRepository.get_match(match_id)
3. ReportService → DocumentRepository.get_document(selected_document_id)
4. ReportService renders Jinja2 template to markdown
5. ReportService → AuditLogger.log(event_type=`REPORT_GENERATED`, match_id, document_id, payload_json)
6. Return `{ match_id, markdown, created_at }` per `04_API.md`

**Satisfies**

- `UC-REPORT`
- `UC-AUDIT` (REPORT_GENERATED)

---

## Interaction: UC-HISTORY (match history)

**Trigger**

- HTTP `GET /matches`

**Sequence**

1. ApiRouter → DocumentRepository.list_matches(client_id, pagination/filters)
2. DocumentRepository joins selected document summary fields as required by `04_API.md`
3. Return response per `04_API.md`

**Satisfies**

- `UC-HISTORY`

---

## Interaction: UC-IDENTITY (current user/client)

**Trigger**

- HTTP `GET /user/current`

**Sequence**

1. ApiRouter → DocumentRepository.get_demo_identity()
2. Return response per `04_API.md`

**Satisfies**

- `UC-IDENTITY`

---

## Interaction: UC-AUDIT (audit completeness)

This use case is satisfied by the explicit `AuditLogger.log(...)` call in:

- ingest (startup + watcher + rescan hook) → `INGEST`
- match creation → `SEARCH`
- match confirmation → `SELECT`
- report generation → `REPORT_GENERATED`

Audit events are verified in acceptance tests by reading the SQLite database file (`./data/document_matcher.db`).

## Data access interface (normative)

All database access occurs through a single component:

- **SqlStore**
  - Owns the SQLite connection lifecycle.
  - Applies schema from `schema.sql` at startup.
  - Executes parameterized SQL statements.
  - Exposes only:
    - `execute(sql_id, params) -> None`
    - `fetch_one(sql_id, params) -> dict | None`
    - `fetch_all(sql_id, params) -> list[dict]`

`sql_id` refers to a statement defined in the single SQL file (or a single SQL module) identified by name.
No other component may execute raw SQL strings.
