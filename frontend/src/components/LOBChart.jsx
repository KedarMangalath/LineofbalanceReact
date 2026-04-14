import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer, Cell } from 'recharts'

export default function LOBChart({ chartData, bottleneckStage }) {
  if (!chartData) return null

  const shortNames = {
    'Admission & Registration': 'ADM',
    'Triage & Assessment': 'TRI',
    'Diagnostics': 'DX',
    'Surgical / Procedure': 'SRG',
    'Recovery (PACU)': 'PACU',
    'Ward / ICU Stay': 'WRD',
    'Discharge & Handoff': 'DC',
  }

  const data = chartData.stages.map((stage, i) => ({
    stage,
    short: shortNames[stage] || stage.split(' ')[0].slice(0, 4).toUpperCase(),
    actual: chartData.actual_throughput[i],
    target: chartData.target_throughput[i],
  }))

  const targetRate = chartData.target_throughput[0] || 10

  // Find bottleneck index
  const bnIdx = bottleneckStage
    ? data.findIndex(d => d.stage.toLowerCase().includes(bottleneckStage.replace('_', ' ').split('_')[0]))
    : data.reduce((minI, d, i, arr) => d.actual < arr[minI].actual ? i : minI, 0)

  const CustomBar = (props) => {
    const { x, y, width, height, index } = props
    const isBn = index === bnIdx
    return (
      <g>
        <rect x={x} y={y} width={width} height={height} rx={3}
          fill={isBn ? 'var(--critical)' : 'var(--bar-blue)'}
          opacity={isBn ? 0.85 : 1}
        />
        {isBn && (
          <rect x={x - 2} y={y - 2} width={width + 4} height={height + 4} rx={4}
            fill="none" stroke="var(--critical)" strokeWidth={1.5} strokeDasharray="4 3"
          />
        )}
      </g>
    )
  }

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null
    const d = payload[0].payload
    return (
      <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: 6, padding: '8px 12px', fontSize: 11 }}>
        <div style={{ fontWeight: 600, marginBottom: 4 }}>{d.stage}</div>
        <div>Actual: <b>{d.actual.toFixed(1)}</b> pts/hr</div>
        <div>Target: <b>{d.target.toFixed(1)}</b> pts/hr</div>
        <div style={{ color: d.actual >= d.target ? 'var(--success)' : 'var(--critical)', marginTop: 2 }}>
          {d.actual >= d.target ? '▲' : '▼'} {((d.actual / d.target - 1) * 100).toFixed(1)}%
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">Line of Balance — Stage Throughput vs Target</div>
          <div className="card-subtitle">Binding constraint highlighted in red. Waste regions shown in amber.</div>
        </div>
        <div className="legend">
          <span className="legend-item"><span className="legend-bar"></span> Stage</span>
          <span className="legend-item"><span className="legend-dash"></span> Target</span>
          <span className="legend-item"><span className="legend-bn"></span> Bottleneck</span>
        </div>
      </div>
      <div style={{ padding: '8px 8px 4px' }}>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data} margin={{ top: 10, right: 10, bottom: 5, left: 0 }} barCategoryGap="20%">
            <CartesianGrid vertical={false} stroke="var(--border-light)" strokeDasharray="3 3" />
            <XAxis dataKey="short" tick={{ fontSize: 10, fill: 'var(--text-ter)' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 10, fill: 'var(--text-ter)' }} axisLine={false} tickLine={false}
              label={{ value: 'pts/hr', angle: -90, position: 'insideLeft', fontSize: 9, fill: 'var(--text-ter)' }} />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(0,0,0,.03)' }} />
            <ReferenceLine y={targetRate} stroke="var(--critical)" strokeDasharray="8 4" strokeWidth={1.5}
              label={{ value: `Target ${targetRate.toFixed(0)}`, position: 'right', fill: 'var(--critical)', fontSize: 9 }} />
            <Bar dataKey="actual" shape={<CustomBar />} radius={[3, 3, 0, 0]}>
              {data.map((_, i) => <Cell key={i} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
