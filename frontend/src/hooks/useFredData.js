import { useState, useEffect, useCallback, useRef } from 'react'

const API_BASE = '/api'
const WS_URL = `ws://${window.location.hostname}:8000/ws/agents`

/**
 * Primary data hook.
 *
 * 1. On mount: fetch /api/agents/latest (cached from AgentLoop) + /api/data/core + /api/data/curve
 * 2. Connect WebSocket to /ws/agents for live push updates from the loop
 * 3. Falls back to polling /api/agents/latest every 60s if WS disconnects
 */
export function useFredData() {
  const [coreData, setCoreData] = useState(null)
  const [agentResults, setAgentResults] = useState(null)
  const [curveData, setCurveData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [fetchTime, setFetchTime] = useState(null)
  const [wsConnected, setWsConnected] = useState(false)
  const wsRef = useRef(null)
  const pollRef = useRef(null)

  // ── Initial HTTP fetch ────────────────────────────────────────────
  const fetchAll = useCallback(async (force = false) => {
    setLoading(true)
    setError(null)
    try {
      const suffix = force ? '?force=true' : ''

      // Try /agents/latest first (instant from loop cache), fall back to /agents/analyze
      let agentsResp = await fetch(`${API_BASE}/agents/latest`)
      if (agentsResp.status === 503) {
        // Loop hasn't run yet — trigger on-demand
        agentsResp = await fetch(`${API_BASE}/agents/analyze${suffix}`)
      }

      const [coreResp, curveResp, extResp] = await Promise.all([
        fetch(`${API_BASE}/data/core${suffix}`),
        fetch(`${API_BASE}/data/curve${suffix}`),
        fetch(`${API_BASE}/data/extended${suffix}`),
      ])

      if (!coreResp.ok) throw new Error(`Core data: ${coreResp.status}`)
      if (!agentsResp.ok) throw new Error(`Agents: ${agentsResp.status}`)

      const core = await coreResp.json()
      const agents = await agentsResp.json()
      const curve = curveResp.ok ? await curveResp.json() : null
      const ext = extResp.ok ? await extResp.json() : null

      // Merge extended data into core data for chart access
      if (ext?.data) {
        core.data = { ...core.data, ...ext.data }
      }

      setCoreData(core)
      setAgentResults(agents)
      setCurveData(curve)
      setFetchTime(core.fetch_time)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // ── WebSocket for live loop updates ───────────────────────────────
  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    try {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        setWsConnected(true)
        // Stop polling when WS is connected
        if (pollRef.current) {
          clearInterval(pollRef.current)
          pollRef.current = null
        }
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          setAgentResults(data)
          setFetchTime(data.timestamp || new Date().toISOString())
        } catch (e) {
          console.warn('WS parse error:', e)
        }
      }

      ws.onclose = () => {
        setWsConnected(false)
        // Start polling fallback
        startPolling()
        // Reconnect after 5s
        setTimeout(connectWs, 5000)
      }

      ws.onerror = () => {
        ws.close()
      }
    } catch (e) {
      // WS not available — rely on polling
      startPolling()
    }
  }, [])

  // ── Polling fallback ──────────────────────────────────────────────
  const startPolling = useCallback(() => {
    if (pollRef.current) return
    pollRef.current = setInterval(async () => {
      try {
        const resp = await fetch(`${API_BASE}/agents/latest`)
        if (resp.ok) {
          const data = await resp.json()
          setAgentResults(data)
          setFetchTime(data.timestamp || new Date().toISOString())
        }
      } catch (_) { /* silent */ }
    }, 60000) // Poll every 60s
  }, [])

  // ── Lifecycle ─────────────────────────────────────────────────────
  useEffect(() => {
    fetchAll()
    connectWs()

    return () => {
      if (wsRef.current) wsRef.current.close()
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [fetchAll, connectWs])

  const refresh = useCallback(() => {
    // Trigger immediate server-side run via POST
    fetch(`${API_BASE}/agents/run-now`, { method: 'POST' })
      .then(r => r.json())
      .then(data => {
        setAgentResults(data)
        setFetchTime(data.timestamp || new Date().toISOString())
      })
      .catch(() => fetchAll(true))
  }, [fetchAll])

  return {
    coreData, agentResults, curveData,
    loading, error, fetchTime, wsConnected,
    refresh,
  }
}


// ─── Helper utilities ───────────────────────────────────────────────

export function alignSeries(data, ...ids) {
  if (!data) return null
  const series = ids.map(id => data[id] || [])
  if (series.some(s => !s.length)) return null

  const dateSets = series.map(s => new Set(s.map(o => o.date)))
  const common = [...dateSets[0]].filter(d => dateSets.every(ds => ds.has(d))).sort()

  const result = { dates: common }
  ids.forEach((id, i) => {
    const lookup = new Map(series[i].map(o => [o.date, o.value]))
    result[id] = common.map(d => lookup.get(d))
  })
  return result
}

export function lastVal(data, id, offset = 0) {
  const series = data?.[id]
  if (!series?.length || series.length <= offset) return null
  return series[series.length - 1 - offset].value
}

export function lastDate(data, id) {
  const series = data?.[id]
  if (!series?.length) return null
  return series[series.length - 1].date
}
