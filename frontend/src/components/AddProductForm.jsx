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
    <form onSubmit={submit} className="glass-strong p-5">
      <div className="flex flex-col gap-3 sm:flex-row">
        <input
          type="url"
          required
          placeholder="Paste any product URL"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="w-full rounded-lg border border-line bg-ink/60 px-4 py-2.5 font-mono text-strong placeholder-faint outline-none transition focus:border-accent"
          style={{ transition: `border-color 0.15s var(--ease)` }}
        />
        <button
          disabled={busy}
          className="glow shrink-0 rounded-lg bg-accent px-6 py-2.5 font-semibold text-white transition disabled:opacity-50"
          style={{ transition: `all 0.15s var(--ease)` }}
        >
          {busy ? 'Adding…' : 'Track product'}
        </button>
      </div>
      {error && <p className="mt-3 font-mono text-sm text-red-400">{error}</p>}
      <p className="mt-3 text-xs text-faint">
        Works with any site — AI reads the price.
      </p>
    </form>
  )
}
