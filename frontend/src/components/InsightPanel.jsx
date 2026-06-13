import { useEffect, useState } from 'react'
import { api } from '../api'

const TREND = {
  up: { arrow: '↑', className: 'text-accent-3', label: 'Trending up' },
  down: { arrow: '↓', className: 'text-accent-2', label: 'Trending down' },
  stable: { arrow: '→', className: 'text-dim', label: 'Stable' },
}

export default function InsightPanel({ productId }) {
  const [state, setState] = useState({ insight: null, error: '' })
  const { insight, error } = state

  useEffect(() => {
    let alive = true
    api(`/api/products/${productId}/insight`)
      .then((d) => alive && setState({ insight: d, error: '' }))
      .catch((e) => alive && setState({ insight: null, error: e.message }))
    return () => {
      alive = false
    }
  }, [productId])

  return (
    <div className="glass-strong p-6">
      <div className="flex items-center justify-between">
        <h2 className="font-sans font-bold text-strong">AI insight</h2>
        {insight && (
          <span className="rounded-full border border-line bg-panel px-2.5 py-0.5 font-mono text-xs font-medium uppercase tracking-wide text-dim backdrop-blur-sm">
            {insight.source}
          </span>
        )}
      </div>

      {error && <p className="mt-4 font-mono text-sm text-red-400">{error}</p>}

      {!insight && !error && (
        <div className="mt-4 animate-pulse space-y-3">
          <div className="h-4 w-1/3 rounded bg-line" />
          <div className="h-3 w-full rounded bg-line" />
          <div className="h-3 w-5/6 rounded bg-line" />
        </div>
      )}

      {insight && (
        <div className="mt-4">
          {(() => {
            const t = TREND[insight.trend] ?? TREND.stable
            return (
              <p className={`flex items-center gap-2 font-semibold ${t.className}`}>
                <span aria-hidden className="text-lg">
                  {t.arrow}
                </span>
                {t.label}
              </p>
            )
          })()}
          <p className="mt-2 font-medium text-strong">{insight.recommendation}</p>
          <p className="mt-1 text-sm leading-relaxed text-dim">{insight.summary}</p>
        </div>
      )}
    </div>
  )
}
