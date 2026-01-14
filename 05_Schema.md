<!-- @format -->

# 05_Schema.md

This file is the canonical persistence contract for the POC: tables, key fields, and invariants.
All JSON values are stored as **TEXT containing JSON**.

---

## Core tables

### clients

- `id` INTEGER PK
- `name` TEXT NOT NULL
- `external_key` TEXT NOT NULL
- `created_at` TEXT NOT NULL (ISO8601)

### users

- `id` INTEGER PK
- `client_id` INTEGER NOT NULL FK → `clients.id`
- `email` TEXT NOT NULL
- `hashed_password` TEXT NOT NULL
- `role` TEXT NOT NULL
- `created_at` TEXT NOT NULL (ISO8601)

### documents

- `id` INTEGER PK
- `client_id` INTEGER NOT NULL FK → `clients.id`
- `k_number` TEXT NOT NULL
- `document_name` TEXT NOT NULL
- `document_type` TEXT NOT NULL
- `manufacturer_name` TEXT NOT NULL
- `manufacturer_address` TEXT NOT NULL
- `regulation_number` TEXT NOT NULL
- `regulation_name` TEXT NOT NULL
- `regulatory_class` TEXT NOT NULL
- `product_codes` TEXT NOT NULL
- `indications_for_use` TEXT NOT NULL
- `version` INTEGER NOT NULL
- `created_at` TEXT NOT NULL (ISO8601)
- `updated_at` TEXT NOT NULL (ISO8601)
- `full_text` TEXT NOT NULL

### document_attributes

Used to extend per-document fields without schema changes.

- `id` INTEGER PK
- `document_id` INTEGER NOT NULL FK → `documents.id`
- `name` TEXT NOT NULL
- `value_json` TEXT NOT NULL (JSON)

### matches

- `id` INTEGER PK
- `query_text` TEXT NOT NULL
- `selected_document_id` INTEGER NULL FK → `documents.id`
- `candidate_document_ids_json` TEXT NOT NULL (JSON array of ints)
- `created_at` TEXT NOT NULL (ISO8601)

### audit_events

- `id` INTEGER PK
- `event_type` TEXT NOT NULL (`INGEST`, `SEARCH`, `SELECT`, `REPORT_GENERATED`)
- `timestamp` TEXT NOT NULL (ISO8601)
- `document_id` INTEGER NULL FK → `documents.id`
- `match_id` INTEGER NULL FK → `matches.id`
- `payload_json` TEXT NOT NULL (JSON)

### pdf_files

Tracks ingested PDFs for idempotency and versioning.

- `id` INTEGER PK
- `client_id` INTEGER NOT NULL FK → `clients.id`
- `file_path` TEXT NOT NULL
- `last_modified` TEXT NOT NULL (ISO8601 derived from filesystem mtime)
- `document_id` INTEGER NOT NULL FK → `documents.id`
- `version` INTEGER NOT NULL

Constraints:

- UNIQUE(`client_id`, `file_path`)

### field_parsing_rules

Configurable extraction rules.

- `id` INTEGER PK
- `client_id` INTEGER NOT NULL FK → `clients.id`
- `field_name` TEXT NOT NULL
- `pattern` TEXT NOT NULL (regex)
- `priority` INTEGER NOT NULL

---

## Versioning invariant (POC)

- Identity key for an ingested file: `(client_id, file_path)` (enforced by UNIQUE constraint in `pdf_files`)
- Create a new document version **iff** the filesystem `last_modified` timestamp is newer than the stored `pdf_files.last_modified` for that `(client_id, file_path)`.

Operational rule:

- If `(client_id, file_path)` does not exist in `pdf_files`, ingest creates:
  - a new `documents` row with `version = 1`
  - a `pdf_files` row pointing to that document
- If it exists and `last_modified` is unchanged, ingest is a no-op
- If it exists and `last_modified` increased, ingest creates:
  - a new `documents` row with `version = previous_version + 1`
  - updates `pdf_files.document_id`, `pdf_files.version`, and `pdf_files.last_modified`

Prior document versions are preserved.

---

## FTS5 (full-text search)

Search corpus:

- `documents.full_text`

FTS requirements:

- `documents_fts` virtual table indexing `full_text` with `content='documents'` and `content_rowid='id'`
- Triggers keep FTS consistent on insert, update, delete:
  - INSERT: add `new.full_text`
  - UPDATE: delete old row then insert new
  - DELETE: delete old row

## Initial PDF parsing rules

- `document_name`  
  `^(?:Trade/)?document Name\W*(?P<value>.+)$`
- `k_number`  
  `^(?:510\\(k\\) Number|Re:)\\W*(?P<value>K\\d{6}).*$`
- `regulation_number`  
  `^Regulation Number\\W*(?P<value>\\d+\\.\\d+).*$`
- `regulation_name`  
  `^Regulation Name\W*(?P<value>.+)$`
- `regulatory_class`  
  `^Regulatory Class\\W*(?P<value>Class\\s+[IIVX]+).*$`
- `product_codes`  
  `^Product Code\\(s\\)?\\W*(?P<value>[A-Z0-9,\\s]+).*$`
- `manufacturer_name`  
  `^(Sponsor|Applicant|Manufacturer|Submitter Name)\\W*(?P<value>.+)$`  
  `^(?P<value>.+?(?:Inc\\.?|LLC|Ltd|S\\.r\\.l\\.|S\\.A\\.|GmbH))$` (fallback)
