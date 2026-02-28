import React from 'react'
import {
  ResponsiveContainer, LineChart, AreaChart, Line, Area, XAxis, YAxis,
  Tooltip, CartesianGrid, ReferenceLine, Legend,
} from 'recharts'

const CHART_COLORS = [
  '#60a5fa', '#f59e0b', '#22c55e', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#14b8a6',
]

const tooltipStyle = {
  contentStyle: { background: '#1a2744', border: '1px solid #334155', borderRadius: 8, fontSize: 12 },
  labelStyle: { color: '#94a3b8' },
  itemStyle: { color: '#e2e8f4' },
}

/**
 * Renders a single chart from a ChartDef config + data.
 */
export function VerticalChart({ chartDef, data, themeColor }) {
  const { chart_id, title, series, chart_type, color, reference_lines } = chartDef

  // Merge all series into a single dataset keyed by date
  const mergedData = mergeSeriesData(series, data)
  if (!mergedData.length) {
    return (
      <div className="chart-card" style={{ borderColor: `${themeColor}20` }}>
        <h3 className="chart-title">{title}</h3>
        <div style={{ color: '#475569', fontSize: 13, padding: 20 }}>No data available</div>
      </div>
    )
  }

  // Downsample if too many points
  const chartData = downsample(mergedData, 200)

  const ChartComponent = chart_type === 'area' ? AreaChart : LineChart

  return (
    <div className="chart-card" style={{ borderColor: `${themeColor}20` }}>
      <h3 className="chart-title">{title}</h3>
      <ResponsiveContainer width="100%" height={220}>
        <ChartComponent data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#475569', fontSize: 10 }}
            tickFormatter={(d) => d?.slice(5) || ''}
            minTickGap={40}
          />
          <YAxis tick={{ fill: '#475569', fontSize: 10 }} width={50} />
          <Tooltip {...tooltipStyle} />

          {/* Reference lines */}
          {reference_lines && Object.entries(reference_lines).map(([val, label]) => (
            <ReferenceLine
              key={val}
              y={parseFloat(val)}
              stroke="#475569"
              strokeDasharray="4 4"
              label={{ value: label, fill: '#64748b', fontSize: 10, position: 'right' }}
            />
          ))}

          {/* Data lines/areas */}
          {series.map((sid, idx) => {
            const lineColor = idx === 0 ? (color || themeColor) : CHART_COLORS[idx % CHART_COLORS.length]
            if (chart_type === 'area' && idx === 0) {
              return (
                <Area
                  key={sid}
                  type="monotone"
                  dataKey={sid}
                  stroke={lineColor}
                  fill={`${lineColor}20`}
                  strokeWidth={2}
                  dot={false}
                  name={sid}
                />
              )
            }
            return (
              <Line
                key={sid}
                type="monotone"
                dataKey={sid}
                stroke={lineColor}
                strokeWidth={2}
                dot={false}
                name={sid}
              />
            )
          })}

          {series.length > 1 && <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />}
        </ChartComponent>
      </ResponsiveContainer>
    </div>
  )
}

/**
 * KPI Strip component — renders KPIs from vertical config.
 */
export function VerticalKPIStrip({ kpis, data, themeColor }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: `repeat(${Math.min(kpis.length, 6)}, 1fr)`,
      gap: 12,
      marginBottom: 20,
    }}>
      {kpis.map((kpi) => {
        const val = getLatestValue(data, kpi.series_id)
        const formatted = formatKPI(val, kpi.format, kpi.suffix)

        return (
          <div
            key={kpi.series_id}
            style={{
              background: '#111827',
              borderRadius: 10,
              padding: '12px 16px',
              borderLeft: `3px solid ${kpi.color || themeColor}`,
            }}
          >
            <div style={{ color: '#64748b', fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5 }}>
              {kpi.label}
            </div>
            <div style={{ color: kpi.color || themeColor, fontSize: 24, fontWeight: 700, fontFamily: 'monospace' }}>
              {formatted}
            </div>
          </div>
        )
      })}
    </div>
  )
}


/**
 * Analysis Panel — shows synthesis results or metrics.
 */
export function VerticalAnalysisPanel({ analysis, config }) {
  if (!analysis) return null

  const synthesis = analysis.synthesis
  const metrics = analysis.metrics

  // If we have full synthesis (defi_crypto), show it rich
  if (synthesis) {
    return (
      <div style={{
        background: '#0a0f1a', borderRadius: 12, padding: 20, marginBottom: 20,
        border: `1px solid ${config.color}30`,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h3 style={{ color: '#e2e8f4', margin: 0, fontSize: 18 }}>
            {config.icon} AI Synthesis
          </h3>
          {synthesis.market_regime && (
            <span style={{
              background: `${config.color}20`, color: config.color,
              padding: '4px 14px', borderRadius: 20, fontSize: 12, fontWeight: 700,
              border: `1px solid ${config.color}40`,
            }}>
              {synthesis.regime_label || synthesis.market_regime}
            </span>
          )}
        </div>
        {synthesis.headline && (
          <p style={{ color: '#e2e8f4', fontSize: 15, fontWeight: 600, margin: '0 0 12px' }}>
            {synthesis.headline}
          </p>
        )}
        {synthesis.narrative && (
          <p style={{ color: '#94a3b8', fontSize: 13, lineHeight: 1.7, margin: '0 0 12px', whiteSpace: 'pre-wrap' }}>
            {synthesis.narrative}
          </p>
        )}
        {synthesis.key_risks?.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <span style={{ color: '#ef4444', fontSize: 12, fontWeight: 600 }}>KEY RISKS: </span>
            <span style={{ color: '#f87171', fontSize: 12 }}>{synthesis.key_risks.join(' • ')}</span>
          </div>
        )}
      </div>
    )
  }

  // For non-DeFi verticals, show metrics summary
  if (metrics && Object.keys(metrics).length > 0) {
    return (
      <div style={{
        background: '#0a0f1a', borderRadius: 12, padding: 20, marginBottom: 20,
        border: `1px solid ${config.color}30`,
      }}>
        <h3 style={{ color: '#e2e8f4', margin: '0 0 12px', fontSize: 18 }}>
          {config.icon} Key Metrics
        </h3>
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
          gap: 10,
        }}>
          {Object.entries(metrics).slice(0, 12).map(([sid, m]) => (
            <div key={sid} style={{
              background: '#111827', borderRadius: 8, padding: '10px 14px',
              borderLeft: `3px solid ${config.color}`,
            }}>
              <div style={{ color: '#64748b', fontSize: 10, textTransform: 'uppercase' }}>
                {m.series_name || sid}
              </div>
              <div style={{ color: '#e2e8f4', fontSize: 18, fontWeight: 700, fontFamily: 'monospace' }}>
                {typeof m.value === 'number' ? m.value.toLocaleString('en-US', { maximumFractionDigits: 2 }) : m.value}
                <span style={{ fontSize: 11, color: '#64748b', marginLeft: 4 }}>{m.units}</span>
              </div>
              {m.change_pct != null && (
                <div style={{
                  fontSize: 11, fontWeight: 600,
                  color: m.change_pct >= 0 ? '#4ade80' : '#f87171',
                }}>
                  {m.change_pct >= 0 ? '▲' : '▼'} {Math.abs(m.change_pct).toFixed(2)}%
                </div>
              )}
            </div>
          ))}
        </div>
        <p style={{ color: '#475569', fontSize: 11, marginTop: 12 }}>
          {analysis.prompt_status === 'none'
            ? '💡 Add an ANTHROPIC_API_KEY to enable AI synthesis for this vertical.'
            : `Prompt status: ${analysis.prompt_status}`}
        </p>
      </div>
    )
  }

  return null
}


// ═══════ Utilities ═══════

function mergeSeriesData(seriesIds, rawData) {
  if (!rawData?.data) return []

  const dateMap = {}

  for (const sid of seriesIds) {
    const obs = rawData.data[sid]
    if (!Array.isArray(obs)) continue

    for (const point of obs) {
      const date = point.date
      const val = parseFloat(point.value)
      if (!date || isNaN(val)) continue

      if (!dateMap[date]) dateMap[date] = { date }
      dateMap[date][sid] = val
    }
  }

  return Object.values(dateMap).sort((a, b) => a.date.localeCompare(b.date))
}

function downsample(data, maxPoints) {
  if (data.length <= maxPoints) return data
  const step = Math.ceil(data.length / maxPoints)
  const result = []
  for (let i = 0; i < data.length; i += step) {
    result.push(data[i])
  }
  // Always include last point
  if (result[result.length - 1] !== data[data.length - 1]) {
    result.push(data[data.length - 1])
  }
  return result
}

function getLatestValue(rawData, seriesId) {
  const obs = rawData?.data?.[seriesId]
  if (!Array.isArray(obs) || obs.length === 0) return null
  const last = obs[obs.length - 1]
  return last?.value != null ? parseFloat(last.value) : null
}

function formatKPI(value, format = '.2f', suffix = '%') {
  if (value == null || isNaN(value)) return '—'
  if (format.includes(',')) {
    const decimals = parseInt(format.match(/(\d+)f/)?.[1] || '0')
    return value.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }) + suffix
  }
  const decimals = parseInt(format.match(/(\d+)f/)?.[1] || '2')
  return value.toFixed(decimals) + suffix
}
