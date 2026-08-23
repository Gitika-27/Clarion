const BASE = ''

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: options.body && !(options.body instanceof FormData)
      ? { 'Content-Type': 'application/json', ...options.headers }
      : options.headers,
    ...options,
  })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    throw new Error(data?.detail || `Request failed: ${res.status}`)
  }
  return data
}

export const api = {
  status: () => request('/api/pipeline/status'),
  runSample: () => request('/api/pipeline/run-sample', { method: 'POST' }),
  upload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request('/api/upload', { method: 'POST', body: formData })
  },
  records: () => request('/api/records'),
  receipt: (recordId, fieldName) => request(`/api/receipts/${recordId}/${fieldName}`),
  decideField: (recordId, fieldName, action, customValue) =>
    request('/api/review/fields/decide', {
      method: 'POST',
      body: JSON.stringify({ record_id: recordId, field_name: fieldName, action, custom_value: customValue }),
    }),
  identityProposals: () => request('/api/identity/proposals'),
  decideIdentity: (proposalId, action) =>
    request(`/api/identity/proposals/${proposalId}/${action}`, { method: 'POST' }),
  conflicts: () => request('/api/review/conflicts'),
  resolveConflict: (conflictId, resolution) =>
    request('/api/review/conflicts/resolve', {
      method: 'POST',
      body: JSON.stringify({ conflict_id: conflictId, resolution }),
    }),
  pendingFields: () => request('/api/review/fields'),
  outliers: (zThreshold) => request(`/api/catalog/outliers?z_threshold=${zThreshold}`),
  exportCsvUrl: (format) => `${BASE}/api/export/csv?format=${format}`,
  exportJsonUrl: () => `${BASE}/api/export/json`,
}
