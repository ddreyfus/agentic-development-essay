<!-- @format -->

# 08_Container.md

Normative container contract for the POC.

---

## Base images (fixed)

- Backend: `python:3.13-slim`
- Frontend build: `node:20`

Versions are fixed and out of scope to change.

---

## Build

- Multi-stage build.
- Python stage:
  - Install system deps required for `pdfplumber` and SQLite (FTS5).
  - `pip install -r requirements.txt` (versions must be pinned).
  - Copy backend code to `/app`.
- Node stage:
  - Build React/Vite frontend.
  - Emit static assets to `/frontend/dist`.
- Final image:
  - Python-only runtime.
  - Copy frontend assets to `/app/static`.

---

## Runtime layout

- App root: `/app`
- Static assets: `/app/static`
- PDFs (mounted): `/pdfs`
- SQLite DB: `$DB_PATH`

---

## Entrypoint

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
