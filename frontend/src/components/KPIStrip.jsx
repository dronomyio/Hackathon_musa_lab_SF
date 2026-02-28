import React from 'react'
import { lastVal } from '../hooks/useFredData'

export default function KPIStrip({ data }) {
  const items = [
    { label: '2-Year Yield', id: 'DGS2', color: 'var(--c2y)', suffix: '%', bps: true },
    { label: '10-Year Yield', id: 'DGS10', color: 'var(--c10y)', suffix: '%', bps: true },
    { label: '30-Year Yield', id: 'DGS30', color: 'var(--c30y)', suffix: '%', bps: true },
    { label: '10Y − 2Y Spread', id: 'T10Y2Y', color: 'var(--cspr)', suffix: '%', bps: true },
    { label: 'VIX', id: 'VIXCLS', color: '#ef4444', suffix: '', bps: false },
    { label: 'USD Index', id: 'DTWEXBGS', color: '#22c55e', suffix: '', bps: false },
    { label: 'S&P 500', id: 'SP500', color: '#3b82f6', suffix: '', bps: false, big: true },
  ]

  return (
    <div className="kpi-row">
      {items.map((k, i) => {
        const v = k.id ? lastVal(data, k.id) : null
        const prev = k.id ? lastVal(data, k.id, 1) : null
        const d = v !== null && prev !== null ? v - prev : 0
        const cls = d > 0.005 ? 'up' : d < -0.005 ? 'down' : 'flat'
        const arrow = d > 0.005 ? '▲' : d < -0.005 ? '▼' : '—'

        let displayVal = 'N/A'
        let displayDelta = ''
        if (v !== null) {
          if (k.big) {
            displayVal = Math.round(v).toLocaleString() + k.suffix
          } else if (k.suffix === '%') {
            displayVal = v.toFixed(2) + '%'
          } else {
            displayVal = v.toFixed(2) + k.suffix
          }
        }
        if (k.bps) {
          displayDelta = `${arrow} ${d >= 0 ? '+' : ''}${(d * 100).toFixed(1)} bps`
        } else if (k.big) {
          displayDelta = `${arrow} ${d >= 0 ? '+' : ''}${d.toFixed(0)} pts`
        } else {
          displayDelta = `${arrow} ${d >= 0 ? '+' : ''}${d.toFixed(2)}`
        }

        return (
          <div className="kpi" key={i}>
            <div className="kpi-label">{k.label}</div>
            <div className="kpi-value" style={{ color: k.color }}>
              {displayVal}
            </div>
            <div className={`kpi-delta ${cls}`}>
              {displayDelta}
            </div>
          </div>
        )
      })}
    </div>
  )
}
