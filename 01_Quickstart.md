<!-- @format -->

# 01_Quickstart.md

## Prereq

- Docker installed and running

## Build

From the repo root:

```bash
docker build -t document-matcher .
```

Prepare local data directory:

```bash
mkdir -p data
chmod 777 data
```

Run:

```bash
docker run -p 8000:8000 \
 -v ./pdfs:/pdfs \
 -v ./data:/data \
 -e DB_PATH=/data/document_matcher.db \
 --rm document-matcher
```

Open the UI:

```bash
http://localhost:8000
```

Local data directories

PDFs: ./pdfs (mounted into container at /pdfs)
DB: ./data (mounted into container at /data)

View database contents (optional):

```bash
sqlite3 ./data/document_matcher.db
```

Notes:

Ensure ./pdfs exists and contains PDFs to ingest (or add PDFs while the container is running).
If port 8000 is in use, change the host port, e.g. -p 8080:8000 and open http://localhost:8080
