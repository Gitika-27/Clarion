import { api } from '../api'
import { useStatus } from '../context/StatusContext'

export default function Export() {
  const { records } = useStatus()
  const preview = records.slice(0, 5)

  return (
    <div className="panel-card">
      <div className="panel-head">
        <h1>Structured export</h1>
        <p>Export verified, cited product records for downstream commerce, ERP, or the UniHack 252-column delivery format.</p>
      </div>

      <div className="actions-row" style={{ marginTop: 0 }}>
        <a className="btn btn-primary" href={api.exportCsvUrl('unihack')}>Download UniHack 252-column CSV</a>
        <a className="btn" href={api.exportCsvUrl('standard')}>Download standard CSV</a>
        <a className="btn" href={api.exportJsonUrl()}>Download verified JSON</a>
      </div>

      <div className="block-label">Export preview — first 5 records</div>
      {!preview.length ? (
        <div className="empty-state">No records to preview. Run the demo pipeline first.</div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                <th>Part number</th>
                <th>Mfg part num</th>
                <th>Part description</th>
                <th>Manufacturer</th>
                <th>Brand</th>
                <th>Attributes (1..50)</th>
              </tr>
            </thead>
            <tbody>
              {preview.map((r) => (
                <tr key={r.record_id}>
                  <td className="mono">{r.mfg_part_num}</td>
                  <td className="mono">{r.mfg_part_num}</td>
                  <td>{r.product_name}</td>
                  <td>{r.manufacturer}</td>
                  <td>{r.brand}</td>
                  <td style={{ fontSize: '0.78rem' }}>
                    {Object.entries(r.fields).map(([k, v]) => `${k}: ${v.normalized_value}`).join(' · ')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
