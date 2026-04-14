import { useEffect, useState } from 'react'
import { api } from '../api/client'
import LOBChart from '../components/LOBChart'
import StageTable from '../components/StageTable'
import SparklineGrid from '../components/SparklineGrid'

export default function Overview({ hours, metrics }) {
  const [chartData, setChartData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.getChartData(hours)
      .then(setChartData)
      .finally(() => setLoading(false))
  }, [hours])

  if (loading) return <div className="loading-spinner"><div className="spinner" /></div>

  if (!metrics || !chartData) return <div className="empty">Failed to load data</div>

  const bottleneckStage = metrics.bottleneck_stage

  return (
    <div className="left-col">
      {/* Bottleneck Alert */}
      {bottleneckStage && (
        <div className="alert-box critical">
          <div className="alert-title" style={{ color: 'var(--critical)' }}>
            ⚠ Binding Constraint Detected
          </div>
          <div className="alert-text">
            <b>{bottleneckStage.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</b> is the current bottleneck.
            Balance Score: <b>{metrics.balance_score?.toFixed(3)}</b> — System throughput capped at{' '}
            <b>{metrics.overall_throughput_per_hour?.toFixed(1)} pts/hr</b>
          </div>
        </div>
      )}

      {/* LOB Chart */}
      <LOBChart chartData={chartData} bottleneckStage={bottleneckStage} />

      {/* Stage Performance Table */}
      <StageTable stageMetrics={metrics.stage_metrics} bottleneckStage={bottleneckStage} />

      {/* Sparkline Grid */}
      <SparklineGrid stageMetrics={metrics.stage_metrics} />
    </div>
  )
}
