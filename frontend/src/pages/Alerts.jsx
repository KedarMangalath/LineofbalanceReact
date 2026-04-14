import { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function Alerts() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.getAlerts().then(setData).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>
  if (!data) return <div className="empty">Failed to load alerts</div>

  const { alerts, summary } = data

  return (
    <div className="left-col">
      {/* Alert Summary KPI */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">Alert Summary</div>
        </div>
        <div style={{ padding: 0 }}>
          <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
            <div className="kpi-cell">
              <div className="kpi-label">Total Alerts</div>
              <div className="kpi-value" style={{ color: 'var(--primary)' }}>{summary.total}</div>
            </div>
            <div className="kpi-cell">
              <div className="kpi-label">Critical</div>
              <div className="kpi-value" style={{ color: 'var(--critical)' }}>{summary.critical}</div>
            </div>
            <div className="kpi-cell">
              <div className="kpi-label">Warning</div>
              <div className="kpi-value" style={{ color: 'var(--warning)' }}>{summary.warning}</div>
            </div>
            <div className="kpi-cell">
              <div className="kpi-label">Info</div>
              <div className="kpi-value" style={{ color: 'var(--text-sec)' }}>{summary.info}</div>
            </div>
          </div>
        </div>
      </div>

      {/* All clear banner */}
      {alerts.length === 0 && (
        <div className="alert-box success">
          <div className="alert-title" style={{ color: 'var(--success)' }}>All Clear</div>
          <div className="alert-text">All metrics within normal thresholds. No active alerts.</div>
        </div>
      )}

      {/* Alert List */}
      {alerts.length > 0 && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">Active Alerts</div>
            <span style={{ fontSize: 10, color: 'var(--text-ter)' }}>{alerts.length} active</span>
          </div>
          <div className="log-wrap" style={{ maxHeight: 'none' }}>
            {alerts.map((alert, i) => {
              const sevClass = alert.severity === 'critical' ? 'critical' : alert.severity === 'warning' ? 'warning' : 'info'
              return (
                <div key={i} style={{ padding: '10px 14px', borderBottom: '1px solid var(--border-light)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span className={`severity-badge sev-${alert.severity}`}>
                        {alert.severity.toUpperCase()}
                      </span>
                      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)' }}>
                        {alert.metric_name}
                      </span>
                    </div>
                    {alert.stage && (
                      <span style={{ fontSize: 10, color: 'var(--text-ter)' }}>
                        {alert.stage}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-sec)', lineHeight: 1.5 }}>
                    {alert.message}
                  </div>
                  <div style={{ display: 'flex', gap: 16, marginTop: 4, fontSize: 10, color: 'var(--text-ter)' }}>
                    <span>Current: <b style={{ color: 'var(--text)' }}>{alert.current_value.toFixed(1)}</b></span>
                    <span>Threshold: <b style={{ color: 'var(--text)' }}>{alert.threshold_value.toFixed(1)}</b></span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
