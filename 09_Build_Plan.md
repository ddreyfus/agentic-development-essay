<!-- @format -->

# 09_Build_Plan.md

## Purpose

This build plan is the authoritative implementation handoff for a human or an agent.  
It specifies **what to build, in what order, and how completion is verified**, without prescribing internal implementation details.

Work is organized as **test-gated milestones**. A milestone is complete only when its acceptance tests pass.

References:

- System contract: `00_Contract.md`
- Runtime/container contract: `08_Container.md`
- API contract: `04_API.md`
- Schema + FTS + invariants: `05_Schema.md`
- Extraction contract: `06_Extraction.md`
- UI contract: `07_UI.md`

---

## Test execution model

- All tests are written in **pytest**.
- All acceptance tests are **black-box** and run **against a Docker container**.
- Each test:
  1. Builds the Docker image (if needed),
  2. Starts a fresh container,
  3. Interacts with the system via HTTP and mounted volumes,
  4. Stops and removes the container.
- Tests must not rely on in-process calls, shared state, or pre-existing containers.
- Internal unit tests may exist, but **milestone completion is determined only by container-level pytest tests**.
- Tests may verify persistence by reading the SQLite DB file on the host via the mounted `./data` volume.
- Audit is validated via DB access in tests; no audit-read API is required for the POC.

---

## Milestone 0 — Container skeleton

**Deliverables**

- Dockerfile conforming to `08_Container.md`
- Container starts FastAPI app on port 8000

**Acceptance tests**

- `test_container_build_and_health`
  - `docker build` succeeds
  - container starts
  - `GET /health` returns 200

---

## Milestone 1 — Application skeleton + static frontend serving

**Deliverables**

- FastAPI entrypoint
- Static asset serving path wired (placeholders acceptable)
- `GET /health` implemented per `04_API.md`
- SPA static content served at `/` (built assets once available)

**Architectural checkpoints**

- Route handlers contain no business logic
- All logic lives behind service/module boundaries

**Acceptance tests**

- `test_container_build_and_health` (continues to pass)
- `test_static_frontend_served`
  - `GET /` returns 200
  - response contains a stable marker (e.g., `<div id="root">`)

---

## Milestone 2 — Database schema and bootstrap

**Deliverables**

- Single SQL schema file implementing all tables in `05_Schema.md`
- Schema applied automatically at startup
- Demo client and demo user seeded
- `GET /user/current` implemented per `04_API.md`

**Architectural checkpoints**

- All SQL defined in one location
- No inline SQL in route handlers
- Schema is the single source of truth for persistence

**Acceptance tests**

- `test_db_bootstrap`
  - fresh container creates all tables
  - demo client and user exist
- `test_user_current_endpoint`
  - `GET /user/current` returns demo user and client metadata

---

## Milestone 3 — Startup ingest (idempotent + versioned)

**Deliverables**

- Startup scan of `/pdfs`
- Idempotent ingest using `pdf_files`
- Document versioning per invariants in `05_Schema.md`
- `INGEST` audit events emitted
- `POST /ingest/rescan` implemented per `04_API.md`

**Architectural checkpoints**

- Ingest logic isolated in an ingest service
- File hash / mtime logic not duplicated elsewhere

**Acceptance tests**

- `test_startup_ingest_idempotent`
  - PDFs ingested on startup
  - container restart does not duplicate documents
  - modified PDF creates a new document version
- `test_ingest_rescan_endpoint`
  - `POST /ingest/rescan` returns 202
  - adding a new PDF then rescan ingests it (document count increases)

---

## Milestone 4 — PDF context extraction (text + structured fields)

**Deliverables**

- PDF text extraction using `pdfplumber`
- Field extraction per `06_Extraction.md` (regex rules from DB)
- Persist extracted values on document record (and/or attributes table as designed)
- `GET /documents/{id}` exposes required fields (including excerpt)

**Architectural checkpoints**

- Extraction isolated behind an `ExtractionService`
- Ingest calls extraction; search/matching/report do not parse PDFs
- Field parsing rules loaded from DB; no hardcoded label regexes outside seed/migration

**Acceptance tests**

- `test_pdf_extraction_deterministic`
  - given a fixed sample PDF, `full_text` is non-empty and stable across runs
  - required fields extract deterministically for that sample
- `test_all_sample_pdfs_parse_and_are_complete_via_api`
  - start container with sample `./pdfs` mounted
  - wait for ingest (or call `POST /ingest/rescan`)
  - call `GET /documents` and assert expected count (test corpus count)
  - for each document, call `GET /documents/{id}`
  - assert the following are present and non-null (non-empty string) for every document:
    - `k_number`
    - `document_name`
    - `document_type`
    - `manufacturer_name`
    - `regulation_number`
    - `regulation_name`
    - `regulatory_class`
    - `product_codes`
    - `indications_for_use`
    - `full_text_excerpt` (or `full_text` if that is what the API exposes)

---

## Milestone 5 — Search and document catalog

**Deliverables**

- FTS5 index on `documents.full_text` per `05_Schema.md`
- Endpoints:
  - `GET /documents`
  - `GET /documents/{id}` (remains canonical; already exercised)

**Architectural checkpoints**

- Search accessed only via a search interface
- UI and matching logic do not execute SQL directly

**Acceptance tests**

- `test_documents_and_search`
  - documents list returns ingested docs
  - FTS query returns ranked results
  - ranking is stable for fixed input

---

## Milestone 6 — Match creation

**Deliverables**

- `POST /match` per `04_API.md`
- Top-2 candidates returned
- Deterministic rationale stub
- Match record persisted
- `SEARCH` audit event emitted

**Architectural checkpoints**

- Matching logic isolated behind a matching service
- Rationale generation behind a replaceable interface (`LlmReasoner` stubbed)

**Acceptance tests**

- `test_match_creation`
  - match record created with candidate document IDs
  - exactly two candidates returned when corpus permits
  - SEARCH audit event emitted

---

## Milestone 7 — Match confirmation + history listing

**Deliverables**

- `PUT /matches/{id}` per `04_API.md`
- Selected document persisted
- `SELECT` audit event emitted
- `GET /matches` per `04_API.md`

**Architectural checkpoints**

- Match mutation logic isolated from search logic
- History listing does not reimplement matching logic

**Acceptance tests**

- `test_match_confirmation`
  - selected document persists across restarts
  - SELECT audit event emitted
- `test_matches_list_endpoint`
  - `GET /matches` returns the created match
  - selected document fields are populated per API contract

---

## Milestone 8 — Report generation

**Deliverables**

- Jinja2 markdown template
- `GET /matches/{id}/report` per `04_API.md`
- Reports generated on demand (not stored)
- `REPORT_GENERATED` audit event emitted

**Architectural checkpoints**

- Report rendering isolated behind a report service
- Templates contain no business logic

**Acceptance tests**

- `test_report_generation`
  - markdown rendered
  - match and document metadata present
  - REPORT_GENERATED audit event emitted

---

## Milestone 9 — Runtime file watcher

**Deliverables**

- Background watcher for `/pdfs`
- Ingest triggered on new or updated files
- `INGEST` audit events emitted

**Architectural checkpoints**

- Watcher isolated from ingest implementation
- No watcher logic in API handlers

**Acceptance tests**

- `test_runtime_watcher_ingest`
  - adding PDF while running triggers ingest without restart
  - INGEST audit event emitted

---

## Milestone 10 — Audit completeness gate

**Deliverables**

- Audit events emitted for all major actions
- Audit records persisted in `audit_events` per `05_Schema.md`

**Architectural checkpoints**

- Audit logging is a single, reusable component (no duplicated event writes)
- Event payload schema is stable enough for tests (at least event_type + ids)

**Acceptance tests**

- `test_audit_events_emitted_for_all_actions`
  - perform: ingest (startup or rescan), match, select, report
  - open SQLite DB via mounted `./data/document_matcher.db`
  - assert at least one audit row exists for each `event_type`:
    - `INGEST`
    - `SEARCH`
    - `SELECT`
    - `REPORT_GENERATED`
  - assert `match_id` present for SEARCH/SELECT/REPORT where applicable
  - assert `document_id` present for INGEST and for SELECT/REPORT where applicable

---

## Expected pytest test suite

The following tests must exist and pass. Test names are normative.

- `test_container_build_and_health`
- `test_static_frontend_served`
- `test_db_bootstrap`
- `test_user_current_endpoint`
- `test_startup_ingest_idempotent`
- `test_ingest_rescan_endpoint`
- `test_pdf_extraction_deterministic`
- `test_all_sample_pdfs_parse_and_are_complete_via_api`
- `test_documents_and_search`
- `test_match_creation`
- `test_match_confirmation`
- `test_matches_list_endpoint`
- `test_report_generation`
- `test_runtime_watcher_ingest`
- `test_audit_events_emitted_for_all_actions`

---

## Completion criteria

- All milestones completed in order
- All pytest acceptance tests pass against a freshly built container
- All items in `00_Contract.md` Definition of Done satisfied
- No duplication of schema, API, or invariants across files
