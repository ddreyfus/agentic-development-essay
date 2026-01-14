import React from 'react'

export const NewMatchPage = ({
  query,
  setQuery,
  candidates,
  selectedDocId,
  setSelectedDocId,
  onSearch,
  onConfirm,
  onViewDocument
}) => {
  return (
    <section className="panel">
      <h2>New Match</h2>
      <p>Enter a short description to find the closest matches.</p>
      <textarea value={query} onChange={(e) => setQuery(e.target.value)} />
      <div style={{ marginTop: '12px' }}>
        <button className="primary" onClick={onSearch}>
          Search
        </button>
      </div>

      {candidates.length > 0 && (
        <table className="table">
          <thead>
            <tr>
              <th>Select</th>
              <th>Document</th>
              <th>Manufacturer</th>
              <th>Score</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {candidates.map((candidate) => (
              <tr key={candidate.document_id}>
                <td>
                  <input
                    type="radio"
                    name="selected"
                    checked={selectedDocId === candidate.document_id}
                    onChange={() => setSelectedDocId(candidate.document_id)}
                  />
                </td>
                <td>{candidate.document_name}</td>
                <td>{candidate.manufacturer_name}</td>
                <td>{candidate.score}</td>
                <td>
                  <button onClick={() => onViewDocument(candidate.document_id)}>View</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {candidates.length > 0 && (
        <div style={{ marginTop: '16px' }}>
          <button className="primary" onClick={onConfirm}>
            Confirm + Generate Report
          </button>
        </div>
      )}
    </section>
  )
}
