import React, { useMemo } from 'react'
import {
  ResponsiveContainer, LineChart, AreaChart, Line, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine, ComposedChart, Bar,
} from 'recharts'
import { downsample, shortDate } from '../utils/chartHelpers'

function safeAlign(data, ids) {
  if (!data) return null
  const series = ids.map(id => (data[id] || []))
  if (series.some(s => !s.length)) return null
  const dateSets = series.map(s => new Set(s.map(o => o.date)))
  const common = [...dateSets[0]].filter(d => dateSets.every(ds => ds.has(d))).sort()
  if (!common.length) return null
  const result = { dates: common }
  ids.forEach((id, i) => {
    const lookup = new Map(series[i].map(o => [o.date, o.value]))
    result[id] = common.map(d => lookup.get(d))
  })
  return result
}

// ═══════════════════════════════════════════════════════════════════
// VIX CHART — fear gauge with color zones
// ═══════════════════════════════════════════════════════════════════
export function VixChart({ data }) {
  const chartData = useMemo(() => {
    if (!data?.VIXCLS?.length) return []
    return downsample(
      data.VIXCLS.map(o => ({ date: shortDate(o.date), vix: o.value })),
      400
    )
  }, [data])

  if (!chartData.length) return null

  return (
    <div className="card" style={{ borderImage: 'linear-gradient(90deg, #ef4444, #f59e0b) 1' }}>
      <div className="card-title">🔥 VIX · Fear Index</div>
      <div className="card-sub">&gt;30 = panic (MEV liquidation cascades) · &lt;14 = complacency</div>
      <ResponsiveContainer width="100%" height={250}>
        <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="vixGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#ef4444" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(42,63,102,0.5)" strokeWidth={0.5} />
          <XAxis dataKey="date" tick={{ fill: '#a3b1c6', fontSize: 10, fontFamily: "'JetBrains Mono'" }} />
          <YAxis tick={{ fill: '#a3b1c6', fontSize: 10, fontFamily: "'JetBrains Mono'" }} domain={['auto', 'auto']} />
          <Tooltip contentStyle={{ background: '#1a2744', border: '1px solid #ef4444', borderRadius: 8, fontFamily: "'JetBrains Mono'", fontSize: 12, color: '#e2e8f4', padding: '10px 14px' }}
            labelStyle={{ color: '#e2e8f4' }} itemStyle={{ color: '#e2e8f4' }} />
          <ReferenceLine y={30} stroke="#ef4444" strokeDasharray="6 3" strokeWidth={1.5} label={{ value: 'PANIC', fill: '#ef4444', fontSize: 9 }} />
          <ReferenceLine y={22} stroke="#f59e0b" strokeDasharray="4 4" strokeWidth={1} label={{ value: 'ELEVATED', fill: '#f59e0b', fontSize: 9 }} />
          <ReferenceLine y={14} stroke="#22c55e" strokeDasharray="4 4" strokeWidth={1} label={{ value: 'CALM', fill: '#22c55e', fontSize: 9 }} />
          <Area type="monotone" dataKey="vix" stroke="#ef4444" fill="url(#vixGrad)" strokeWidth={1.5} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════
// USD INDEX — inverse crypto correlation
// ═══════════════════════════════════════════════════════════════════
export function UsdChart({ data }) {
  const chartData = useMemo(() => {
    if (!data?.DTWEXBGS?.length) return []
    return downsample(
      data.DTWEXBGS.map(o => ({ date: shortDate(o.date), usd: o.value })),
      400
    )
  }, [data])

  if (!chartData.length) return null

  return (
    <div className="card" style={{ borderImage: 'linear-gradient(90deg, #22c55e, #f59e0b) 1' }}>
      <div className="card-title">💵 USD Index · Broad Trade-Weighted</div>
      <div className="card-sub">Rising USD = crypto headwind · Falling = tailwind</div>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="rgba(42,63,102,0.5)" strokeWidth={0.5} />
          <XAxis dataKey="date" tick={{ fill: '#a3b1c6', fontSize: 10, fontFamily: "'JetBrains Mono'" }} />
          <YAxis tick={{ fill: '#a3b1c6', fontSize: 10, fontFamily: "'JetBrains Mono'" }} domain={['auto', 'auto']} />
          <Tooltip contentStyle={{ background: '#1a2744', border: '1px solid #22c55e', borderRadius: 8, fontFamily: "'JetBrains Mono'", fontSize: 12, color: '#e2e8f4', padding: '10px 14px' }}
            labelStyle={{ color: '#e2e8f4' }} itemStyle={{ color: '#e2e8f4' }} />
          <Line type="monotone" dataKey="usd" stroke="#22c55e" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════
// LIQUIDITY DASHBOARD — Fed BS + RRP + S&P overlay
// ═══════════════════════════════════════════════════════════════════
export function LiquidityChart({ data }) {
  const chartData = useMemo(() => {
    // Fed balance sheet (weekly) - show as area
    const bs = data?.WALCL || []
    if (!bs.length) return []
    return downsample(
      bs.map(o => ({
        date: shortDate(o.date),
        fed_bs: o.value / 1e6,  // trillions
      })),
      200
    )
  }, [data])

  if (!chartData.length) return null

  return (
    <div className="card" style={{ borderImage: 'linear-gradient(90deg, #06b6d4, #8b5cf6) 1' }}>
      <div className="card-title">💧 Fed Balance Sheet · QE/QT Proxy</div>
      <div className="card-sub">Expanding = risk-on = crypto bullish · Shrinking = QT headwind</div>
      <ResponsiveContainer width="100%" height={250}>
        <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
          <defs>
            <linearGradient id="bsGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#06b6d4" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#8b5cf6" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(42,63,102,0.5)" strokeWidth={0.5} />
          <XAxis dataKey="date" tick={{ fill: '#a3b1c6', fontSize: 10, fontFamily: "'JetBrains Mono'" }} />
          <YAxis tick={{ fill: '#a3b1c6', fontSize: 10, fontFamily: "'JetBrains Mono'" }}
            tickFormatter={v => `$${v.toFixed(1)}T`}
            label={{ value: 'Fed Assets ($T)', angle: -90, position: 'insideLeft', fill: '#06b6d4', fontSize: 11, fontFamily: "'JetBrains Mono'" }} />
          <Tooltip contentStyle={{ background: '#1a2744', border: '1px solid #06b6d4', borderRadius: 8, fontFamily: "'JetBrains Mono'", fontSize: 12, color: '#e2e8f4', padding: '10px 14px' }}
            labelStyle={{ color: '#e2e8f4' }} itemStyle={{ color: '#e2e8f4' }}
            formatter={v => [`$${v.toFixed(3)}T`, 'Fed Assets']} />
          <Area type="monotone" dataKey="fed_bs" stroke="#06b6d4" fill="url(#bsGrad)" strokeWidth={2} dot={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════
// S&P 500 — BTC correlation proxy (ρ = 0.72-0.87)
// ═══════════════════════════════════════════════════════════════════
export function EquityChart({ data }) {
  const chartData = useMemo(() => {
    if (!data?.SP500?.length) return []
    return downsample(
      data.SP500.map(o => ({ date: shortDate(o.date), sp500: o.value })),
      400
    )
  }, [data])

  if (!chartData.length) return null

  return (
    <div className="card" style={{ borderImage: 'linear-gradient(90deg, #3b82f6, #22c55e) 1' }}>
      <div className="card-title">📊 S&P 500 · Crypto Correlation Proxy</div>
      <div className="card-sub">BTC-S&P ρ = 0.72-0.87 (2024-25) · equities lead crypto sentiment</div>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
          <CartesianGrid stroke="rgba(42,63,102,0.5)" strokeWidth={0.5} />
          <XAxis dataKey="date" tick={{ fill: '#a3b1c6', fontSize: 10, fontFamily: "'JetBrains Mono'" }} />
          <YAxis tick={{ fill: '#a3b1c6', fontSize: 10, fontFamily: "'JetBrains Mono'" }}
            tickFormatter={v => v.toLocaleString()} />
          <Tooltip contentStyle={{ background: '#1a2744', border: '1px solid #3b82f6', borderRadius: 8, fontFamily: "'JetBrains Mono'", fontSize: 12, color: '#e2e8f4', padding: '10px 14px' }}
            labelStyle={{ color: '#e2e8f4' }} itemStyle={{ color: '#e2e8f4' }}
            formatter={v => [v.toLocaleString(undefined, {maximumFractionDigits: 0}), 'S&P 500']} />
          <Line type="monotone" dataKey="sp500" stroke="#3b82f6" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
