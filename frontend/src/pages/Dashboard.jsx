import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import Shell from '../components/Shell'
import AddProductForm from '../components/AddProductForm'
import { PctBadge, SiteBadge } from '../components/Badges'
import { formatPrice, formatRelative } from '../format'

export default function Dashboard() {
  const [items, setItems] = useState(null)
  const [error, setError] = useState('')
  const [scrapeBusy, setScrapeBusy] = useState(false)
  const [scrapeMsg, setScrapeMsg] = useState('')

  function load() {
    api('/api/products')
      .then(setItems)
      .catch((e) => setError(e.message))
  }

  useEffect(load, [])

  async function scrape(jitter) {
    setScrapeBusy(true)
    setScrapeMsg('')
    try {
      const q = jitter ? '?jitter=true' : ''
      const r = await api(`/api/scrape${q}`, { method: 'POST' })
      setScrapeMsg(`Scraped ${r.scraped} · failed ${r.failed} · ${r.alerts} price alert(s)`)
      load()
    } catch (e) {
      setScrapeMsg(e.message)
    } finally {
      setScrapeBusy(false)
    }
  }

  async function remove(id, name) {
    if (!window.confirm(`Stop tracking "${name}"?`)) return
    await api(`/api/products/${id}`, { method: 'DELETE' })
    setItems((prev) => prev.filter((p) => p.id !== id))
  }

  function onAdded(product) {
    setItems((prev) => [product, ...(prev ?? [])])
  }

  return (
    <Shell>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-sans text-2xl font-bold text-strong">Tracked products</h1>
          <p className="mt-1 font-mono text-sm text-dim">
            {items ? `${items.length} tracked` : 'Loading…'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => scrape(false)}
            disabled={scrapeBusy}
            className="glow rounded-xl bg-accent px-5 py-2.5 font-semibold text-white transition disabled:opacity-50"
            style={{ transition: `all 0.2s var(--ease)` }}
          >
            {scrapeBusy ? 'Working…' : 'Scrape now'}
          </button>
          <button
            onClick={() => scrape(true)}
            disabled={scrapeBusy}
            title="Demo only: re-checks prices but nudges them randomly so you can see changes and alerts"
            className="rounded-xl border border-line px-4 py-2.5 font-medium text-body transition hover:border-accent hover:text-strong disabled:opacity-50"
            style={{ transition: `all 0.2s var(--ease)` }}
          >
            Simulate change
          </button>
        </div>
      </div>

      {scrapeMsg && (
        <p className="glass-strong mt-3 rounded-xl px-4 py-2 font-mono text-sm text-dim">
          {scrapeMsg}
        </p>
      )}

      <div className="mt-6">
        <AddProductForm onAdded={onAdded} />
      </div>

      {error && <p className="mt-6 font-mono text-red-400">{error}</p>}

      {items && items.length === 0 && (
        <div className="glass-strong mt-10 border-dashed p-16 text-center">
          <p className="font-sans text-lg font-semibold text-strong">No products tracked yet</p>
          <p className="mt-2 text-sm text-dim">
            Add a product URL above, or seed demo data with{' '}
            <code className="font-mono text-faint">python -m backend.seed_demo</code>.
          </p>
        </div>
      )}

      {items && items.length > 0 && (
        <div className="glass-strong mt-6 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-line text-xs uppercase tracking-wide text-faint">
              <tr>
                <th className="px-5 py-3 font-medium">Product</th>
                <th className="px-5 py-3 font-medium">Site</th>
                <th className="px-5 py-3 font-medium">Price</th>
                <th className="px-5 py-3 font-medium">Change</th>
                <th className="px-5 py-3 font-medium">Checked</th>
                <th className="px-5 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr
                  key={p.id}
                  className="border-b border-line last:border-0 transition-colors hover:bg-accent/5"
                  style={{ transition: `background-color 0.15s var(--ease)` }}
                >
                  <td className="px-5 py-3">
                    <Link
                      to={`/product/${p.id}`}
                      className="font-medium text-strong transition-colors hover:text-accent"
                    >
                      {p.name}
                    </Link>
                  </td>
                  <td className="px-5 py-3">
                    <SiteBadge site={p.site} />
                  </td>
                  <td className="px-5 py-3 font-mono font-semibold text-strong">
                    {formatPrice(p.current_price, p.currency)}
                  </td>
                  <td className="px-5 py-3">
                    <PctBadge pct={p.pct_change} />
                  </td>
                  <td className="px-5 py-3 font-mono text-dim">{formatRelative(p.last_checked_at)}</td>
                  <td className="px-5 py-3 text-right">
                    <button
                      onClick={() => remove(p.id, p.name)}
                      title="Stop tracking"
                      className="rounded-lg border border-line px-3 py-1.5 text-dim transition hover:border-red-500/50 hover:text-red-400"
                      style={{ transition: `all 0.15s var(--ease)` }}
                    >
                      ✕
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Shell>
  )
}
