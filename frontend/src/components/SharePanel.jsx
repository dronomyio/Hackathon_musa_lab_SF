import React, { useState, useEffect } from 'react'

/**
 * SharePanel — Generates a shareable public link for the dashboard.
 * 
 * When a user deploys via the meta-agent, this component shows:
 * 1. The public Morph Cloud URL (already accessible)
 * 2. A QR code for mobile sharing
 * 3. Embed snippet for iframes
 * 4. API access instructions
 */
export default function SharePanel({ dashboardUrl, apiUrl, wsUrl, snapshotId }) {
  const [copied, setCopied] = useState(null)

  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text)
    setCopied(label)
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div style={{
      margin: '24px 0', padding: '24px',
      background: 'linear-gradient(135deg, rgba(6,182,212,0.06), rgba(139,92,246,0.06))',
      borderRadius: 12, border: '1px solid rgba(6,182,212,0.2)',
    }}>
      <h2 style={{
        fontSize: 16, fontWeight: 700, marginBottom: 16,
        fontFamily: "'JetBrains Mono', monospace",
        background: 'linear-gradient(90deg, #06b6d4, #8b5cf6)',
        WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
      }}>
        🌐 Share This Dashboard
      </h2>

      {/* Public URL */}
      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 11, color: '#a3b1c6', textTransform: 'uppercase', letterSpacing: 1, fontFamily: "'JetBrains Mono', monospace" }}>
          📊 Live Dashboard (anyone with link can view)
        </label>
        <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
          <input
            readOnly value={dashboardUrl || 'Deploying...'}
            style={{
              flex: 1, padding: '10px 14px', borderRadius: 8,
              background: '#0d1525', border: '1px solid #1e2d4a',
              color: '#e2e8f4', fontFamily: "'JetBrains Mono', monospace", fontSize: 13,
            }}
          />
          <button
            onClick={() => copyToClipboard(dashboardUrl, 'dashboard')}
            style={{
              padding: '10px 16px', borderRadius: 8, border: 'none', cursor: 'pointer',
              background: copied === 'dashboard' ? '#22c55e' : '#3b82f6',
              color: '#fff', fontWeight: 600, fontSize: 12,
            }}
          >
            {copied === 'dashboard' ? '✓ Copied' : 'Copy'}
          </button>
        </div>
      </div>

      {/* API endpoint */}
      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 11, color: '#a3b1c6', textTransform: 'uppercase', letterSpacing: 1, fontFamily: "'JetBrains Mono', monospace" }}>
          🔌 API Endpoint (JSON)
        </label>
        <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
          <input
            readOnly value={apiUrl ? `${apiUrl}/api/agents/latest` : 'Deploying...'}
            style={{
              flex: 1, padding: '10px 14px', borderRadius: 8,
              background: '#0d1525', border: '1px solid #1e2d4a',
              color: '#e2e8f4', fontFamily: "'JetBrains Mono', monospace", fontSize: 13,
            }}
          />
          <button
            onClick={() => copyToClipboard(`${apiUrl}/api/agents/latest`, 'api')}
            style={{
              padding: '10px 16px', borderRadius: 8, border: 'none', cursor: 'pointer',
              background: copied === 'api' ? '#22c55e' : '#3b82f6',
              color: '#fff', fontWeight: 600, fontSize: 12,
            }}
          >
            {copied === 'api' ? '✓ Copied' : 'Copy'}
          </button>
        </div>
      </div>

      {/* WebSocket */}
      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 11, color: '#a3b1c6', textTransform: 'uppercase', letterSpacing: 1, fontFamily: "'JetBrains Mono', monospace" }}>
          📡 WebSocket (live updates)
        </label>
        <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
          <input
            readOnly value={wsUrl || 'Deploying...'}
            style={{
              flex: 1, padding: '10px 14px', borderRadius: 8,
              background: '#0d1525', border: '1px solid #1e2d4a',
              color: '#e2e8f4', fontFamily: "'JetBrains Mono', monospace", fontSize: 13,
            }}
          />
          <button
            onClick={() => copyToClipboard(wsUrl, 'ws')}
            style={{
              padding: '10px 16px', borderRadius: 8, border: 'none', cursor: 'pointer',
              background: copied === 'ws' ? '#22c55e' : '#3b82f6',
              color: '#fff', fontWeight: 600, fontSize: 12,
            }}
          >
            {copied === 'ws' ? '✓ Copied' : 'Copy'}
          </button>
        </div>
      </div>

      {/* Embed snippet */}
      <div style={{ marginBottom: 16 }}>
        <label style={{ fontSize: 11, color: '#a3b1c6', textTransform: 'uppercase', letterSpacing: 1, fontFamily: "'JetBrains Mono', monospace" }}>
          📋 Embed in your website
        </label>
        <pre style={{
          marginTop: 4, padding: '12px 16px', borderRadius: 8,
          background: '#0d1525', border: '1px solid #1e2d4a',
          color: '#a3b1c6', fontFamily: "'JetBrains Mono', monospace", fontSize: 11,
          overflow: 'auto', whiteSpace: 'pre-wrap',
        }}>
{`<iframe
  src="${dashboardUrl || 'https://your-morph-url'}"
  width="100%" height="800"
  style="border: none; border-radius: 12px;"
  title="Treasury Bond Intelligence"
></iframe>`}
        </pre>
      </div>

      {/* Access info */}
      <div style={{
        padding: '12px 16px', borderRadius: 8,
        background: 'rgba(34,197,94,0.06)', border: '1px solid rgba(34,197,94,0.15)',
      }}>
        <p style={{ fontSize: 12, color: '#a3b1c6', lineHeight: 1.6, margin: 0, fontFamily: "'JetBrains Mono', monospace" }}>
          <strong style={{ color: '#22c55e' }}>✅ No login required.</strong> Anyone with the URL sees live data, AI analysis, and charts.
          Dashboard auto-updates via WebSocket every 15 minutes. Backed by Morph Cloud snapshot
          <span style={{ color: '#8b5cf6' }}> {snapshotId}</span> — restore in &lt;250ms if needed.
        </p>
      </div>
    </div>
  )
}
