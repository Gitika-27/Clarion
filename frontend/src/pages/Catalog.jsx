import { useMemo, useState } from 'react'
import { useStatus } from '../context/StatusContext'
import ReceiptModal from '../components/ReceiptModal'

function statusBadge(status) {
  if (status === 'auto_published') return <span className="badge badge-success">Auto-published</span>
  if (status === 'human_confirmed') return <span className="badge badge-success">Confirmed</span>
  return <span className="badge badge-warning">Needs review</span>
}

export default function Catalog() {
  const { records, refresh } = useStatus()
  const [query, setQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [openReceipt, setOpenReceipt] = useState(null)

  const filtered = useMemo(() => {
    const q = query.toLowerCase()
    return records.filter((r) => {
      const matchesQuery = !q ||
        r.product_name.toLowerCase().includes(q) ||
        r.mfg_part_num.toLowerCase().includes(q) ||
        r.manufacturer.toLowerCase().includes(q)
      const matchesStatus = !statusFilter || r.publication_status === statusFilter
      return matchesQuery && matchesStatus
    })
  }, [records, query, statusFilter])

  return (
    <div className="panel-card">
      <div className="panel-head">
        <h1>Structured product catalog</h1>
        <p>Click any specification to see exactly where it came from.</p>
      </div>

      <div className="actions-row" style={{ marginTop: 0, marginBottom: '1.25rem' }}>
        <input
          className="input-field"
          style={{ flex: 1, minWidth: 200 }}
          placeholder="Search by name, part number, or manufacturer"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select className="input-field" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          <option value="auto_published">Auto-published</option>
          <option value="human_confirmed">Confirmed</option>
          <option value="needs_review">Needs review</option>
        </select>
      </div>

      {!filtered.length ? (
        <div className="empty-state">No products match. Run the demo pipeline from Upload and run.</div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>Part number</th>
                <th>Product</th>
                <th>Manufacturer / brand</th>
                <th>Specifications</th>
                <th>Trust</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => {
                const trustPct = Math.round(r.trust_score * 100)
                const trustBadgeClass = trustPct >= 80 ? 'badge-success' : trustPct >= 60 ? 'badge-warning' : 'badge-danger'
                return (
                  <tr key={r.record_id}>
                    <td className="mono">{r.mfg_part_num}</td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{r.product_name}</div>
                      <div className="text-muted" style={{ fontSize: '0.76rem', marginTop: 2 }}>{r.grounded_description}</div>
                    </td>
                    <td>{r.manufacturer}<br /><span className="text-muted" style={{ fontSize: '0.76rem' }}>{r.brand}</span></td>
                    <td>
                      {Object.keys(r.fields).length === 0 ? (
                        <span className="text-muted">None extracted</span>
                      ) : (
                        Object.entries(r.fields).map(([fname, fv]) => (
                          <span
                            key={fname}
                            className="spec-tag"
                            onClick={() => setOpenReceipt({ recordId: r.record_id, fieldName: fname })}
                          >
                            {fname.replace(/_/g, ' ')}: {fv.normalized_value}
                          </span>
                        ))
                      )}
                    </td>
                    <td><span className={`badge ${trustBadgeClass}`}>{trustPct}%</span></td>
                    <td>{statusBadge(r.publication_status)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {openReceipt && (
        <ReceiptModal
          recordId={openReceipt.recordId}
          fieldName={openReceipt.fieldName}
          onClose={() => setOpenReceipt(null)}
          onApproved={refresh}
        />
      )}
    </div>
  )
}
