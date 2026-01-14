import { useMemo, useState } from "react";

const API_BASE = "http://localhost:8000";

const emptyReport = {
  documentId: null,
  reportPath: "",
  reportContent: ""
};

export function App() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [candidates, setCandidates] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [selection, setSelection] = useState(null);
  const [report, setReport] = useState(emptyReport);
  const [auditEvents, setAuditEvents] = useState([]);
  const [loading, setLoading] = useState(false);

  const canGenerateReport = useMemo(() => {
    return selection?.documentId && selectedDoc?.id === selection.documentId;
  }, [selection, selectedDoc]);

  const apiFetch = async (path, options = {}) => {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {})
      },
      ...options
    });

    if (!response.ok) {
      const detail = await response.json().catch(() => ({ detail: "Request failed" }));
      throw new Error(detail.detail || "Request failed");
    }
    return response.json();
  };

  const refreshAudits = async () => {
    const data = await apiFetch("/api/audit");
    setAuditEvents(data.events || []);
  };

  const handleIngest = async () => {
    setLoading(true);
    setStatus("");
    setErrorMessage("");
    try {
      const data = await apiFetch("/api/ingest", { method: "POST" });
      setStatus(`Ingested ${data.ingested} PDFs.`);
      await refreshAudits();
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (event) => {
    event.preventDefault();
    if (!query.trim()) {
      setErrorMessage("Enter a short description to search.");
      return;
    }
    setLoading(true);
    setStatus("");
    setErrorMessage("");
    setSelection(null);
    setReport(emptyReport);
    try {
      const data = await apiFetch("/api/search", {
        method: "POST",
        body: JSON.stringify({ query })
      });
      setCandidates(data.candidates || []);
      await refreshAudits();
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInspect = async (documentId) => {
    setLoading(true);
    setStatus("");
    setErrorMessage("");
    try {
      const data = await apiFetch(`/api/documents/${documentId}`);
      setSelectedDoc(data);
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async () => {
    if (!selectedDoc) {
      setErrorMessage("Inspect a document before confirming selection.");
      return;
    }
    setLoading(true);
    setStatus("");
    setErrorMessage("");
    try {
      const data = await apiFetch("/api/selection", {
        method: "POST",
        body: JSON.stringify({ document_id: selectedDoc.id })
      });
      setSelection({
        selectionId: data.selection_id,
        documentId: data.document_id,
        createdAt: data.created_at
      });
      await refreshAudits();
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReport = async () => {
    if (!selectedDoc) {
      setErrorMessage("Inspect and select a document before generating a report.");
      return;
    }
    setLoading(true);
    setStatus("");
    setErrorMessage("");
    try {
      const data = await apiFetch("/api/report", {
        method: "POST",
        body: JSON.stringify({ document_id: selectedDoc.id })
      });
      setReport({
        documentId: data.document_id,
        reportPath: data.report_path,
        reportContent: data.report_content
      });
      await refreshAudits();
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="hero">
        <div>
          <p className="eyebrow">FDA Document Match</p>
          <h1>Pinpoint the closest submission in seconds.</h1>
          <p className="subtitle">
            Describe the document you have, compare the top two matches, confirm the
            best one, and generate a report with a complete audit trail.
          </p>
        </div>
        <div className="hero-actions">
          <button type="button" className="primary" onClick={handleIngest} disabled={loading}>
            Ingest PDFs
          </button>
          <button type="button" className="ghost" onClick={refreshAudits} disabled={loading}>
            Refresh Audit Log
          </button>
          <span className="status">{status}</span>
          {errorMessage ? <div className="error-banner">{errorMessage}</div> : null}
        </div>
      </header>

      <main className="grid">
        <section className="panel search">
          <h2>Describe the document</h2>
          <form onSubmit={handleSearch}>
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Short description of the document you are trying to match..."
              rows={4}
            />
            <button type="submit" className="primary" disabled={loading}>
              Find Top Matches
            </button>
          </form>
          <div className="results">
            {candidates.length === 0 ? (
              <p className="empty">No candidates yet. Run a search to see matches.</p>
            ) : (
              candidates.map((candidate, index) => (
                <article key={candidate.document_id} className="candidate">
                  <div>
                    <p className="tag">Match {index + 1}</p>
                    <h3>{candidate.title}</h3>
                    <p className="meta">{candidate.filename}</p>
                    <p className="summary">{candidate.summary}</p>
                    <p className="explanation">{candidate.explanation}</p>
                  </div>
                  <div className="candidate-actions">
                    <span className="score">Score {candidate.score.toFixed(2)}</span>
                    <button
                      type="button"
                      className="ghost"
                      onClick={() => handleInspect(candidate.document_id)}
                      disabled={loading}
                    >
                      Inspect Details
                    </button>
                  </div>
                </article>
              ))
            )}
          </div>
        </section>

        <section className="panel detail">
          <h2>Document details</h2>
          {selectedDoc ? (
            <div className="detail-card">
              <div>
                <p className="tag">Selected Candidate</p>
                <h3>{selectedDoc.title}</h3>
                <p className="meta">{selectedDoc.filename}</p>
                <p className="meta">
                  {selectedDoc.page_count} pages · {selectedDoc.word_count} words
                </p>
              </div>
              <p className="summary">{selectedDoc.summary}</p>
              <div className="detail-actions">
                <button type="button" className="primary" onClick={handleSelect} disabled={loading}>
                  Confirm Match
                </button>
                <button
                  type="button"
                  className="ghost"
                  onClick={handleReport}
                  disabled={loading || !canGenerateReport}
                >
                  Generate Report
                </button>
              </div>
              {selection ? (
                <p className="status">Confirmed selection #{selection.selectionId}</p>
              ) : null}
            </div>
          ) : (
            <p className="empty">Inspect a candidate to review full document details.</p>
          )}
        </section>

        <section className="panel report">
          <h2>Generated report</h2>
          {report.reportContent ? (
            <div className="report-card">
              <p className="meta">Saved to {report.reportPath}</p>
              <pre>{report.reportContent}</pre>
            </div>
          ) : (
            <p className="empty">Generate a report after confirming a selection.</p>
          )}
        </section>

        <section className="panel audit">
          <h2>Audit trail</h2>
          {auditEvents.length === 0 ? (
            <p className="empty">Audit events will appear here after actions run.</p>
          ) : (
            <div className="audit-list">
              {auditEvents.map((event) => (
                <div key={event.id} className="audit-item">
                  <p className="tag">{event.event_type}</p>
                  <p className="meta">{event.created_at}</p>
                  <pre>{JSON.stringify(event.details, null, 2)}</pre>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
