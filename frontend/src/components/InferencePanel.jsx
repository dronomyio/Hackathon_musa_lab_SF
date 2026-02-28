import React from 'react'

export default function InferencePanel({ agentResults }) {
  if (!agentResults) return null

  const signals = agentResults.signals || {}
  const synthesis = agentResults.synthesis || {}
  const engine = agentResults.synthesis_engine
  const transmission = synthesis.macro_crypto_transmission || {}

  const agents = [
    { key: 'yield_curve', title: 'Yield Curve', icon: '📈' },
    { key: 'credit_risk', title: 'Credit Risk', icon: '🏦' },
    { key: 'inflation', title: 'Inflation', icon: '🔥' },
    { key: 'liquidity', title: 'Liquidity', icon: '💧' },
    { key: 'dollar_vol', title: 'Dollar & VIX', icon: '💵' },
    { key: 'employment_stress', title: 'Jobs & Stress', icon: '📋' },
    { key: 'tail_risk', title: 'Tail Risk', icon: '📊' },
    { key: 'cross_correlation', title: '2Y↔10Y Corr', icon: '🔗' },
  ]

  const isClaude = engine === 'claude-opus-4.6'

  return (
    <div className="inference-panel">
      {/* Header */}
      <div className="inference-header">
        <div className="inference-icon">{isClaude ? '✨' : '🧠'}</div>
        <h2 className="mono" style={{ fontSize: 15, fontWeight: 600 }}>
          {isClaude ? 'Opus 4.6' : 'Rule-Based'} · {agentResults.agent_count || 8} Agents · {synthesis.regime_label || 'Analyzing…'}
        </h2>
        {synthesis.dominant_signal && (
          <span className={`badge ${synthesis.dominant_signal}`} style={{ marginLeft: 12 }}>
            {synthesis.dominant_signal.toUpperCase()}
          </span>
        )}
        {synthesis.confidence != null && (
          <span className="badge neutral" style={{ marginLeft: 6 }}>
            {(synthesis.confidence * 100).toFixed(0)}%
          </span>
        )}
        <span className="mono" style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--t3)' }}>
          {engine}
        </span>
      </div>

      {/* Headline */}
      {synthesis.headline && (
        <h3 className="mono" style={{
          fontSize: 15, fontWeight: 600, color: 'var(--t1)', margin: '12px 0 6px',
          background: 'linear-gradient(135deg, var(--c2y), var(--c10y))',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>
          {synthesis.headline}
        </h3>
      )}

      {/* Main narrative */}
      {synthesis.narrative && (
        <div style={{
          marginBottom: 18, padding: '16px 20px',
          background: isClaude
            ? 'linear-gradient(135deg, rgba(6,182,212,0.04), rgba(139,92,246,0.04))'
            : 'rgba(255,255,255,0.02)',
          borderRadius: 10,
          border: isClaude ? '1px solid rgba(6,182,212,0.15)' : '1px solid rgba(255,255,255,0.04)',
        }}>
          <p style={{ color: 'var(--t2)', fontSize: 13, lineHeight: 1.75, whiteSpace: 'pre-wrap' }}>
            {synthesis.narrative}
          </p>
        </div>
      )}

      {/* Macro → Crypto Transmission Channel */}
      {transmission.primary_channel && (
        <div style={{
          marginBottom: 16, padding: '12px 16px',
          background: 'linear-gradient(135deg, rgba(34,211,238,0.06), rgba(59,130,246,0.06))',
          borderRadius: 10, border: '1px solid rgba(34,211,238,0.2)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <span style={{ fontSize: 13 }}>⚡</span>
            <span className="mono" style={{ fontSize: 11, color: 'var(--ccyan)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
              Macro → Crypto Transmission
            </span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 8 }}>
            <span className="badge bullish">Channel: {transmission.primary_channel}</span>
            <span className="badge neutral">Lag: ~{transmission.transmission_lag_days}d</span>
            <span className={`badge ${transmission.signal_strength === 'strong' ? 'bearish' : 'caution'}`}>
              Strength: {transmission.signal_strength}
            </span>
          </div>
          {transmission.description && (
            <p style={{ fontSize: 12, color: 'var(--t2)', lineHeight: 1.5 }}>{transmission.description}</p>
          )}
        </div>
      )}

      {/* Key Risks + Triggers + DeFi row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12, marginBottom: 18 }}>
        {synthesis.key_risks?.length > 0 && (
          <div style={{ padding: '12px 16px', background: 'rgba(239,68,68,0.04)', borderRadius: 8, border: '1px solid rgba(239,68,68,0.12)' }}>
            <span className="mono" style={{ fontSize: 10, color: 'var(--cneg)', textTransform: 'uppercase', letterSpacing: 1 }}>Key Risks</span>
            <ul style={{ margin: '6px 0 0 16px', color: 'var(--t2)', fontSize: 12, lineHeight: 1.6 }}>
              {synthesis.key_risks.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>
        )}
        {synthesis.regime_triggers?.length > 0 && (
          <div style={{ padding: '12px 16px', background: 'rgba(245,158,11,0.04)', borderRadius: 8, border: '1px solid rgba(245,158,11,0.12)' }}>
            <span className="mono" style={{ fontSize: 10, color: 'var(--cspr)', textTransform: 'uppercase', letterSpacing: 1 }}>Regime Triggers</span>
            <ul style={{ margin: '6px 0 0 16px', color: 'var(--t2)', fontSize: 12, lineHeight: 1.6 }}>
              {synthesis.regime_triggers.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>
        )}

        {/* Enhanced DeFi Panel */}
        {synthesis.defi_implications && (
          <div style={{ padding: '12px 16px', background: 'rgba(139,92,246,0.04)', borderRadius: 8, border: '1px solid rgba(139,92,246,0.12)' }}>
            <span className="mono" style={{ fontSize: 10, color: 'var(--cvio)', textTransform: 'uppercase', letterSpacing: 1 }}>DeFi / MEV / Crypto</span>
            <div style={{ marginTop: 6, display: 'flex', flexWrap: 'wrap', gap: 5 }}>
              {[
                ['Risk', synthesis.defi_implications.risk_appetite],
                ['MEV', synthesis.defi_implications.mev_activity],
                ['Liq Risk', synthesis.defi_implications.liquidation_risk],
                ['BTC', synthesis.defi_implications.btc_bias],
                ['Alts', synthesis.defi_implications.altseason_probability],
                ['Yield', synthesis.defi_implications.defi_yield_vs_tbill],
              ].filter(([, v]) => v).map(([label, val]) => {
                const cls = val === 'high' || val === 'bullish' || val === 'defi_attractive' || val === 'elevated'
                  ? 'bullish'
                  : val === 'low' || val === 'bearish' || val === 'tbill_attractive' || val === 'suppressed'
                  ? 'bearish' : 'caution'
                return <span key={label} className={`badge ${cls}`} style={{ fontSize: 10 }}>{label}: {val}</span>
              })}
            </div>
            {synthesis.defi_implications.narrative && (
              <p style={{ marginTop: 8, fontSize: 12, color: 'var(--t2)', lineHeight: 1.5 }}>
                {synthesis.defi_implications.narrative}
              </p>
            )}
          </div>
        )}
      </div>

      {/* 8 Agent Cards */}
      <div className="inference-grid">
        {agents.map(({ key, title, icon }) => {
          const s = signals[key]
          if (!s) return null
          return (
            <div className="inference-item" key={key}>
              <h3>{icon} {title}</h3>
              <p>
                <span className={`badge ${s.signal}`}>{s.regime?.replace(/_/g, ' ')}</span>
                <span className="badge neutral" style={{ marginLeft: 6 }}>{(s.confidence * 100).toFixed(0)}%</span>
                <br /><br />
                {s.summary}
                {s.metrics && Object.keys(s.metrics).length > 0 && (
                  <span style={{ display: 'block', marginTop: 8, fontSize: 11, color: 'var(--t3)', fontFamily: "'JetBrains Mono', monospace" }}>
                    {Object.entries(s.metrics).filter(([, v]) => v !== null && typeof v === 'number').slice(0, 5)
                      .map(([k, v]) => `${k.replace(/_/g, ' ')}: ${typeof v === 'number' && Math.abs(v) < 100 ? v.toFixed(2) : Math.round(v).toLocaleString()}`).join(' · ')}
                  </span>
                )}
              </p>
            </div>
          )
        })}
      </div>

      {/* Conflicts */}
      {synthesis.conflicts?.length > 0 && (
        <div style={{ marginTop: 16, padding: '10px 14px', background: 'rgba(245,158,11,0.05)', borderRadius: 8, border: '1px solid rgba(245,158,11,0.15)' }}>
          <span className="mono" style={{ fontSize: 11, color: 'var(--cspr)' }}>
            ⚠ Conflicts: {synthesis.conflicts.join(' | ')}
          </span>
        </div>
      )}
    </div>
  )
}
