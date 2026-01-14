<!-- @format -->

# Application Behavior

The application must allow a user to:

- Enter a short free-text document description.
- Retrieve the two most similar documents, with a brief explanation of why each was selected.
- Inspect document details for each candidate.
- Confirm one candidate as the final match.
- Generate a document report based on the confirmed selection.
- Record audit events for ingest, search, selection, and report generation.

# Deliverables

- A runnable implementation with clear instructions for building and executing the system.
- Minimal documentation explaining key design choices and constraints.

# Objective

The system must ingest PDFs, extract and persist structured data, support similarity search and user selection, generate a report from that selection, and emit an audit trail for all meaningful actions.

# Input Data

A small set of representative PDFs (5) is provided under `/pdfs/`. Each PDF summarizes an FDA document and reflects the structure and variability expected in real submissions.
