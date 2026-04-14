import { useState } from 'react'
import { api } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const STAGES = ['admission', 'triage', 'diagnostics', 'surgical', 'recovery_pacu', 'ward_icu', 'discharge']
const STAGE_LABELS = { admission: 'ADM', triage: 'TRI', diagnostics: 'DX', surgical: 'SRG', recovery_pacu: 'PACU', ward_icu: 'WRD', discharge: 'DC' }
const DEFAULT_CAPS = { admission: 10, triage: 8, diagnostics: 15, surgical: 6, recovery_pacu: 12, ward_icu: 100, discharge: 5 }

export default function Simulation() {
  const [duration, setDuration] = useState(168)
  const [arrivalRate, setArrivalRate] = useState(8)
  const [diagMult, setDiagMult] = useState(1.0)
  const [dischMult, setDischMult] = useState(1.0)
  const [caps, setCaps] = useState({ ...DEFAULT_CAPS })
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  const runSim = async () => {
    setLoading(true)
    const capOverrides = {}
    const stMults = {}
    for (const [k, v] of Object.entries(caps)) {
      if (v !== DEFAULT_CAPS[k]) capOverrides[k] = v
    }
    if (diagMult !== 1.0) stMults.diagnostics = diagMult
    if (dischMult !== 1.0) stMults.discharge = dischMult

    try {
      const res = await api.runSimulation({
        duration_hours: duration,
        arrival_rate: arrivalRate,
        capacity_overrides: capOverrides,
        service_time_multipliers: stMults,
      })
      setResults(res)
    } finally {
      setLoading(false)
    }
  }

  const throughputData = results ? STAGES.filter(s => results.baseline.stage_throughput_per_hour[s] !== undefined).map(s => ({
    stage: STAGE_LABELS[s],
    baseline: results.baseline.stage_throughput_per_hour[s] || 0,
    scenario: results.scenario.stage_throughput_per_hour[s] || 0,
  })) : []

  const delta = results ? results.scenario.patients_completed - results.baseline.patients_completed : 0

  return (
    <div className="left-col">
      {/* Controls Card */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">What-If Scenario Parameters</div>
        </div>
        <div className="card-body">
          <div className="sim-controls">
            <div className="sim-field">
              <label>Duration (hours)</label>
              <input type="number" value={duration} onChange={e => setDuration(+e.target.value)} min={24} max={720} />
            </div>
            <div className="sim-field">
              <label>Arrival Rate (pts/hr)</label>
              <input type="number" value={arrivalRate} onChange={e => setArrivalRate(+e.target.value)} min={1} max={30} step={0.5} />
            </div>
            <div className="sim-field">
              <label>Diagnostics Speed ({diagMult}x)</label>
              <input type="range" min={0.3} max={2} step={0.1} value={diagMult} onChange={e => setDiagMult(+e.target.value)} />
            </div>
            <div className="sim-field">
              <label>Discharge Speed ({dischMult}x)</label>
              <input type="range" min={0.3} max={2} step={0.1} value={dischMult} onChange={e => setDischMult(+e.target.value)} />
            </div>
          </div>

          <div style={{ marginTop: 14 }}>
            <label style={{ fontSize: 10, color: 'var(--text-ter)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '.3px', display: 'block', marginBottom: 6 }}>
              Capacity Overrides
            </label>
            <div className="sim-caps">
              {STAGES.map(s => (
                <div key={s}>
                  <label>{STAGE_LABELS[s]}</label>
                  <input type="number" value={caps[s]} onChange={e => setCaps({ ...caps, [s]: +e.target.value })} min={1} max={200} />
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginTop: 14 }}>
            <button className="run-btn" onClick={runSim} disabled={loading}>
              {loading ? (
                <><span className="spinner" style={{ width: 14, height: 14, borderWidth: 1.5 }} /> Running...</>
              ) : (
                <><span>▶</span> Run Simulation</>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {results && (
        <>
          {/* KPI comparison */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">Simulation Results</div>
            </div>
            <div style={{ padding: 0 }}>
              <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
                <div className="kpi-cell">
                  <div className="kpi-label">Baseline Completed</div>
                  <div className="kpi-value" style={{ color: 'var(--bar-blue)' }}>{results.baseline.patients_completed}</div>
                  <div className="kpi-sub">patients</div>
                </div>
                <div className="kpi-cell">
                  <div className="kpi-label">Scenario Completed</div>
                  <div className="kpi-value" style={{ color: delta >= 0 ? 'var(--success)' : 'var(--critical)' }}>
                    {results.scenario.patients_completed}
                  </div>
                  <div className="kpi-sub">{delta >= 0 ? '+' : ''}{delta} vs baseline</div>
                </div>
                <div className="kpi-cell">
                  <div className="kpi-label">Predicted Bottleneck</div>
                  <div className="kpi-value" style={{ color: 'var(--warning)' }}>
                    {STAGE_LABELS[results.scenario.predicted_bottleneck?.stage] || results.scenario.predicted_bottleneck?.stage || '—'}
                  </div>
                  <div className="kpi-sub">new constraint</div>
                </div>
              </div>
            </div>
          </div>

          {/* Throughput comparison chart */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">Throughput Comparison</div>
              <div className="legend">
                <span className="legend-item"><span style={{ width: 10, height: 4, background: 'var(--bar-blue)', borderRadius: 1, display: 'inline-block' }} /> Baseline</span>
                <span className="legend-item"><span style={{ width: 10, height: 4, background: 'var(--success)', borderRadius: 1, display: 'inline-block' }} /> Scenario</span>
              </div>
            </div>
            <div style={{ padding: '8px 8px 4px' }}>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={throughputData} barCategoryGap="20%">
                  <CartesianGrid vertical={false} stroke="var(--border-light)" strokeDasharray="3 3" />
                  <XAxis dataKey="stage" tick={{ fontSize: 10, fill: 'var(--text-ter)' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: 'var(--text-ter)' }} axisLine={false} tickLine={false}
                    label={{ value: 'pts/hr', angle: -90, position: 'insideLeft', fontSize: 9, fill: 'var(--text-ter)' }} />
                  <Tooltip />
                  <Bar dataKey="baseline" name="Baseline" fill="var(--bar-blue)" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="scenario" name="Scenario" fill="var(--success)" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
