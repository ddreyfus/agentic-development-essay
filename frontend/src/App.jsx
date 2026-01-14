import React, { useEffect, useState } from 'react'
import './styles.css'
import { NewMatchPage } from './pages/NewMatchPage.jsx'
import { MatchHistoryPage } from './pages/MatchHistoryPage.jsx'
import { DocumentCatalogPage } from './pages/DocumentCatalogPage.jsx'

const panels = {
  newMatch: 'New Match',
  history: 'Match History',
  catalog: 'Document Catalog'
}

export const App = () => {
  const [activePanel, setActivePanel] = useState('newMatch')
  const [query, setQuery] = useState('')
  const [candidates, setCandidates] = useState([])
  const [matchId, setMatchId] = useState(null)
  const [selectedDocId, setSelectedDocId] = useState(null)
  const [history, setHistory] = useState([])
  const [documents, setDocuments] = useState([])
  const [identity, setIdentity] = useState(null)
  const [modalContent, setModalContent] = useState(null)
  const [reportContent, setReportContent] = useState(null)
  const [error, setError] = useState(null)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    fetch('/user/current')
      .then((res) => res.json())
      .then(setIdentity)
      .catch(() => setError('Failed to load user identity.'))
  }, [])

  useEffect(() => {
    if (activePanel === 'history') {
      fetch('/matches')
        .then((res) => res.json())
        .then((data) => setHistory(data.items || []))
        .catch(() => setError('Failed to load match history.'))
    }
    if (activePanel === 'catalog') {
      fetch('/documents')
        .then((res) => res.json())
        .then((data) => setDocuments(data.items || []))
        .catch(() => setError('Failed to load documents.'))
    }
  }, [activePanel])

  const runMatch = () => {
    setError(null)
    fetch('/match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    })
      .then((res) => res.json())
      .then((data) => {
        setCandidates(data.candidates || [])
        setMatchId(data.match_id)
      })
      .catch(() => setError('Match request failed.'))
  }

  const confirmMatch = () => {
    if (!matchId || !selectedDocId) {
      setError('Select a document before confirming.')
      return
    }
    fetch(`/matches/${matchId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ selected_document_id: selectedDocId })
    })
      .then((res) => res.json())
      .then(() => fetchReport(matchId))
      .catch(() => setError('Failed to confirm match.'))
  }

  const fetchReport = (id) => {
    fetch(`/matches/${id}/report`)
      .then((res) => res.json())
      .then((data) => setReportContent(data.markdown))
      .catch(() => setError('Report generation failed.'))
  }

  const fetchDocument = (id) => {
    fetch(`/documents/${id}`)
      .then((res) => res.json())
      .then((data) => setModalContent(data))
      .catch(() => setError('Failed to load document.'))
  }

  const changeSelection = (matchRow) => {
    const input = window.prompt('Enter a new document ID to select:')
    if (!input) {
      return
    }
    const docId = Number(input)
    if (!docId) {
      setError('Invalid document ID.')
      return
    }
    fetch(`/matches/${matchRow.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ selected_document_id: docId })
    })
      .then((res) => res.json())
      .then(() => {
        setError(null)
        return fetch('/matches')
      })
      .then((res) => res.json())
      .then((data) => setHistory(data.items || []))
      .catch(() => setError('Failed to change selection.'))
  }

  const downloadReport = () => {
    if (!reportContent) {
      return
    }
    const blob = new Blob([reportContent], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `match-report-${Date.now()}.md`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  const renderMarkdown = (markdown) => {
    const escapeHtml = (value) =>
      value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

    const lines = markdown.split('\n')
    const output = []
    let inList = false

    lines.forEach((line) => {
      if (line.startsWith('- ')) {
        if (!inList) {
          output.push('<ul>')
          inList = true
        }
        output.push(`<li>${escapeHtml(line.slice(2))}</li>`)
        return
      }

      if (inList) {
        output.push('</ul>')
        inList = false
      }

      if (line.startsWith('### ')) {
        output.push(`<h3>${escapeHtml(line.slice(4))}</h3>`)
      } else if (line.startsWith('## ')) {
        output.push(`<h2>${escapeHtml(line.slice(3))}</h2>`)
      } else if (line.startsWith('# ')) {
        output.push(`<h1>${escapeHtml(line.slice(2))}</h1>`)
      } else if (line.trim()) {
        output.push(`<p>${escapeHtml(line)}</p>`)
      }
    })

    if (inList) {
      output.push('</ul>')
    }

    return output.join('')
  }

  return (
    <div>
      <header>
        <div>
          <h1>Document Matcher</h1>
          <div>{identity ? `${identity.client_name} · ${identity.user_email}` : 'Loading identity...'}</div>
        </div>
        <div className="header-meta">
          <span className="badge">Ingest: idle</span>
          <div className="user-menu">
            <button onClick={() => setMenuOpen((prev) => !prev)}>
              {identity ? identity.user_email : 'User'}
            </button>
            {menuOpen && (
              <div className="user-menu-panel">
                <button onClick={() => setError('Profile editor is a UI stub.')}>View / Edit Profile</button>
                <button onClick={() => setError('Logout is a UI stub.')}>Logout</button>
                <button onClick={() => setError('Login is a UI stub.')}>Login</button>
              </div>
            )}
          </div>
        </div>
        <nav>
          {Object.entries(panels).map(([key, label]) => (
            <button
              key={key}
              className={activePanel === key ? 'active' : ''}
              onClick={() => setActivePanel(key)}
            >
              {label}
            </button>
          ))}
        </nav>
      </header>

      <main>
        {error && <div className="panel">{error}</div>}

        {activePanel === 'newMatch' && (
          <NewMatchPage
            query={query}
            setQuery={setQuery}
            candidates={candidates}
            selectedDocId={selectedDocId}
            setSelectedDocId={setSelectedDocId}
            onSearch={runMatch}
            onConfirm={confirmMatch}
            onViewDocument={fetchDocument}
          />
        )}

        {activePanel === 'history' && (
          <MatchHistoryPage
            history={history}
            onViewReport={fetchReport}
            onViewDocument={fetchDocument}
            onChangeSelection={changeSelection}
          />
        )}

        {activePanel === 'catalog' && (
          <DocumentCatalogPage documents={documents} onViewDocument={fetchDocument} />
        )}
      </main>

      {modalContent && (
        <div className="modal" onClick={() => setModalContent(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{modalContent.document_name}</h3>
              <button className="modal-close" onClick={() => setModalContent(null)}>Close</button>
            </div>
            <p><strong>K-Number:</strong> {modalContent.k_number}</p>
            <p><strong>Document Type:</strong> {modalContent.document_type}</p>
            <p><strong>Manufacturer:</strong> {modalContent.manufacturer_name}</p>
            <p><strong>Manufacturer Address:</strong> {modalContent.manufacturer_address}</p>
            <p><strong>Regulation:</strong> {modalContent.regulation_number} — {modalContent.regulation_name}</p>
            <p><strong>Regulatory Class:</strong> {modalContent.regulatory_class}</p>
            <p><strong>Product Codes:</strong> {modalContent.product_codes}</p>
            <p><strong>Indications:</strong> {modalContent.indications_for_use}</p>
          </div>
        </div>
      )}

      {reportContent && (
        <div className="modal" onClick={() => setReportContent(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Generated Report</h3>
              <div className="modal-actions">
                <button className="modal-close" onClick={downloadReport}>Download</button>
                <button className="modal-close" onClick={() => setReportContent(null)}>Close</button>
              </div>
            </div>
            <div
              className="markdown"
              dangerouslySetInnerHTML={{ __html: renderMarkdown(reportContent) }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
