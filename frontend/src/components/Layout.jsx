import { useEffect } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useStatus } from '../context/StatusContext'

export default function Layout() {
  const { metrics, refresh } = useStatus()

  useEffect(() => {
    refresh()
  }, [refresh])

  const reviewCount = metrics.pending_conflicts + metrics.pending_fields
  const trustPct = Math.round((metrics.avg_trust_score || 0) * 100)

  return (
    <div className="app-shell">
      <div className="topbar">
        <div className="brand">
          <img src="/logo-full.png" alt="Clarion" />
        </div>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card accent-amber">
          <div className="kpi-label">Extracted records</div>
          <div className="kpi-value">{metrics.total_records}</div>
          <div className="kpi-sub">Parsed from PDFs and CSV catalogs</div>
        </div>
        <div className="kpi-card accent-success">
          <div className="kpi-label">Auto-published</div>
          <div className="kpi-value">{metrics.auto_published}</div>
          <div className="kpi-sub">High trust, passed domain sanity</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Review queue</div>
          <div className="kpi-value">{reviewCount}</div>
          <div className="kpi-sub">Duplicates, conflicts, low confidence</div>
        </div>
        <div className="kpi-card accent-danger">
          <div className="kpi-label">Catalog outliers</div>
          <div className="kpi-value">{metrics.outlier_count}</div>
          <div className="kpi-sub">Statistical anomalies</div>
        </div>
        <div className="kpi-card accent-amber">
          <div className="kpi-label">Trust score</div>
          <div className="kpi-value">{trustPct}%</div>
          <div className="kpi-sub">Weighted verified fields</div>
        </div>
      </div>

      <nav className="nav">
        <NavLink to="/" end>Upload and run</NavLink>
        <NavLink to="/catalog">
          Catalog<span className="nav-count">{metrics.total_records}</span>
        </NavLink>
        <NavLink to="/review">
          Review<span className="nav-count">{reviewCount}</span>
        </NavLink>
        <NavLink to="/outliers">
          Outliers<span className="nav-count">{metrics.outlier_count}</span>
        </NavLink>
        <NavLink to="/export">Export</NavLink>
      </nav>

      <Outlet />
    </div>
  )
}
