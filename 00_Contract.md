<!-- @format -->

```markdown
# 00_Contract.md

## Purpose

Single-container POC for ingesting regulatory PDFs, matching free-text descriptions to submissions, and generating auditable reports.

This document is **normative** for scope and completion criteria.  
Behavioral expectations and dynamics are defined in separate use-case and interaction documents.

---

## Specification structure

This system is specified using the following layered documents:

- **Contract (`00_Contract.md`)** — scope, non-goals, and definition of done
- **Use cases (`02_Use_Cases.md`)** — expected outcomes and externally observable behavior
- **Interactions (`03_Interactions.md`)** — architectural dynamics that satisfy use cases
- **API (`04_API.md`) / Schema (`05_Schema.md`) / UI (`07_UI.md`)** — static reference contracts
- **Build plan + tests (`09_Build_Plan.md`)** — construction order and proof of correctness

Each fact appears in exactly one place; other documents reference it by ID.

---

## In Scope

- PDF ingest via startup scan and filesystem watcher
- Heuristic field extraction
- Full-text similarity search over documents (top-2 results)
- Explicit match confirmation with persistence
- Markdown report generation from confirmed matches
- Structured audit logging for all major actions
- SPA frontend served by the backend

---

## Out of Scope

- Real LLM calls or semantic retrieval
- Multi-tenant routing and authentication enforcement
- Section-level or chunked indexing
- Persistent storage of generated reports
- Automated UI testing

---

## Primary flow

Ingest PDFs → Search → Select → Report → Audit

---

## Use cases in scope

The following use cases are **normative** and must be satisfied:

- `UC-INGEST-STARTUP` — ingest PDFs on application startup
- `UC-INGEST-WATCHER` — ingest new or updated PDFs detected by the filesystem watcher
- `UC-DOCS` — browse ingested documents and view extracted fields
- `UC-MATCH` — match a free-text description to candidate documents
- `UC-CONFIRM` — confirm a selected match
- `UC-REPORT` — generate a report from a confirmed match
- `UC-HISTORY` — view prior match decisions
- `UC-IDENTITY` — retrieve current client/user identity
- `UC-AUDIT` — record audit events for all externally meaningful actions

Notes:

- `POST /ingest/rescan` exists as an **operational/test hook**, not a primary user workflow.

---

## Audit requirement

- Every externally meaningful action **must emit exactly one audit event**.
- Audit completeness is mandatory for correctness.
- Audit verification is part of the system’s definition of done.

---

## Definition of Done

The system is complete when:

- The container builds and runs successfully
- PDF ingest is idempotent and versioned
- All PDFs in the test corpus parse successfully
- `/match` returns exactly two candidates with rationales when possible
- Match confirmation persists across restarts
- Reports render correctly from templates
- All required audit events are emitted and verifiable
- All acceptance tests defined in the build plan pass in a clean container
```
