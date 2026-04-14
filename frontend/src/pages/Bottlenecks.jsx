import { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function Bottlenecks({ hours }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [expandedAction, setExpandedAction] = useState(null)

  useEffect(() => {
    setLoading(true)
    api.getBottlenecks(hours).then(setData).finally(() => setLoading(false))
  }, [hours])

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>
  if (!data) return <div className="empty">Failed to load bottleneck data</div>

  const primary = data.primary_bottleneck
  const secondary = data.secondary_bottleneck
  const allStages = data.all_stages_ranked || []

  // Generate optimization actions from analysis
  const actions = [
    primary && {
      severity: 'critical',
      label: `Increase ${primary.display_name} capacity`,
      detail: `Current utilization is ${primary.utilization_percent.toFixed(1)}% with throughput ${primary.actual_throughput.toFixed(1)} vs target ${primary.target_throughput.toFixed(1)} pts/hr. Adding resources can reduce cycle time and eliminate the binding constraint.`,
      compliance: 'Staffing changes require department head approval per hospital policy.',
    },
    secondary && {
      severity: 'high',
      label: `Monitor ${secondary.display_name} — approaching constraint`,
      detail: `Secondary constraint score: ${secondary.constraint_score.toFixed(3)}. WIP count: ${secondary.wip_count}. May become binding if primary is resolved without addressing secondary.`,
    },
    ...allStages.filter(s => s.constraint_score > 0.3 && s !== primary && s !== secondary).map(s => ({
      severity: 'medium',
      label: `Review ${s.display_name} performance`,
      detail: `Constraint score ${s.constraint_score.toFixed(3)}. Throughput deviation from target may indicate emerging issues.`,
    })),
  ].filter(Boolean)

  // Generate predictions
  const predictions = [
    primary && {
      color: 'var(--critical)',
      stage: primary.display_name,
      msg: `Throughput limited to ${primary.actual_throughput.toFixed(1)} pts/hr — ${((1 - primary.actual_throughput / primary.target_throughput) * 100).toFixed(0)}% below target`,
      eta: 'Now',
    },
    secondary && {
      color: 'var(--warning)',
      stage: secondary.display_name,
      msg: `Risk of becoming binding if ${primary?.display_name} is resolved`,
      eta: 'Next 2-4h',
    },
    {
      color: 'var(--bar-blue)',
      stage: 'System',
      msg: `Balance score ${data.primary_bottleneck?.constraint_score > 0.5 ? 'critical' : 'elevated'} — flow optimization recommended`,
      eta: 'Ongoing',
    },
  ].filter(Boolean)

  return (
    <div className="main-grid" style={{ padding: 0 }}>
      {/* LEFT — Constraint Analysis */}
      <div className="left-col">
        {/* Constraint Score Table */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Constraint Score by Stage</div>
          </div>
          <div>
            <div className="stage-header">
              <div>Stage</div>
              <div>Constraint Level</div>
              <div style={{ textAlign: 'right' }}>Score</div>
              <div style={{ textAlign: 'right' }}>Thru.</div>
              <div style={{ textAlign: 'right' }}>Status</div>
            </div>
            {allStages.map(s => {
              const isPrimary = s === primary
              const isSecondary = s === secondary
              const pct = Math.min(s.constraint_score * 100, 100)
              const barColor = s.constraint_score > 0.5 ? 'var(--critical)' : s.constraint_score > 0.3 ? 'var(--warning)' : 'var(--bar-blue)'
              return (
                <div key={s.display_name} className={`stage-row ${isPrimary ? 'binding' : ''}`}>
                  <div className="stage-name">{s.display_name}</div>
                  <div>
                    <div className="bar-track">
                      <div className="bar-fill" style={{ width: `${pct}%`, background: barColor }} />
                    </div>
                  </div>
                  <div className="cell-right">{s.constraint_score.toFixed(3)}</div>
                  <div className="cell-right">{s.actual_throughput.toFixed(1)}</div>
                  <div style={{ textAlign: 'right' }}>
                    {isPrimary ? (
                      <span className="badge-binding">BINDING</span>
                    ) : isSecondary ? (
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

        {/* Analysis */}
        {data.analysis && (
          <div className="card">
            <div className="card-header">
              <div className="card-title">Analysis Report</div>
            </div>
            <div className="card-body" style={{ fontSize: 11.5, lineHeight: 1.6, color: 'var(--text-sec)' }}>
              {data.analysis.split('\n').filter(Boolean).map((line, i) => (
                <p key={i} style={{ marginBottom: 6 }}>{line}</p>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* RIGHT — Agent Panels */}
      <div className="right-col">
        {/* Monitor Agent */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="card-badge" style={{ background: '#0057B8' }} />
              <div>
                <span className="card-title">Monitor Agent</span>{' '}
                <span className="card-subtitle">— Overseer</span>
              </div>
            </div>
          </div>
          <div style={{ padding: 14 }}>
            {primary && (
              <div className="alert-box critical">
                <div className="alert-title" style={{ color: 'var(--critical)' }}>
                  Binding Constraint: {primary.display_name}
                </div>
                <div className="alert-text">
                  Throughput: {primary.actual_throughput.toFixed(1)}/{primary.target_throughput.toFixed(1)} pts/hr.
                  Utilization: {primary.utilization_percent.toFixed(1)}%. WIP: {primary.wip_count}.
                  System ceiling capped at this stage.
                </div>
              </div>
            )}
            {secondary && (
              <div className="alert-box warning">
                <div className="alert-title" style={{ color: 'var(--warning)' }}>
                  Backlog Risk: {secondary.display_name}
                </div>
                <div className="alert-text">
                  Score: {secondary.constraint_score.toFixed(3)}.
                  May become binding if primary constraint shifts.
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Optimization Agent */}
        <div className="card">
          <div className="card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="card-badge" style={{ background: '#6D28D9' }} />
              <div>
                <span className="card-title">Optimization Agent</span>{' '}
                <span className="card-subtitle">— Fixer</span>
              </div>
            </div>
            <span style={{ fontSize: 10, color: 'var(--text-ter)' }}>{actions.length} levers</span>
          </div>
          <div style={{ padding: 6 }}>
            {actions.map((a, i) => (
              <div key={i} className={`action-item ${expandedAction === i ? 'expanded' : ''}`}
                onClick={() => setExpandedAction(expandedAction === i ? null : i)}>
                <div className="action-header">
                  <span className="action-label">{a.label}</span>
                  <span className={`severity-badge sev-${a.severity}`}>{a.severity.toUpperCase()}</span>
                </div>
                {expandedAction === i && (
                  <div className="action-detail">
                    <p>{a.detail}</p>
                    {a.compliance && (
                      <div style={{
                        fontSize: 10, color: 'var(--warning)', background: 'var(--warning-bg)',
                        border: '1px solid var(--warning-border)', padding: '5px 8px', borderRadius: 4, margin: '8px 0'
                      }}>
                        {a.compliance}
                      </div>
                    )}
                    <button className="apply-btn">Apply Lever</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Predictive Nudges */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Predictive Nudges</div>
          </div>
          <div style={{ padding: 6 }}>
            {predictions.map((p, i) => (
              <div key={i} className="pred-item">
                <div className="pred-dot" style={{ background: p.color }} />
                <div style={{ flex: 1 }}>
                  <div className="pred-stage">{p.stage}</div>
                  <div className="pred-msg">{p.msg}</div>
                </div>
                <div className="pred-eta">{p.eta}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
