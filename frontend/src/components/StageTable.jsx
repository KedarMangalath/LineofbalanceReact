export default function StageTable({ stageMetrics, bottleneckStage }) {
  if (!stageMetrics) return null

  const stageNames = {
    admission: { name: 'Admission & Registration', short: 'ADM' },
    triage: { name: 'Triage & Assessment', short: 'TRI' },
    diagnostics: { name: 'Diagnostics', short: 'DX' },
    surgical: { name: 'Surgical / Procedure', short: 'SRG' },
    recovery_pacu: { name: 'Recovery (PACU)', short: 'PACU' },
    ward_icu: { name: 'Ward / ICU Stay', short: 'WRD' },
    discharge: { name: 'Discharge & Handoff', short: 'DC' },
  }

  const rows = Object.entries(stageMetrics).map(([key, sm]) => {
    const info = stageNames[key] || { name: key, short: key.slice(0, 3).toUpperCase() }
    const ratio = sm.avg_service_time_minutes / sm.takt_time_minutes
    const isBinding = key === bottleneckStage
    const isWatch = !isBinding && ratio > 0.85
    return {
      key,
      name: info.name,
      cycleTime: sm.avg_service_time_minutes,
      targetTime: sm.takt_time_minutes,
      throughput: sm.actual_throughput_per_hour,
      ratio,
      isBinding,
      isWatch,
    }
  })

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Stage Performance Detail</div>
      </div>
      <div>
        <div className="stage-header">
          <div>Stage</div>
          <div>Cycle Time vs Target</div>
          <div style={{ textAlign: 'right' }}>Cycle</div>
          <div style={{ textAlign: 'right' }}>Thru.</div>
          <div style={{ textAlign: 'right' }}>Status</div>
        </div>
        {rows.map(row => {
          const pct = Math.min((row.ratio) * 100, 150)
          const barColor = row.isBinding ? 'var(--critical)' : row.isWatch ? 'var(--warning)' : 'var(--bar-blue)'
          return (
            <div key={row.key} className={`stage-row ${row.isBinding ? 'binding' : ''}`}>
              <div className="stage-name">{row.name}</div>
              <div>
                <div className="bar-track">
                  <div className="bar-mid" />
                  <div className="bar-fill" style={{ width: `${Math.min(pct, 100)}%`, background: barColor }} />
                </div>
              </div>
              <div className="cell-right">{row.cycleTime.toFixed(0)}m</div>
              <div className="cell-right">{row.throughput.toFixed(1)}</div>
              <div style={{ textAlign: 'right' }}>
                {row.isBinding ? (
                  <span className="badge-binding">BINDING</span>
                ) : row.isWatch ? (
                  <span className="status-watch">Watch</span>
                ) : (
                  <span className="status-normal">Normal</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
