import { useEffect, useRef, useState } from 'react'
import { api } from '../api'

export default function ReceiptModal({ recordId, fieldName, onClose, onApproved }) {
  const dialogRef = useRef(null)
  const [receipt, setReceipt] = useState(null)

  useEffect(() => {
    if (!recordId || !fieldName) return
    let cancelled = false
    api.receipt(recordId, fieldName).then((data) => {
      if (!cancelled && data.ok) setReceipt(data.receipt)
    })
    return () => { cancelled = true }
  }, [recordId, fieldName])

  useEffect(() => {
    if (recordId && fieldName) dialogRef.current?.showModal()
    else dialogRef.current?.close()
  }, [recordId, fieldName])

  async function handleApprove() {
    await api.decideField(recordId, fieldName, 'approve')
    onApproved?.()
    onClose()
  }

  if (!recordId || !fieldName) return null

  const conf = receipt?.confidence_breakdown || {}
  const sref = receipt?.source_ref || {}

  const factor = (label, key) => (
    <div className="conf-factor">
      <div className="conf-factor-top">
        <span className="fname">{label}</span>
        <span className="fval mono">{(conf[key] ?? 0).toFixed(2)}</span>
      </div>
      <div className="conf-bar-track">
        <div className="conf-bar-fill" style={{ width: `${(conf[key] ?? 0) * 100}%` }} />
      </div>
    </div>
  )

  return (
    <dialog ref={dialogRef} onClose={onClose}>
      <div className="modal-head">
        <h2>{fieldName.replace(/_/g, ' ').toUpperCase()}</h2>
        <button className="modal-close" onClick={onClose}>&times;</button>
      </div>
      <div className="modal-body">
        {!receipt ? (
          <p className="text-muted">Loading citation…</p>
        ) : (
          <>
            <div className="receipt-value">{receipt.normalized_value}</div>

            <div className="block-label">Source snippet</div>
            <div className="receipt-snippet">{receipt.source_snippet || 'No textual context available'}</div>
            <div className="receipt-source-ref">
              Document: {sref.doc_id || recordId} · Source: {sref.source_type || 'pdf'} · Page: {sref.page || '1'} · Paragraph: {sref.paragraph || '1'}
            </div>

            <div className="block-label">Confidence breakdown</div>
            {factor('Self-consistency', 'self_consistency')}
            {factor('Verification agreement', 'verification_agreement')}
            {factor('Sanity rule compliance', 'sanity_compliance')}
            {factor('Source quality', 'source_quality')}

            <div className="receipt-explain">{receipt.explainability}</div>
          </>
        )}
      </div>
      <div className="modal-footer">
        <button className="btn" onClick={onClose}>Close</button>
        <button className="btn btn-success" onClick={handleApprove}>Confirm value</button>
      </div>
    </dialog>
  )
}
