<!-- @format -->

# 04_API.md

## Conventions

### Error format (all non-2xx responses)

```json
{ "error": "message" }
```

All errors return a non-2xx status code and a JSON body in the format above.

---

## Endpoints

### GET /health

Purpose: Liveness check.

Response: `200`

```json
{ "status": "ok" }
```

---

### POST /ingest/rescan

Purpose: Trigger a rescan of `/pdfs` and ingest any new or updated files.

Request body: none

Response: `202`

```json
{ "status": "scheduled" }
```

---

### GET /documents

Purpose: List documents for the current client.

Query params (optional):

- `limit` (int)
- `offset` (int)

Response: `200`

```json
{
  "items": [
    {
      "id": 1,
      "k_number": "K240666",
      "document_name": "Example document",
      "manufacturer_name": "Example Manufacturer",
      "regulatory_class": "Class II"
    }
  ],
  "total": 5
}
```

---

### GET /documents/{id}

Purpose: Retrieve full document details.

Response: `200`

```json
{
  "id": 1,
  "k_number": "K240666",
  "document_name": "Example document",
  "document_type": "Cardiopulmonary bypass oxygenator",
  "manufacturer_name": "Example Manufacturer",
  "manufacturer_address": "123 Example St, City, State",
  "regulation_number": "870.4200",
  "regulation_name": "Example regulation name",
  "regulatory_class": "Class II",
  "product_codes": "DTZ, DTR",
  "indications_for_use": "Indicated for ...",
  "full_text_excerpt": "First few hundred characters of full_text..."
}
```

---

### POST /match

Purpose: Perform similarity search over documents for a free-text description and create a match record.

Request body:

```json
{ "query": "string" }
```

Response: `200`

```json
{
  "match_id": 42,
  "candidates": [
    {
      "document_id": 1,
      "document_name": "Example document A",
      "k_number": "K240666",
      "manufacturer_name": "Example Manufacturer A",
      "score": 0.92,
      "rationale": "Shares indications and document type terms with the query."
    },
    {
      "document_id": 2,
      "document_name": "Example document B",
      "k_number": "K231773",
      "manufacturer_name": "Example Manufacturer B",
      "score": 0.81,
      "rationale": "Similar indications-for-use language and overlapping regulation number."
    }
  ]
}
```

---

### PUT /matches/{id}

Purpose: Update an existing match record with the user’s selected document.

Request body:

```json
{ "selected_document_id": 1 }
```

Response: `200`

```json
{
  "id": 42,
  "query_text": "Short description entered by user",
  "selected_document_id": 1,
  "candidate_document_ids": [1, 2],
  "created_at": "2025-12-18T10:00:00Z"
}
```

---

### GET /matches

Purpose: List past matches for the current client.

Query params (optional):

- pagination (`limit`, `offset`)
- date range (`from`, `to`) (ISO8601)
- free-text filter (implementation optional; POC may be client-side only)

Response: `200`

```json
{
  "items": [
    {
      "id": 42,
      "created_at": "2025-12-18T10:00:00Z",
      "query_text": "Short description entered by user",
      "selected_document_id": 1,
      "selected_document_name": "Example document A",
      "selected_document_k_number": "K240666",
      "report_generated": true
    }
  ],
  "total": 3
}
```

---

### GET /matches/{id}/report

Purpose: Generate a markdown report for a given match.

Request body: none

Response: `200`

```json
{
  "match_id": 42,
  "markdown": "# Document Match Report\n...",
  "created_at": "2025-12-18T10:05:00Z"
}
```

---

### GET /user/current

Purpose: Return current client and user information (POC demo identity).

Request body: none

Response: `200`

```json
{
  "client_name": "DemoClient",
  "user_name": "demo",
  "user_email": "demo@client.com",
  "user_role": "editor"
}
```

---

## Audit mapping

The system emits structured audit events for major actions.

- ingest → `INGEST`
- match → `SEARCH`
- confirm → `SELECT`
- report → `REPORT_GENERATED`
