import React, { useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { alignSeries } from '../hooks/useFredData'
import { shortDate } from '../utils/chartHelpers'

export default function YieldChart({ data }) {
  const chartData = useMemo(() => {
    const aligned = alignSeries(data, 'DGS2', 'DGS10', 'DGS30')
    if (!aligned) return []
    return aligned.dates.map((d, i) => ({
      date: d, y2: aligned.DGS2[i], y10: aligned.DGS10[i], y30: aligned.DGS30[i],
    }))
  }, [data])

  if (!chartData.length) return null

  return (
    <div className="card">
      <div className="card-title">2Y / 10Y / 30Y Treasury Yields</div>
      <div className="card-sub">Daily constant maturity · Past 2 years through latest</div>
      <div className="legend-row">
        <div className="legend-item"><div className="legend-dot" style={{ background: 'var(--c2y)' }} />2-Year (DGS2)</div>
        <div className="legend-item"><div className="legend-dot" style={{ background: 'var(--c10y)' }} />10-Year (DGS10)</div>
        <div className="legend-item"><div className="legend-dot" style={{ background: 'var(--c30y)' }} />30-Year (DGS30)</div>
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid stroke="rgba(42,63,102,0.5)" strokeWidth={0.5} />
          <XAxis dataKey="date" tickFormatter={shortDate} tick={{ fill: '#a3b1c6', fontSize: 10, fontFamily: "'JetBrains Mono'" }} interval={Math.floor(chartData.length / 12)} />
          <YAxis tickFormatter={v => `${v.toFixed(1)}%`} tick={{ fill: '#a3b1c6', fontSize: 10, fontFamily: "'JetBrains Mono'" }} domain={['auto', 'auto']} />
          <Tooltip contentStyle={{ background: '#1a2744', border: '1px solid #3b82f6', borderRadius: 8, fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: '#e2e8f4', padding: '10px 14px', boxShadow: '0 4px 20px rgba(0,0,0,0.5)' }} labelStyle={{ color: '#e2e8f4' }} itemStyle={{ color: '#e2e8f4' }}
            formatter={(v, name) => [`${v.toFixed(2)}%`, name === 'y2' ? '2Y' : name === 'y10' ? '10Y' : '30Y']}
            labelFormatter={shortDate} />
          <Line type="monotone" dataKey="y2" stroke="#22d3ee" strokeWidth={2} dot={false} />
          <Line type="monotone" dataKey="y10" stroke="#3b82f6" strokeWidth={2.5} dot={false} />
          <Line type="monotone" dataKey="y30" stroke="#a78bfa" strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
