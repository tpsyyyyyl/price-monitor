const CURRENCY_SYMBOL = { GBP: '£', USD: '$', EUR: '€' }

export function formatPrice(value, currency) {
  if (value === null || value === undefined) return '—'
  const symbol = CURRENCY_SYMBOL[currency] ?? ''
  return `${symbol}${value.toFixed(2)}${symbol ? '' : ` ${currency}`}`
}

export function formatRelative(iso) {
  if (!iso) return 'never'
  const then = new Date(iso)
  const diff = Date.now() - then.getTime()
  const mins = Math.round(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.round(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  if (days < 30) return `${days}d ago`
  return then.toLocaleDateString('en-GB')
}

// A price drop is GOOD for a buyer → green; a rise → red; null/0 → neutral.
export function pctChangeStyle(pct) {
  if (pct === null || pct === undefined || pct === 0) {
    return { className: 'bg-slate-500/15 text-dim', arrow: '→', label: '0%' }
  }
  const abs = Math.abs(pct).toFixed(1)
  if (pct < 0) {
    return { className: 'bg-emerald-500/15 text-emerald-400', arrow: '↓', label: `${abs}%` }
  }
  return { className: 'bg-red-500/15 text-red-400', arrow: '↑', label: `${abs}%` }
}
