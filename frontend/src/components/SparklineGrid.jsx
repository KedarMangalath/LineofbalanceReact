import { useMemo } from 'react'

function Sparkline({ points, color = 'var(--bar-blue)', width = 80, height = 28 }) {
  if (!points || points.length < 2) return null

  const min = Math.min(...points)
  const max = Math.max(...points)
  const range = max - min || 1
  const pad = 2

  const pathD = points.map((v, i) => {
    const x = pad + (i / (points.length - 1)) * (width - pad * 2)
    const y = pad + (1 - (v - min) / range) * (height - pad * 2)
    return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')

  // Area fill
  const lastX = pad + ((points.length - 1) / (points.length - 1)) * (width - pad * 2)
  const areaD = `${pathD} L${lastX.toFixed(1)},${height - pad} L${pad},${height - pad} Z`

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ display: 'block' }}>
      <path d={areaD} fill={color} opacity={0.1} />
      <path d={pathD} fill="none" stroke={color} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export default function SparklineGrid({ stageMetrics, chartHistory }) {
  const stages = useMemo(() => {
    if (!stageMetrics) return []
    const stageNames = {
      admission: 'ADM', triage: 'TRI', diagnostics: 'DX', surgical: 'SRG',
      recovery_pacu: 'PACU', ward_icu: 'WRD', discharge: 'DC',
    }
    return Object.entries(stageMetrics).map(([key, sm]) => {
      // Generate synthetic trend points from current value
      const current = sm.actual_throughput_per_hour
      const points = chartHistory?.[key] || Array.from({ length: 20 }, (_, i) => {
        const noise = Math.sin(i * 0.8 + key.length) * current * 0.15
        return Math.max(0, current + noise)
      })
      const trend = points.length >= 2 ? points[points.length - 1] - points[points.length - 2] : 0
      const trendPct = points.length >= 2 && points[points.length - 2] !== 0
        ? (trend / points[points.length - 2]) * 100 : 0

      return {
        key,
        label: stageNames[key] || key.slice(0, 3).toUpperCase(),
        value: current.toFixed(1),
        points,
        trendPct,
        color: trendPct < -5 ? 'var(--critical)' : trendPct > 5 ? 'var(--success)' : 'var(--bar-blue)',
      }
    })
  }, [stageMetrics, chartHistory])

  if (!stages.length) return null

  return (
    <div className="card">
      <div className="card-header">
        <div className="card-title">Throughput Trend</div>
      </div>
      <div className="spark-grid">
        {stages.map(s => (
          <div className="spark-cell" key={s.key}>
            <div className="spark-header">
              <span className="spark-label">{s.label}</span>
              <span className="spark-value" style={{ color: s.color }}>{s.value}</span>
            </div>
            <Sparkline points={s.points} color={s.color} />
          </div>
        ))}
      </div>
    </div>
  )
}
