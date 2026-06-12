import { useState } from 'react'
import { api } from '../api'

export default function AddProductForm({ onAdded }) {
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      const product = await api('/api/products', { method: 'POST', body: { url: url.trim() } })
      setUrl('')
      onAdded(product)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="rounded-2xl border border-line bg-panel p-5">
      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          type="url"
          required
          placeholder="https://books.toscrape.com/catalogue/…"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="w-full rounded-lg border border-line bg-ink px-4 py-2.5 text-strong placeholder-faint outline-none transition focus:border-accent"
        />
        <button
          disabled={busy}
          className="shrink-0 rounded-lg bg-accent px-6 py-2.5 font-semibold text-white transition hover:bg-accent-soft disabled:opacity-50"
        >
          {busy ? 'Adding…' : 'Track product'}
        </button>
      </div>
      {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
      <p className="mt-3 text-xs text-faint">
        Supported sites: <span className="text-dim">books.toscrape.com</span> and{' '}
        <span className="text-dim">scrapeme.live</span>. Example:{' '}
        <code className="text-dim">
          https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html
        </code>
      </p>
    </form>
  )
}
