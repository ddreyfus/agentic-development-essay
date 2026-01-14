# Document Matcher

This system ingests the provided PDFs, extracts structured text data, performs similarity search, lets a user confirm the best match, generates a report, and logs audit events.

## Setup

Backend:

1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `uvicorn app.main:app --reload`

Frontend (separate terminal):

1. `cd frontend`
2. `npm install`
3. `npm run dev`

The frontend runs at `http://localhost:5173` and the API at `http://localhost:8000`.

## Quick flow

1. Click **Ingest PDFs**.
2. Enter a short description and run **Find Top Matches**.
3. Inspect a candidate and confirm the match.
4. Generate the report and review the audit trail.

Reports are written to `reports/` and the sqlite database lives at `data/app.db`.

## Notes

See `docs/Design.md` for assumptions and design choices.
