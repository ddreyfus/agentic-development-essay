import React from 'react'

export const DocumentCatalogPage = ({ documents, onViewDocument }) => {
  return (
    <section className="panel">
      <h2>Document Catalog</h2>
      <table className="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>K-Number</th>
            <th>Manufacturer</th>
            <th>Class</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.id}>
              <td>{doc.document_name}</td>
              <td>{doc.k_number}</td>
              <td>{doc.manufacturer_name}</td>
              <td>{doc.regulatory_class}</td>
              <td>
                <button onClick={() => onViewDocument(doc.id)}>View</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  )
}
