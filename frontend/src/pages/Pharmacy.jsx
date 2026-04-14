import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const STAGE_NAMES = {
  order_receipt: 'Order Receipt', verification: 'Verification',
  compounding: 'Compounding', labelling: 'Dispensing', administration: 'Administration',
}

export default function Pharmacy({ hours }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.getPharmacyMetrics(hours).then(setData).finally(() => setLoading(false))
  }, [hours])

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>
  if (!data) return <div className="empty">Failed to load pharmacy data</div>

  const bnStage = data.bottleneck_stage

  const stageRows = Object.entries(data.throughput_per_hour).map(([key, throughput]) => {
    const queue = data.orders_in_queue[key] || 0
    const isBottleneck = key === bnStage
    return {
      key,
      name: STAGE_NAMES[key] || key,
      throughput,
      queue,
      isBottleneck,
    }
  })

  const queueData = Object.entries(data.orders_in_queue).map(([stage, val]) => ({
    stage: STAGE_NAMES[stage] || stage,
    queue: val,
  }))

  return (
    <div className="left-col">
      {/* Pharmacy KPI strip */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">Pharmacy Medication Turnaround</div>
        </div>
        <div style={{ padding: 0 }}>
          <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
            <div className="kpi-cell">
              <div className="kpi-label">Avg MTAT</div>
              <div className="kpi-value" style={{ color: data.avg_mtat_minutes > 45 ? 'var(--critical)' : 'var(--success)' }}>
                {data.avg_mtat_minutes.toFixed(0)}m
              </div>
              <div className="kpi-sub">{data.avg_mtat_minutes > 45 ? 'Above 45m target' : 'Within target'}</div>
            </div>
            <div className="kpi-cell">
              <div className="kpi-label">Verify Wait</div>
              <div className="kpi-value" style={{ color: 'var(--bar-blue)' }}>
                {data.avg_verification_wait_minutes.toFixed(0)}m
              </div>
              <div className="kpi-sub">avg wait time</div>
            </div>
            <div className="kpi-cell">
              <div className="kpi-label">Compound Time</div>
              <div className="kpi-value" style={{ color: 'var(--text)' }}>
                {data.avg_compounding_time_minutes.toFixed(0)}m
              </div>
              <div className="kpi-sub">avg compounding</div>
            </div>
            <div className="kpi-cell">
              <div className="kpi-label">Bottleneck</div>
              <div className="kpi-value" style={{ color: bnStage ? 'var(--critical)' : 'var(--success)' }}>
                {bnStage ? (STAGE_NAMES[bnStage] || bnStage).split(' ')[0] : 'None'}
              </div>
              <div className="kpi-sub">{bnStage ? 'constraint detected' : 'flow balanced'}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottleneck Alert */}
      {bnStage && (
        <div className="alert-box critical">
          <div className="alert-title" style={{ color: 'var(--critical)' }}>
            ⚠ Pharmacy Bottleneck: {STAGE_NAMES[bnStage] || bnStage}
          </div>
          <div className="alert-text">
            This stage is limiting medication throughput. Queue depth and turnaround time elevated.
          </div>
        </div>
      )}

      {/* Stage Performance Table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">Stage Performance</div>
        </div>
        <div>
          <div className="stage-header" style={{ gridTemplateColumns: '140px 1fr 60px 60px 70px' }}>
            <div>Stage</div>
            <div>Throughput Level</div>
            <div style={{ textAlign: 'right' }}>Thru.</div>
            <div style={{ textAlign: 'right' }}>Queue</div>
            <div style={{ textAlign: 'right' }}>Status</div>
          </div>
          {stageRows.map(row => {
            const maxThru = Math.max(...Object.values(data.throughput_per_hour), 1)
            const pct = (row.throughput / maxThru) * 100
            const barColor = row.isBottleneck ? 'var(--critical)' : row.throughput < 1.5 ? 'var(--warning)' : 'var(--bar-blue)'
            return (
              <div key={row.key} className={`stage-row ${row.isBottleneck ? 'binding' : ''}`}
                style={{ gridTemplateColumns: '140px 1fr 60px 60px 70px' }}>
                <div className="stage-name">{row.name}</div>
                <div>
                  <div className="bar-track">
                    <div className="bar-fill" style={{ width: `${pct}%`, background: barColor }} />
                  </div>
                </div>
                <div className="cell-right">{row.throughput.toFixed(1)}</div>
                <div className="cell-right">{row.queue}</div>
                <div style={{ textAlign: 'right' }}>
                  {row.isBottleneck ? (
                    <span className="badge-binding">BINDING</span>
                  ) : row.throughput < 1.5 ? (
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

      {/* Queue Depth Chart */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">Queue Depth by Stage</div>
        </div>
        <div style={{ padding: '8px 8px 4px' }}>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={queueData} barCategoryGap="20%">
              <CartesianGrid vertical={false} stroke="var(--border-light)" strokeDasharray="3 3" />
              <XAxis dataKey="stage" tick={{ fontSize: 10, fill: 'var(--text-ter)' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: 'var(--text-ter)' }} axisLine={false} tickLine={false} />
              <Tooltip />
              <Bar dataKey="queue" name="Orders" fill="var(--waste)" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
