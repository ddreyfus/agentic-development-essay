<!-- @format -->

# 06_Extraction.md

This document is **normative**.  
It defines which fields are extracted from PDFs and how extraction rules are applied.

---

## Extracted fields

The extraction process must populate the following fields for every ingested document:

- `document_name`
- `k_number`
- `regulation_number`
- `regulation_name`
- `regulatory_class`
- `product_codes`
- `manufacturer_name`
- `indications_for_use`
- `full_text`

All fields above are **required**. Failure to extract any required field for a PDF in the test corpus is considered a failure.

---

## Field definitions

- **document_name**  
  Human-readable submission or trade name.

- **k_number**  
  FDA 510(k) identifier (e.g., `K240666`).

- **regulation_number**  
  CFR regulation number (e.g., `870.4200`).

- **regulation_name**  
  Textual name of the regulation.

- **regulatory_class**  
  Regulatory class (e.g., `Class I`, `Class II`, `Class III`).

- **product_codes**  
  One or more FDA product codes, stored as a comma-separated string.

- **manufacturer_name**  
  Legal name of the submitter/manufacturer.

- **indications_for_use**  
  Short paragraph extracted from the primary “Indications for Use” section.

- **full_text**  
  Concatenated text of all PDF pages; used as the sole search corpus.

---

## Rule semantics

Extraction is driven by regex rules stored in the `field_parsing_rules` table.

Rules are applied as follows:

1. Rules are grouped by `field_name`.
2. For a given field, rules are evaluated in **ascending `priority` order**.
3. Each rule is applied to the extracted PDF text (line-based or block-based, implementation-defined).
4. **First match wins**.
5. The value of the named capture group `(?P<value>...)` is used as the extracted field value.
6. If no rule matches for a required field, extraction fails for that document.

---

## Rule loading

- All `field_parsing_rules` for the active client are loaded **once at application startup**.
- Rules are treated as read-only for the lifetime of the process.
- Changing extraction behavior requires updating database rows and restarting the container.

---

## Indications for Use extraction

- The first detected “Indications for Use” section is treated as canonical.
- A fixed window of text following the section header is captured.
- If multiple sections exist, only the first is used.

---

## Failure semantics

- Partial extraction is not allowed.
- A document that cannot satisfy all required fields must not be persisted as a valid `documents` row.
- Such failures must be visible during ingest (and surfaced via tests).

---

## Scope notes

- Extraction is heuristic and deterministic.
- No ML or LLM-based extraction is performed in the POC.
- Section-level indexing or chunking is explicitly out of scope.
