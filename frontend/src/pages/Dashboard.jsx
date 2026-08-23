import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useStatus } from '../context/StatusContext'

export default function Dashboard() {
  const { refresh } = useStatus()
  const navigate = useNavigate()
  const fileInputRef = useRef(null)
  const [dragOver, setDragOver] = useState(false)
  const [status, setStatus] = useState(null)
  const [recordCount, setRecordCount] = useState(0)

  async function runDemo() {
    setStatus({ kind: 'pending', message: 'Running the pipeline on the sample dataset…' })
    try {
      const data = await api.runSample()
      if (data.ok) {
        setRecordCount(data.record_count)
        setStatus({ kind: 'ok', message: `Done — ${data.record_count} product records extracted and verified.` })
        await refresh()
      }
    } catch (err) {
      setStatus({ kind: 'error', message: err.message })
    }
  }

  async function handleFile(file) {
    if (!file) return
    setStatus({ kind: 'pending', message: `Uploading and parsing ${file.name}…` })
    try {
      const data = await api.upload(file)
      if (data.ok) {
        setStatus({ kind: 'ok', message: `Parsed ${file.name}. View it in the catalog.` })
        await refresh()
      }
    } catch (err) {
      setStatus({ kind: 'error', message: err.message })
    }
  }

  return (
    <div className="panel-card">
      <div className="panel-head">
        <h1>Upload a document or run the sample dataset</h1>
        <p>Accepts PDF datasheets, CSV parts catalogs, and JPG or PNG images.</p>
      </div>

      <div
        className={`dropzone${dragOver ? ' dragover' : ''}`}
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={(e) => { e.preventDefault(); setDragOver(false) }}
        onDrop={(e) => {
          e.preventDefault()
          setDragOver(false)
          const file = e.dataTransfer.files[0]
          if (file) handleFile(file)
        }}
      >
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M12 3v12m0-12l-4 4m4-4l4 4M4 17v2a2 2 0 002 2h12a2 2 0 002-2v-2" />
        </svg>
        <h3>Click or drag a file here</h3>
        <p>PDF, CSV, JPG, or PNG</p>
        <input
          ref={fileInputRef}
          type="file"
          style={{ display: 'none' }}
          accept=".pdf,.csv,.jpg,.jpeg,.png"
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </div>

      <div className="actions-row">
        <button className="btn btn-primary" onClick={runDemo}>Run demo pipeline on sample dataset</button>
        {recordCount > 0 && (
          <>
            <a className="btn btn-success" href={api.exportCsvUrl('unihack')}>
              Download UniHack 252-column CSV
            </a>
            <button className="btn" onClick={() => navigate('/catalog')}>View extracted catalog</button>
          </>
        )}
      </div>

      {status && (
        <div className={`status-banner ${status.kind === 'ok' ? 'ok' : status.kind === 'error' ? 'error' : ''}`}>
          <span className="dot" />
          <span>{status.message}</span>
        </div>
      )}
    </div>
  )
}
