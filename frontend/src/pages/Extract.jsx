import { useEffect, useState } from 'react'
import { extractUrl, trackProduct } from '../api'
import { detectFields, inferCurrency } from '../components/ResultCard'
import Shell from '../components/Shell'
import ParticleField from '../components/ParticleField'
import ResultCard from '../components/ResultCard'

const EXAMPLES = [
  {
    url: 'https://books.toscrape.com/',
    query: 'all book titles and their prices',
  },
  {
    url: 'https://en.wikipedia.org/wiki/Web_scraping',
    query: 'key dates mentioned',
  },
  {
    url: 'https://news.ycombinator.com/',
    query: 'top story titles and their links',
  },
]

function dispatchIntensity(count) {
  window.dispatchEvent(new CustomEvent('pm:intensity', { detail: count }))
}

function ExampleChips({ onPick }) {
  return (
    <div className="mt-4 flex flex-wrap gap-2">
      <span className="self-center font-mono text-xs uppercase tracking-wider text-faint">
        Try:
      </span>
      {EXAMPLES.map((ex) => (
        <button
          key={ex.url}
          type="button"
          onClick={() => onPick(ex)}
          className="rounded-full border border-line bg-panel px-3 py-1.5 text-xs text-dim transition hover:border-accent hover:text-strong"
          style={{ transitionTimingFunction: 'var(--ease)' }}
        >
          {ex.query}
        </button>
      ))}
    </div>
  )
}

export default function Extract() {
  const [url, setUrl] = useState('')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  // Bridge: drive the 3D background whenever results change.
  useEffect(() => {
    dispatchIntensity(data?.results?.length || 0)
  }, [data])

  // Reset the field when leaving the page.
  useEffect(() => () => dispatchIntensity(0), [])

  function pickExample(ex) {
    setUrl(ex.url)
    setQuery(ex.query)
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setData(null)
    dispatchIntensity(0) // calm the field while a new search runs
    setLoading(true)
    try {
      const res = await extractUrl(url, query)
      setData(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const results = data?.results || []
  const hasResults = results.length > 0
  const isErrorSource = data?.source === 'error'

  const trackableCount = results.filter((r) => {
    const { priceKey, nameKey } = detectFields(r)
    return priceKey && nameKey
  }).length

  function handleTrack(item) {
    const { priceKey, nameKey } = detectFields(item)
    const priceVal = priceKey ? String(item[priceKey]) : undefined
    return trackProduct({
      url,
      name: nameKey ? String(item[nameKey]) : undefined,
      price: priceVal,
      currency: inferCurrency(priceVal),
    })
  }

  return (
    <Shell>
      <ParticleField />

      <div className="relative z-10">
        <header className="text-center">
          <h1 className="text-4xl font-bold leading-tight text-strong sm:text-5xl">
            Extract anything from any page
          </h1>
          <p className="mx-auto mt-3 max-w-2xl text-dim">
            Paste a URL, describe what you want in plain language, and get clean
            structured results — powered by AI.
          </p>
        </header>

        <form onSubmit={onSubmit} className="glass-strong mt-8 space-y-4 p-6">
          <div>
            <label className="font-mono text-xs uppercase tracking-wider text-faint">
              URL
            </label>
            <input
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://books.toscrape.com/"
              className="mt-1.5 w-full rounded-xl border border-line bg-ink/40 px-4 py-3 text-body outline-none transition focus:border-accent"
              style={{ transitionTimingFunction: 'var(--ease)' }}
            />
          </div>
          <div>
            <label className="font-mono text-xs uppercase tracking-wider text-faint">
              What to extract
            </label>
            <textarea
              required
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe what to extract, e.g. 'all book titles and their prices'"
              className="mt-1.5 w-full resize-y rounded-xl border border-line bg-ink/40 px-4 py-3 text-body outline-none transition focus:border-accent"
              style={{ transitionTimingFunction: 'var(--ease)' }}
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="glow w-full rounded-xl bg-accent px-5 py-3 font-semibold text-white transition hover:bg-accent-soft disabled:opacity-50"
            style={{ transitionTimingFunction: 'var(--ease)' }}
          >
            {loading ? 'Extracting…' : 'Extract'}
          </button>

          {!data && !loading && <ExampleChips onPick={pickExample} />}
        </form>

        <div className="mt-8">
          {loading && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="glass animate-pulse space-y-3 p-4">
                  <div className="h-3 w-1/3 rounded bg-line" />
                  <div className="h-3 w-full rounded bg-line" />
                  <div className="h-3 w-2/3 rounded bg-line" />
                  <div className="h-3 w-1/2 rounded bg-line" />
                </div>
              ))}
            </div>
          )}

          {!loading && error && (
            <div className="glass border-red-500/40 p-4 text-sm text-red-400">
              {error}
            </div>
          )}

          {!loading && !error && data && hasResults && (
            <div className="space-y-4">
              {data.summary && (
                <div className="glass p-4 text-sm leading-relaxed text-dim">
                  {data.summary}
                </div>
              )}
              <div className="flex items-center justify-between">
                <p className="font-mono text-sm text-dim">
                  {results.length} result{results.length === 1 ? '' : 's'}
                </p>
                {trackableCount > 0 && (
                  <p className="text-sm text-faint">
                    Found prices? Click Track on a card to monitor it in the Tracker.
                  </p>
                )}
              </div>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {results.map((r, i) => (
                  <ResultCard key={i} item={r} onTrack={handleTrack} />
                ))}
              </div>
            </div>
          )}

          {!loading && !error && data && !hasResults && (
            <div className="glass p-8 text-center">
              <p className="text-lg font-semibold text-strong">
                No results
              </p>
              <p className="mt-2 text-sm text-dim">
                Try rephrasing your query or another URL.
              </p>
              {isErrorSource && data.error && (
                <p className="mt-3 font-mono text-xs text-faint">{data.error}</p>
              )}
              <div className="mt-4 flex justify-center">
                <ExampleChips onPick={pickExample} />
              </div>
            </div>
          )}
        </div>
      </div>
    </Shell>
  )
}
