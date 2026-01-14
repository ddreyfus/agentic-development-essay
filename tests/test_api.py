"""API endpoint tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _ingest(client) -> int:
    response = client.post("/api/ingest")
    assert response.status_code == 200
    payload = response.json()
    assert "ingested" in payload
    assert payload["ingested"] > 0
    return payload["ingested"]


def _search(client, query: str) -> list[dict[str, Any]]:
    response = client.post("/api/search", json={"query": query})
    assert response.status_code == 200
    payload = response.json()
    assert "candidates" in payload
    return payload["candidates"]


def test_openapi_smoke(client) -> None:
    test_client, _ = client
    response = test_client.get("/openapi.json")
    assert response.status_code == 200
    payload = response.json()
    assert "paths" in payload


def test_ingest_records_audit(client) -> None:
    test_client, _ = client
    ingested = _ingest(test_client)

    response = test_client.get("/api/audit")
    assert response.status_code == 200
    payload = response.json()
    events = payload.get("events", [])
    assert any(event["event_type"] == "ingest" for event in events)
    ingest_event = next(event for event in events if event["event_type"] == "ingest")
    assert ingest_event["details"]["count"] == ingested


def test_search_returns_candidates(client) -> None:
    test_client, _ = client
    _ingest(test_client)

    candidates = _search(test_client, "510(k) device submission")
    assert len(candidates) <= 2
    assert len(candidates) > 0
    first = candidates[0]
    assert "document_id" in first
    assert "explanation" in first


def test_document_details(client) -> None:
    test_client, _ = client
    _ingest(test_client)

    candidates = _search(test_client, "medical device summary")
    document_id = candidates[0]["document_id"]
    response = test_client.get(f"/api/documents/{document_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == document_id
    assert payload["content"]


def test_selection_and_report(client) -> None:
    test_client, report_dir = client
    _ingest(test_client)

    candidates = _search(test_client, "clinical overview")
    document_id = candidates[0]["document_id"]

    selection_response = test_client.post("/api/selection", json={"document_id": document_id})
    assert selection_response.status_code == 200
    selection_payload = selection_response.json()
    assert selection_payload["document_id"] == document_id

    report_response = test_client.post("/api/report", json={"document_id": document_id})
    assert report_response.status_code == 200
    report_payload = report_response.json()
    assert report_payload["document_id"] == document_id
    assert report_payload["report_content"]
    report_path = Path(report_payload["report_path"]).resolve()
    assert report_dir.exists()
    assert report_path.exists()
    assert report_dir.resolve() in report_path.parents
