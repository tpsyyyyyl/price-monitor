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
          <h1 className="text-2xl font-bold text-strong">Tracked products</h1>
          <p className="mt-1 text-sm text-dim">
            {items ? `${items.length} tracked` : 'Loading…'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => scrape(false)}
            disabled={scrapeBusy}
            className="rounded-xl bg-accent px-5 py-2.5 font-semibold text-white shadow-lg shadow-accent/30 transition hover:bg-accent-soft disabled:opacity-50"
          >
            {scrapeBusy ? 'Working…' : 'Scrape now'}
          </button>
          <button
            onClick={() => scrape(true)}
            disabled={scrapeBusy}
            title="Demo only: re-checks prices but nudges them randomly so you can see changes and alerts"
            className="rounded-xl border border-line px-4 py-2.5 font-medium text-body transition hover:border-dim hover:text-strong disabled:opacity-50"
          >
            Simulate change
          </button>
        </div>
      </div>

      {scrapeMsg && (
        <p className="mt-3 rounded-lg border border-line bg-panel px-4 py-2 text-sm text-dim">
          {scrapeMsg}
        </p>
      )}

      <div className="mt-6">
        <AddProductForm onAdded={onAdded} />
      </div>

      {error && <p className="mt-6 text-red-400">{error}</p>}

      {items && items.length === 0 && (
        <div className="mt-10 rounded-2xl border border-dashed border-line p-16 text-center">
          <p className="text-lg font-semibold text-strong">No products tracked yet</p>
          <p className="mt-2 text-sm text-dim">
            Add a product URL above, or seed demo data with{' '}
            <code className="text-faint">python -m backend.seed_demo</code>.
          </p>
        </div>
      )}

      {items && items.length > 0 && (
        <div className="mt-6 overflow-x-auto rounded-2xl border border-line bg-panel">
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
                <tr key={p.id} className="border-b border-line last:border-0 hover:bg-ink/40">
                  <td className="px-5 py-3">
                    <Link
                      to={`/product/${p.id}`}
                      className="font-medium text-strong hover:text-accent-soft"
                    >
                      {p.name}
                    </Link>
                  </td>
                  <td className="px-5 py-3">
                    <SiteBadge site={p.site} />
                  </td>
                  <td className="px-5 py-3 font-semibold text-strong">
                    {formatPrice(p.current_price, p.currency)}
                  </td>
                  <td className="px-5 py-3">
                    <PctBadge pct={p.pct_change} />
                  </td>
                  <td className="px-5 py-3 text-dim">{formatRelative(p.last_checked_at)}</td>
                  <td className="px-5 py-3 text-right">
                    <button
                      onClick={() => remove(p.id, p.name)}
                      title="Stop tracking"
                      className="rounded-lg border border-line px-3 py-1.5 text-dim transition hover:border-red-500/50 hover:text-red-400"
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
