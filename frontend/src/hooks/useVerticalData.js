import { useState, useEffect, useCallback, useRef } from 'react'

const API_BASE = import.meta.env.VITE_API_URL || ''

/**
 * Hook to fetch vertical config, data, and analysis.
 * Re-fetches when verticalId changes.
 */
export function useVerticalData(verticalId) {
  const [config, setConfig] = useState(null)
  const [data, setData] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const fetchRef = useRef(0)

  const fetchVertical = useCallback(async () => {
    const fetchId = ++fetchRef.current
    setLoading(true)
    setError(null)

    try {
      // Fetch config and data in parallel
      const [configRes, dataRes] = await Promise.all([
        fetch(`${API_BASE}/api/v/${verticalId}/config`),
        fetch(`${API_BASE}/api/v/${verticalId}/data`),
      ])

      if (fetchId !== fetchRef.current) return // Stale

      if (!configRes.ok) throw new Error(`Config fetch failed: ${configRes.status}`)
      if (!dataRes.ok) throw new Error(`Data fetch failed: ${dataRes.status}`)

      const configData = await configRes.json()
      const rawData = await dataRes.json()

      setConfig(configData)
      setData(rawData)

      // Fetch analysis (non-blocking — may take longer)
      try {
        const analysisRes = await fetch(`${API_BASE}/api/v/${verticalId}/analysis`)
        if (fetchId === fetchRef.current && analysisRes.ok) {
          setAnalysis(await analysisRes.json())
        }
      } catch {
        // Analysis is optional
      }
    } catch (e) {
      if (fetchId === fetchRef.current) {
        setError(e.message)
      }
    } finally {
      if (fetchId === fetchRef.current) {
        setLoading(false)
      }
    }
  }, [verticalId])

  useEffect(() => {
    fetchVertical()
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchVertical, 300000)
    return () => clearInterval(interval)
  }, [fetchVertical])

  return { config, data, analysis, loading, error, refresh: fetchVertical }
}


/**
 * Hook to list all available verticals.
 */
export function useVerticals() {
  const [verticals, setVerticals] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_BASE}/api/verticals`)
      .then(r => r.json())
      .then(d => {
        setVerticals(d.verticals || [])
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  return { verticals, loading }
}


/**
 * Extract latest value from a FRED data series.
 */
export function getLatest(data, seriesId) {
  const series = data?.data?.[seriesId]
  if (!series || !Array.isArray(series) || series.length === 0) return null
  const last = series[series.length - 1]
  if (!last?.value) return null
  return parseFloat(last.value)
}

/**
 * Format a number based on format string.
 */
export function fmt(value, format = '.2f', suffix = '%') {
  if (value == null || isNaN(value)) return '—'
  let formatted
  if (format.includes(',')) {
    formatted = value.toLocaleString('en-US', {
      minimumFractionDigits: parseInt(format.match(/(\d+)f/)?.[1] || '0'),
      maximumFractionDigits: parseInt(format.match(/(\d+)f/)?.[1] || '0'),
    })
  } else {
    const decimals = parseInt(format.match(/(\d+)f/)?.[1] || '2')
    formatted = value.toFixed(decimals)
  }
  return `${formatted}${suffix}`
}
