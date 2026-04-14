import { Routes, Route, NavLink } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { api } from './api/client'
import Overview from './pages/Overview'
import Bottlenecks from './pages/Bottlenecks'
import Simulation from './pages/Simulation'
import Pharmacy from './pages/Pharmacy'
import Alerts from './pages/Alerts'
import AgentChat from './pages/AgentChat'

const navItems = [
  { path: '/', label: 'Overview' },
  { path: '/bottlenecks', label: 'Bottlenecks' },
  { path: '/simulation', label: 'Simulation' },
  { path: '/pharmacy', label: 'Pharmacy' },
  { path: '/alerts', label: 'Alerts' },
  { path: '/chat', label: 'Agent Chat' },
]

const stageNames = {
  admission: 'Admission', triage: 'Triage', diagnostics: 'Diagnostics',
  surgical: 'Surgical', recovery_pacu: 'Recovery', ward_icu: 'Ward/ICU', discharge: 'Discharge',
}

export default function App() {
  const [hours, setHours] = useState(24)
  const [refreshing, setRefreshing] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)
  const [metrics, setMetrics] = useState(null)

  useEffect(() => {
    api.getLOBMetrics(hours).then(setMetrics).catch(() => {})
  }, [hours, refreshKey])

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await api.refreshData()
      setRefreshKey(k => k + 1)
    } finally {
      setRefreshing(false)
    }
  }

  const edWait = metrics?.ed_door_to_provider_minutes || 0
  const orUtil = metrics?.or_utilization_percent || 0
  const bnStage = metrics?.bottleneck_stage
  const throughput = metrics?.overall_throughput_per_hour || 0
  const totalPatients = Math.round(throughput * hours)
  const alos = metrics?.alos_hours || 0
  const balanceScore = metrics?.balance_score || 0

  return (
    <div style={{ minHeight: '100vh' }}>
      {/* NAV */}
      <div className="nav">
        <div className="nav-left">
          <svg width="26" height="26" viewBox="0 0 26 26"><rect width="26" height="26" rx="5" fill="#0057B8"/><path d="M8 13h10M13 8v10" stroke="#fff" strokeWidth="2.2" strokeLinecap="round"/></svg>
          <div>
            <div className="nav-title">LOB Agentic Orchestrator</div>
            <div className="nav-sub">Hospital Patient Flow · Command Center</div>
          </div>
          <div className="nav-tabs">
            {navItems.map(({ path, label }) => (
              <NavLink key={path} to={path} end={path === '/'} className={({ isActive }) => `nav-tab${isActive ? ' active' : ''}`}>
                {label}
              </NavLink>
            ))}
          </div>
        </div>
        <div className="nav-right">
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <div className="status-dot" />
            <span style={{ fontSize: '10.5px', color: 'rgba(255,255,255,.65)' }}>LIVE</span>
          </div>
          <select value={hours} onChange={e => setHours(+e.target.value)} className="nav-btn" style={{ background: 'rgba(255,255,255,.08)' }}>
            {[6, 12, 24, 48, 72].map(h => <option key={h} value={h}>{h}h window</option>)}
          </select>
          <button className="nav-btn" onClick={handleRefresh} disabled={refreshing}>
            {refreshing ? '↻ …' : '↻ Refresh'}
          </button>
        </div>
      </div>

      {/* KPI STRIP */}
      <div className="kpi-strip">
        <div className="kpi-grid">
          <div className="kpi-cell">
            <div className="kpi-label">Total Patients</div>
            <div className="kpi-value" style={{ color: 'var(--primary)' }}>{totalPatients}</div>
            <div className="kpi-sub">last {hours} hours</div>
          </div>
          <div className="kpi-cell">
            <div className="kpi-label">Throughput</div>
            <div className="kpi-value" style={{ color: 'var(--success)' }}>{throughput.toFixed(1)}</div>
            <div className="kpi-sub">patients / hour</div>
          </div>
          <div className="kpi-cell">
            <div className="kpi-label">ALOS</div>
            <div className="kpi-value" style={{ color: alos > 48 ? 'var(--warning)' : 'var(--text)' }}>{alos.toFixed(1)}h</div>
            <div className="kpi-sub">avg length of stay</div>
          </div>
          <div className="kpi-cell">
            <div className="kpi-label">ED Door-to-Provider</div>
            <div className="kpi-value" style={{ color: edWait > 30 ? 'var(--warning)' : 'var(--success)' }}>{edWait.toFixed(0)}m</div>
            <div className="kpi-sub">{edWait > 30 ? 'Above threshold' : 'Within target'}</div>
          </div>
          <div className="kpi-cell">
            <div className="kpi-label">OR Utilization</div>
            <div className="kpi-value" style={{ color: orUtil < 60 ? 'var(--warning)' : 'var(--success)' }}>{orUtil.toFixed(0)}%</div>
            <div className="kpi-sub">{orUtil < 60 ? 'Below target' : 'On target'}</div>
          </div>
          <div className="kpi-cell">
            <div className="kpi-label">Bottleneck</div>
            <div className="kpi-value" style={{ color: bnStage ? 'var(--critical)' : 'var(--success)' }}>
              {bnStage ? (stageNames[bnStage] || bnStage).split(' ')[0] : 'None'}
            </div>
            <div className="kpi-sub">{bnStage ? `balance: ${balanceScore.toFixed(2)}` : 'system balanced'}</div>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div style={{ padding: '16px 24px 24px' }}>
        <Routes>
          <Route path="/" element={<Overview hours={hours} metrics={metrics} key={`o-${refreshKey}`} />} />
          <Route path="/bottlenecks" element={<Bottlenecks hours={hours} key={`b-${refreshKey}`} />} />
          <Route path="/simulation" element={<Simulation key={`s-${refreshKey}`} />} />
          <Route path="/pharmacy" element={<Pharmacy hours={hours} key={`p-${refreshKey}`} />} />
          <Route path="/alerts" element={<Alerts key={`a-${refreshKey}`} />} />
          <Route path="/chat" element={<AgentChat key="chat" />} />
        </Routes>
      </div>
    </div>
  )
}
