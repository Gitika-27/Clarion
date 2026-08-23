import { useEffect, useState } from 'react'
import { NavLink, Route, Routes, Navigate } from 'react-router-dom'
import { api } from '../api'
import { useStatus } from '../context/StatusContext'

function DuplicatesPanel({ onChanged }) {
  const [proposals, setProposals] = useState([])

  async function load() {
    const data = await api.identityProposals()
    setProposals(data)
  }
  useEffect(() => { load() }, [])

  async function decide(proposalId, action) {
    await api.decideIdentity(proposalId, action)
    await load()
    onChanged()
  }

  if (!proposals.length) return <div className="empty-state">No pending duplicate proposals.</div>

  return proposals.map((p) => (
    <div className="review-card" key={p.proposal_id}>
      <div className="review-card-top">
        <span className="badge badge-success">{Math.round(p.similarity * 100)}% similarity</span>
        <span className="mono text-muted" style={{ fontSize: '0.72rem' }}>{p.proposal_id}</span>
      </div>
      <div className="compare-box">
        <div className="compare-side">
          <div className="side-label">Product A · doc {p.doc_id_a}</div>
          <div className="side-value">{p.raw_name_a}</div>
        </div>
        <div className="compare-side">
          <div className="side-label">Product B · doc {p.doc_id_b}</div>
          <div className="side-value">{p.raw_name_b}</div>
        </div>
      </div>
      <div className="review-actions">
        <button className="btn btn-success btn-sm" onClick={() => decide(p.proposal_id, 'merge')}>Merge — same product</button>
        <button className="btn btn-sm" onClick={() => decide(p.proposal_id, 'keep-separate')}>Keep separate</button>
      </div>
    </div>
  ))
}

function ConflictsPanel({ onChanged }) {
  const [conflicts, setConflicts] = useState([])

  async function load() {
    const data = await api.conflicts()
    setConflicts(data.pending_conflicts || [])
  }
  useEffect(() => { load() }, [])

  async function resolve(conflictId, resolution) {
    await api.resolveConflict(conflictId, resolution)
    await load()
    onChanged()
  }

  if (!conflicts.length) return <div className="empty-state">No cross-source conflicts detected.</div>

  return conflicts.map((c) => (
    <div className="review-card flag" key={c.conflict_id}>
      <div className="review-card-top">
        <strong>{c.product_name}</strong>
        <span className="badge badge-danger">Disagreement on {c.field_name}</span>
      </div>
      <div className="compare-box">
        <div className="compare-side">
          <div className="side-label">Document A</div>
          <div className="side-value">{c.value_a}</div>
          <div className="side-context">{c.snippet_a}</div>
        </div>
        <div className="compare-side">
          <div className="side-label">Document B</div>
          <div className="side-value">{c.value_b}</div>
          <div className="side-context">{c.snippet_b}</div>
        </div>
      </div>
      <div className="review-actions">
        <button className="btn btn-sm" onClick={() => resolve(c.conflict_id, 'choose_a')}>Accept value A</button>
        <button className="btn btn-sm" onClick={() => resolve(c.conflict_id, 'choose_b')}>Accept value B</button>
      </div>
    </div>
  ))
}

function FieldsPanel({ onChanged }) {
  const [fields, setFields] = useState([])

  async function load() {
    const data = await api.pendingFields()
    setFields(data.fields || [])
  }
  useEffect(() => { load() }, [])

  async function approve(recordId, fieldName) {
    await api.decideField(recordId, fieldName, 'approve')
    await load()
    onChanged()
  }

  if (!fields.length) return <div className="empty-state">All fields meet the confidence threshold.</div>

  return fields.map((f) => (
    <div className="review-card" key={`${f.record_id}-${f.field_name}`}>
      <div className="review-card-top">
        <strong>{f.product_name}</strong>
        <span className="badge badge-warning">Score {Math.round(f.confidence.overall_score * 100)}%</span>
      </div>
      <div style={{ fontSize: '0.85rem' }}>
        Field: <strong>{f.field_name}</strong> · Value: <span className="mono" style={{ color: 'var(--amber)' }}>{f.normalized_value}</span>
      </div>
      <div className="text-muted" style={{ fontSize: '0.76rem' }}>{f.confidence.explainability}</div>
      <div className="review-actions">
        <button className="btn btn-success btn-sm" onClick={() => approve(f.record_id, f.field_name)}>Confirm value</button>
      </div>
    </div>
  ))
}

export default function Review() {
  const { refresh } = useStatus()

  return (
    <div className="panel-card">
      <div className="panel-head">
        <h1>Human review</h1>
        <p>Clarion asks for confirmation whenever identity matches are uncertain, sources disagree, or confidence drops below threshold.</p>
      </div>

      <div className="subnav">
        <NavLink to="duplicates" className={({ isActive }) => (isActive ? 'active' : '')}>Duplicate proposals</NavLink>
        <NavLink to="conflicts" className={({ isActive }) => (isActive ? 'active' : '')}>Cross-source conflicts</NavLink>
        <NavLink to="fields" className={({ isActive }) => (isActive ? 'active' : '')}>Low-confidence fields</NavLink>
      </div>

      <Routes>
        <Route index element={<Navigate to="duplicates" replace />} />
        <Route path="duplicates" element={<DuplicatesPanel onChanged={refresh} />} />
        <Route path="conflicts" element={<ConflictsPanel onChanged={refresh} />} />
        <Route path="fields" element={<FieldsPanel onChanged={refresh} />} />
      </Routes>
    </div>
  )
}
