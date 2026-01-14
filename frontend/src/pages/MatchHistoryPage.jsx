import React from 'react'

export const MatchHistoryPage = ({ history, onViewReport, onViewDocument, onChangeSelection }) => {
  return (
    <section className="panel">
      <h2>Match History</h2>
      <table className="table">
        <thead>
          <tr>
            <th>Created</th>
            <th>Query</th>
            <th>Selected Document</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {history.map((item) => (
            <tr key={item.id}>
              <td>{item.created_at}</td>
              <td>{item.query_text}</td>
              <td>{item.selected_document_name || 'Unselected'}</td>
              <td>
                {item.selected_document_id && (
                  <button onClick={() => onViewDocument(item.selected_document_id)}>View Submission</button>
                )}
                {item.selected_document_id && (
                  <button onClick={() => onViewReport(item.id)}>View Report</button>
                )}
                <button onClick={() => onChangeSelection(item)}>Change Selection</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
