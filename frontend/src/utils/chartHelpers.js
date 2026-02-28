/**
 * Downsample a series for better chart performance.
 * Takes every nth point, always keeping first and last.
 *
 * Signature 1: downsample(dates, values, maxPoints) → { dates, values }
 * Signature 2: downsample(arrayOfObjects, maxPoints) → arrayOfObjects (thinned)
 */
export function downsample(arg1, arg2, arg3) {
  // Signature 2: array of objects
  if (Array.isArray(arg1) && typeof arg2 === 'number') {
    const arr = arg1
    const maxPoints = arg2
    if (arr.length <= maxPoints) return arr
    const step = Math.ceil(arr.length / maxPoints)
    const out = []
    for (let i = 0; i < arr.length; i += step) {
      out.push(arr[i])
    }
    if (out[out.length - 1] !== arr[arr.length - 1]) {
      out.push(arr[arr.length - 1])
    }
    return out
  }

  // Signature 1: separate dates + values arrays
  const dates = arg1, values = arg2, maxPoints = arg3 || 300
  if (dates.length <= maxPoints) return { dates, values }
  const step = Math.ceil(dates.length / maxPoints)
  const d = [], v = []
  for (let i = 0; i < dates.length; i += step) {
    d.push(dates[i])
    v.push(values[i])
  }
  // Ensure last point included
  if (d[d.length - 1] !== dates[dates.length - 1]) {
    d.push(dates[dates.length - 1])
    v.push(values[values.length - 1])
  }
  return { dates: d, values: v }
}

/**
 * Format a date string for chart labels (YYYY-MM)
 */
export function shortDate(d) {
  return d ? d.slice(0, 7) : ''
}

/**
 * Compute rolling correlation between two value arrays.
 */
export function rollingCorrelation(x, y, window = 30) {
  const n = Math.min(x.length, y.length)
  const dx = [], dy = []
  for (let i = 1; i < n; i++) {
    dx.push(x[i] - x[i - 1])
    dy.push(y[i] - y[i - 1])
  }

  const corrs = []
  for (let i = window; i < dx.length; i++) {
    const sx = dx.slice(i - window, i)
    const sy = dy.slice(i - window, i)
    const mx = sx.reduce((a, b) => a + b, 0) / window
    const my = sy.reduce((a, b) => a + b, 0) / window
    let num = 0, ddx = 0, ddy = 0
    for (let j = 0; j < window; j++) {
      const a = sx[j] - mx, b = sy[j] - my
      num += a * b; ddx += a * a; ddy += b * b
    }
    const denom = Math.sqrt(ddx * ddy)
    corrs.push(denom > 0 ? num / denom : 0)
  }
  return corrs
}
