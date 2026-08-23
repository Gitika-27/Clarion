import { createContext, useCallback, useContext, useState } from 'react'
import { api } from '../api'

const StatusContext = createContext(null)

const emptyMetrics = {
  total_records: 0,
  auto_published: 0,
  pending_conflicts: 0,
  pending_fields: 0,
  outlier_count: 0,
  avg_trust_score: 0,
}

export function StatusProvider({ children }) {
  const [metrics, setMetrics] = useState(emptyMetrics)
  const [records, setRecords] = useState([])

  const refresh = useCallback(async () => {
    try {
      const statusData = await api.status()
      if (statusData?.ok) setMetrics(statusData.metrics)
    } catch (err) {
      console.error('Status refresh failed', err)
    }
    try {
      const recordsData = await api.records()
      if (recordsData?.ok) setRecords(recordsData.records)
    } catch (err) {
      console.error('Records refresh failed', err)
    }
  }, [])

  return (
    <StatusContext.Provider value={{ metrics, records, refresh }}>
      {children}
    </StatusContext.Provider>
  )
}

export function useStatus() {
  const ctx = useContext(StatusContext)
  if (!ctx) throw new Error('useStatus must be used within StatusProvider')
  return ctx
}
