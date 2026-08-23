import { useEffect, useState } from 'react'
import { api } from '../api'
import { useStatus } from '../context/StatusContext'

export default function Outliers() {
  const { refresh } = useStatus()
  const [threshold, setThreshold] = useState('2.5')
  const [anomalies, setAnomalies] = useState([])

  async function load() {
    const data = await api.outliers(threshold)
    setAnomalies(data.anomalies || [])
  }

  useEffect(() => { load() }, [threshold])

  async function applyFix(recordId, fieldName, fixValue) {
    await api.decideField(recordId, fieldName, 'override', fixValue)
    await load()
    await refresh()
  }

  return (
    <div className="panel-card">
      <div className="panel-head">
        <h1>Catalog consistency and outlier inspector</h1>
        <p>Extracted numeric values are checked against catalog distributions to catch typos, such as 2300V instead of 230V.</p>
      </div>

      <div className="actions-row" style={{ marginTop: 0, marginBottom: '1.25rem' }}>
        <label className="text-secondary" style={{ fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 10 }}>
          Sensitivity (Z-threshold)
          <select className="input-field" value={threshold} onChange={(e) => setThreshold(e.target.value)}>
            <option value="1.5">High (1.5σ)</option>
            <option value="2.5">Standard (2.5σ)</option>
            <option value="3.5">Low (3.5σ)</option>
          </select>
        </label>
      </div>

      {!anomalies.length ? (
        <div className="empty-state">No statistical outliers detected across the current catalog.</div>
      ) : (
        anomalies.map((a) => (
          <div className="review-card flag" key={`${a.record_id}-${a.field_name}`}>
            <div className="review-card-top">
              <strong>{a.product_name}</strong>
              <span className="badge badge-danger">{a.method} anomaly</span>
            </div>
            <div style={{ fontSize: '0.86rem' }}>
              Attribute: <strong>{a.field_name}</strong> = <span className="mono" style={{ color: 'var(--danger)', fontWeight: 700 }}>{a.raw_value}</span>
            </div>
            <div className="text-muted" style={{ fontSize: '0.8rem' }}>{a.explanation}</div>
            {a.suggested_fix && (
              <div className="fix-row">
                <div>Suggested fix: <strong className="mono" style={{ color: 'var(--amber)' }}>{a.suggested_fix}</strong></div>
                <button className="btn btn-primary btn-sm" onClick={() => applyFix(a.record_id, a.field_name, a.suggested_fix)}>Apply fix</button>
              </div>
            )}
          </div>
        ))
      )}
    </div>
  )
}
