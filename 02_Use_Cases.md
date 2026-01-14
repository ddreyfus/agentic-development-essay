<!-- @format -->

# 02_Use_Cases.md

This document is **normative**: it defines expected outcomes and externally observable behavior.
It does not define internal architecture (see `03_Interactions.md`).

Each use case includes:

- Goal / trigger
- Expected outcomes
- API touchpoints (reference only)
- Required audit event(s)

---

## UC-INGEST-STARTUP — Startup ingest

**Trigger**

- Application starts.

**Expected outcomes**

- System scans `/pdfs` and ingests any PDFs not yet ingested for the current client.
- For each ingested PDF, a `documents` row exists with extracted fields populated and `full_text` indexed.
- Idempotency: restarting without PDF changes produces no new document versions.

**API touchpoints**

- None required.
- Observability via: `GET /documents`, `GET /documents/{id}`

**Audit**

- Emits `INGEST` for each newly ingested or versioned PDF.

---

## UC-INGEST-WATCHER — Watcher ingest

**Trigger**

- A PDF is created or modified under `/pdfs` while the container is running.

**Expected outcomes**

- The new/updated PDF is ingested without container restart.
- If the file path is unchanged and `last_modified` increased, a new document version is created and prior versions are preserved.

**API touchpoints**

- None required.
- Observability via: `GET /documents`, `GET /documents/{id}`
- Operational/test hook: `POST /ingest/rescan` may be used to force ingest.

**Audit**

- Emits `INGEST` for each newly ingested or versioned PDF.

---

## UC-DOCS — Browse documents

**Trigger**

- User opens Document Catalog or views a document.

**Expected outcomes**

- Documents are listable and viewable.
- `GET /documents/{id}` returns all required extracted fields non-null for all corpus PDFs:
  - `k_number`
  - `document_name`
  - `document_type`
  - `manufacturer_name`
  - `manufacturer_address`
  - `regulation_number`
  - `regulation_name`
  - `regulatory_class`
  - `product_codes`
  - `indications_for_use`
  - `full_text_excerpt`

**API touchpoints**

- `GET /documents`
- `GET /documents/{id}`

**Audit**

- None required for read-only browsing (POC).

---

## UC-MATCH — Match a description

**Trigger**

- User submits a free-text query.

**Expected outcomes**

- A match record is created for the query.
- The system returns up to 2 candidates ranked by lexical similarity to `documents.full_text`.
- Each candidate includes a deterministic rationale string.

**API touchpoints**

- `POST /match`

**Audit**

- Emits `SEARCH` once per `/match` request.

---

## UC-CONFIRM — Confirm a match

**Trigger**

- User selects one of the candidates and confirms.

**Expected outcomes**

- The match record is updated with `selected_document_id`.
- The selection persists across restarts.
- The persisted match retains the candidate set used at the time of matching.

**API touchpoints**

- `PUT /matches/{id}`

**Audit**

- Emits `SELECT` once per confirmation.

---

## UC-REPORT — Generate report

**Trigger**

- User requests a report for a confirmed match.

**Expected outcomes**

- A markdown report is generated deterministically from a template and returned to the client.
- Reports are generated on demand and are not persisted as first-class records.

**API touchpoints**

- `GET /matches/{id}/report`

**Audit**

- Emits `REPORT_GENERATED` once per report request.

---

## UC-HISTORY — View match history

**Trigger**

- User opens Match History.

**Expected outcomes**

- Prior matches are listable.
- Each listed match includes selected document name and K-number when selection exists.

**API touchpoints**

- `GET /matches`

**Audit**

- None required for read-only browsing (POC).

---

## UC-IDENTITY — View current user/client

**Trigger**

- UI loads header identity.

**Expected outcomes**

- Demo user/client identity is returned.

**API touchpoints**

- `GET /user/current`

**Audit**

- None required (POC).

---

## UC-AUDIT — Audit completeness

**Trigger**

- Any ingest, match, confirm, or report action occurs.

**Expected outcomes**

- Exactly one audit event is emitted per action occurrence:
  - ingest → `INGEST`
  - match → `SEARCH`
  - confirm → `SELECT`
  - report → `REPORT_GENERATED`
- Audit rows are persisted in `audit_events` and verifiable via the SQLite DB.

**API touchpoints**

- None (audits are internal; verified via DB in tests).

**Audit**

- This use case defines the audit requirements above.
