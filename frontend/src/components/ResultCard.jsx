import { useState } from 'react'

const PRICE_KEY_RE = /price|cost|amount|ціна|вартість/i
const PRICE_VAL_RE = /[£$€]\s?\d|\d+[.,]\d{2}/
const NAME_KEY_RE = /name|title|product|назв/i

function detectFields(item) {
  const entries = Object.entries(item || {})

  let priceKey = null
  let nameKey = null

  for (const [k, v] of entries) {
    const strV = String(v)
    if (!priceKey && (PRICE_KEY_RE.test(k) || PRICE_VAL_RE.test(strV))) {
      priceKey = k
    }
    if (!nameKey && NAME_KEY_RE.test(k) && typeof v === 'string') {
      nameKey = k
    }
  }

  // fallback name: first string field that isn't the price field
  if (!nameKey) {
    for (const [k, v] of entries) {
      if (typeof v === 'string' && k !== priceKey) {
        nameKey = k
        break
      }
    }
  }

  return { priceKey, nameKey }
}

function inferCurrency(priceStr) {
  if (!priceStr) return undefined
  if (priceStr.includes('£')) return 'GBP'
  if (priceStr.includes('$')) return 'USD'
  if (priceStr.includes('€')) return 'EUR'
  return undefined
}

function renderValue(value) {
  if (typeof value === 'string' && value.startsWith('http')) {
    return (
      <a
        href={value}
        target="_blank"
        rel="noreferrer"
        className="text-accent-2 hover:underline break-all"
      >
        {value}
      </a>
    )
  }
  if (typeof value === 'object') {
    return <span className="break-all">{JSON.stringify(value)}</span>
  }
  return <span className="break-words">{String(value)}</span>
}

function isEmpty(value) {
  if (value === null || value === undefined) return true
  if (typeof value === 'string' && value.trim() === '') return true
  if (Array.isArray(value) && value.length === 0) return true
  return false
}

export default function ResultCard({ item, onTrack }) {
  const [status, setStatus] = useState(null) // null | 'pending' | 'done' | 'error'
  const [errorMsg, setErrorMsg] = useState('')

  const entries = Object.entries(item || {}).filter(([, v]) => !isEmpty(v))
  const { priceKey, nameKey } = detectFields(item)
  const isTrackable = onTrack && priceKey && nameKey

  async function handleTrack() {
    setStatus('pending')
    setErrorMsg('')
    try {
      await onTrack(item)
      setStatus('done')
    } catch (err) {
      setStatus('error')
      setErrorMsg(err.status === 409 ? 'Already tracked' : (err.message || 'Error'))
    }
  }

  return (
    <div
      className="glass p-4 transition duration-300 hover:-translate-y-1 hover:glow"
      style={{ transitionTimingFunction: 'var(--ease)' }}
    >
      <div className="space-y-3">
        {entries.map(([key, value]) => (
          <div key={key}>
            <p className="font-mono text-[10px] uppercase tracking-wider text-faint">
              {key}
            </p>
            <div className="mt-0.5 text-sm text-body">{renderValue(value)}</div>
          </div>
        ))}
      </div>

      {isTrackable && (
        <div className="mt-3 flex items-center gap-2">
          {status === 'done' ? (
            <span className="text-xs text-accent-2">✓ Tracked</span>
          ) : status === 'error' ? (
            <span className="text-xs text-red-400">{errorMsg}</span>
          ) : (
            <button
              onClick={handleTrack}
              disabled={status === 'pending'}
              className="rounded-md border border-line px-2 py-1 text-xs text-accent-2 transition hover:border-accent disabled:opacity-50"
              style={{ transitionTimingFunction: 'var(--ease)' }}
            >
              {status === 'pending' ? 'Adding…' : 'Track'}
            </button>
          )}
        </div>
      )}
    </div>
  )
}

export { detectFields, inferCurrency }
