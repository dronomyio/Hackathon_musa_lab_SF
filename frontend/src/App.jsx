import React, { useState, useEffect } from 'react'
import { useFredData, lastVal, lastDate } from './hooks/useFredData'
import { useVerticalData, useVerticals } from './hooks/useVerticalData'
import KPIStrip from './components/KPIStrip'
import YieldChart from './components/YieldChart'
import SpreadChart from './components/SpreadChart'
import CurveSnapshot from './components/CurveSnapshot'
import TailChart from './components/TailChart'
import CrossCorrelation from './components/CrossCorrelation'
import ScatterPlot from './components/ScatterPlot'
import InferencePanel from './components/InferencePanel'
import PromptReviewPanel from './components/PromptReviewPanel'
import { VixChart, UsdChart, LiquidityChart, EquityChart } from './components/MacroCharts'
import { VerticalChart, VerticalKPIStrip, VerticalAnalysisPanel } from './components/VerticalDashboard'

export default function App() {
  const [activeTab, setActiveTab] = useState('defi_crypto')
  const { verticals, loading: vertsLoading } = useVerticals()

  return (
    <div className="dashboard">
      {/* Platform Header */}
      <div className="header">
        <div>
          <h1>Macro Intelligence Platform</h1>
          <div className="header-sub">
            FRED API · 8 Verticals · 120+ Series · Opus 4.6 Synthesis · Human-Curated Prompts
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            background: '#14532d', color: '#4ade80', padding: '4px 12px',
            borderRadius: 20, fontSize: 11, fontWeight: 700, border: '1px solid #22c55e40',
          }}>
            PLATFORM v3.0
          </div>
        </div>
      </div>

      {/* Vertical Tabs */}
      <div style={{
        display: 'flex', gap: 4, padding: '4px 0 16px', overflowX: 'auto',
        borderBottom: '1px solid #1e293b', marginBottom: 20,
      }}>
        {verticals.map((v) => {
          const isActive = activeTab === v.id
          return (
            <button
              key={v.id}
              onClick={() => setActiveTab(v.id)}
              style={{
                background: isActive ? `${v.color}15` : 'transparent',
                color: isActive ? v.color : '#64748b',
                border: isActive ? `1px solid ${v.color}40` : '1px solid transparent',
                borderRadius: 8,
                padding: '8px 16px',
                fontSize: 13,
                fontWeight: isActive ? 700 : 500,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <span style={{ fontSize: 16 }}>{v.icon}</span>
              <span>{v.name}</span>
              {v.is_primary && (
                <span style={{
                  background: `${v.color}30`, color: v.color,
                  padding: '1px 6px', borderRadius: 4, fontSize: 9, fontWeight: 800,
                }}>PRIMARY</span>
              )}
            </button>
          )
        })}
      </div>

      {/* Active Vertical Content */}
      <div className="tab-content" key={activeTab}>
        {activeTab === 'defi_crypto' ? (
          <DeFiDashboard />
        ) : (
          <GenericVerticalDashboard verticalId={activeTab} />
        )}
      </div>
    </div>
  )
}


/**
 * DeFi/Crypto Dashboard — the full 8-agent system (existing).
 */
function DeFiDashboard() {
  const { coreData, agentResults, curveData, loading, error, fetchTime, wsConnected, refresh } = useFredData()

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <div className="loading-text">Fetching live FRED data & running 8 agents…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-screen">
        <h2>Connection Error</h2>
        <p>{error}</p>
        <button className="refresh-btn" onClick={refresh}>Retry</button>
      </div>
    )
  }

  const data = coreData?.data || {}
  const latestDate = lastDate(data, 'DGS10')

  return (
    <>
      <KPIStrip data={data} />
      <InferencePanel agentResults={agentResults} />
      <PromptReviewPanel />

      <SectionHeader
        color="#06b6d4" icon="⚡" title="Macro → Crypto Indicators"
        sub="Liquidity · Dollar · Volatility · Equity Correlation"
      />
      <div className="grid-2">
        <VixChart data={data} />
        <UsdChart data={data} />
      </div>
      <div className="grid-2">
        <LiquidityChart data={data} />
        <EquityChart data={data} />
      </div>

      <SectionHeader
        color="#3b82f6" icon="📈" title="Bond Market Dynamics"
        sub="Yield Curve · Spreads · Duration · Correlation"
      />
      <div className="grid-1"><YieldChart data={data} /></div>
      <div className="grid-2">
        <SpreadChart data={data} />
        <CurveSnapshot curveData={curveData} />
      </div>
      <div className="grid-2">
        <TailChart data={data} />
        <CrossCorrelation data={data} agentResult={agentResults?.signals?.cross_correlation} />
      </div>
      <div className="grid-1"><ScatterPlot data={data} /></div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 16 }}>
        <button className="refresh-btn" onClick={refresh}>↻ Refresh Data</button>
        <span className="live-tag" style={{ fontSize: 11 }}>
          <span className="live-dot" style={{ background: wsConnected ? 'var(--cpos)' : 'var(--cspr)' }} />
          {wsConnected ? 'LIVE WS' : 'POLLING'} · {latestDate || '…'}
        </span>
      </div>
    </>
  )
}


/**
 * Generic Vertical Dashboard — renders any non-DeFi vertical using config from API.
 */
function GenericVerticalDashboard({ verticalId }) {
  const { config, data, analysis, loading, error, refresh } = useVerticalData(verticalId)

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <div className="loading-text">Loading {verticalId} data…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-screen">
        <h2>Error loading vertical</h2>
        <p>{error}</p>
        <button className="refresh-btn" onClick={refresh}>Retry</button>
      </div>
    )
  }

  if (!config) return null

  const themeColor = config.color || '#60a5fa'

  return (
    <>
      {/* Vertical header */}
      <div style={{
        background: `linear-gradient(135deg, ${themeColor}08, ${themeColor}03)`,
        borderRadius: 12, padding: '16px 20px', marginBottom: 20,
        border: `1px solid ${themeColor}20`,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ color: '#e2e8f4', margin: 0, fontSize: 22 }}>
              {config.icon} {config.name}
            </h2>
            <p style={{ color: '#94a3b8', margin: '4px 0 0', fontSize: 13 }}>
              {config.description}
            </p>
          </div>
          <div style={{
            background: `${themeColor}15`, color: themeColor,
            padding: '4px 14px', borderRadius: 20, fontSize: 11, fontWeight: 700,
            border: `1px solid ${themeColor}30`,
          }}>
            {config.series_count} SERIES · {config.charts?.length || 0} CHARTS
          </div>
        </div>
        {config.customers?.length > 0 && (
          <div style={{ marginTop: 8 }}>
            <span style={{ color: '#475569', fontSize: 11 }}>TARGET: </span>
            <span style={{ color: '#64748b', fontSize: 11 }}>{config.customers.join(' · ')}</span>
          </div>
        )}
      </div>

      {/* KPIs */}
      {config.kpis?.length > 0 && (
        <VerticalKPIStrip kpis={config.kpis} data={data} themeColor={themeColor} />
      )}

      {/* AI Analysis */}
      <VerticalAnalysisPanel analysis={analysis} config={config} />

      {/* Charts */}
      <SectionHeader
        color={themeColor} icon={config.icon} title={`${config.name} Charts`}
        sub={config.tagline}
      />
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(480px, 1fr))',
        gap: 16,
      }}>
        {config.charts?.map((chartDef) => (
          <VerticalChart
            key={chartDef.chart_id}
            chartDef={chartDef}
            data={data}
            themeColor={themeColor}
          />
        ))}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 20 }}>
        <button className="refresh-btn" onClick={refresh}>↻ Refresh Data</button>
        <span style={{ color: '#475569', fontSize: 11 }}>
          Auto-refresh every 5 minutes
        </span>
      </div>
    </>
  )
}


/**
 * Reusable section header.
 */
function SectionHeader({ color, icon, title, sub }) {
  return (
    <div style={{
      marginTop: 24, marginBottom: 12, padding: '8px 16px',
      background: `linear-gradient(90deg, ${color}08, ${color}04)`,
      borderRadius: 8, border: `1px solid ${color}15`,
    }}>
      <span className="mono" style={{ fontSize: 12, fontWeight: 600, color, letterSpacing: 1, textTransform: 'uppercase' }}>
        {icon} {title}
      </span>
      {sub && (
        <span className="mono" style={{ fontSize: 10, color: '#475569', marginLeft: 12 }}>
          {sub}
        </span>
      )}
    </div>
  )
}
