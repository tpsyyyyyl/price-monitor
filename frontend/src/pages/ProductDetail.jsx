import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, downloadCsv } from '../api'
import Shell from '../components/Shell'
import PriceChart from '../components/PriceChart'
import InsightPanel from '../components/InsightPanel'
import { PctBadge, SiteBadge } from '../components/Badges'
import { formatPrice } from '../format'

export default function ProductDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [product, setProduct] = useState(null)
  const [history, setHistory] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    Promise.all([api('/api/products'), api(`/api/products/${id}/history`)])
      .then(([products, hist]) => {
        if (!alive) return
        const found = products.find((p) => String(p.id) === String(id))
        if (!found) {
          setError('Product not found')
          return
        }
        setProduct(found)
        setHistory(hist)
      })
      .catch((e) => alive && setError(e.message))
    return () => {
      alive = false
    }
  }, [id])

  async function remove() {
    if (!product || !window.confirm(`Stop tracking "${product.name}"?`)) return
    await api(`/api/products/${id}`, { method: 'DELETE' })
    navigate('/')
  }

  if (error) {
    return (
      <Shell>
        <Link to="/" className="text-sm text-dim hover:text-strong">
          ← Back to dashboard
        </Link>
        <p className="mt-4 text-red-400">{error}</p>
      </Shell>
    )
  }

  return (
    <Shell>
      <Link to="/" className="text-sm text-dim hover:text-strong">
        ← Back to dashboard
      </Link>

      <div className="mt-3 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-strong">{product?.name ?? 'Loading…'}</h1>
          {product && (
            <div className="mt-2 flex flex-wrap items-center gap-3 text-sm">
              <SiteBadge site={product.site} />
              <span className="font-semibold text-strong">
                {formatPrice(product.current_price, product.currency)}
              </span>
              <PctBadge pct={product.pct_change} />
              <a
                href={product.url}
                target="_blank"
                rel="noreferrer"
                className="text-dim underline-offset-2 hover:text-strong hover:underline"
              >
                View source ↗
              </a>
            </div>
          )}
        </div>
        {product && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => downloadCsv(product.id, product.name)}
              className="rounded-lg border border-line px-4 py-2 text-sm font-medium text-body transition hover:border-dim hover:text-strong"
            >
              Export CSV
            </button>
            <button
              onClick={remove}
              className="rounded-lg border border-line px-4 py-2 text-sm font-medium text-dim transition hover:border-red-500/50 hover:text-red-400"
            >
              Delete
            </button>
          </div>
        )}
      </div>

      <div className="mt-6 rounded-2xl border border-line bg-panel p-6">
        <h2 className="font-bold text-strong">Price history</h2>
        {history === null && !error ? (
          <div className="flex h-72 items-center justify-center text-sm text-faint">Loading…</div>
        ) : (
          <PriceChart history={history} currency={product?.currency} />
        )}
      </div>

      <div className="mt-6">
        <InsightPanel productId={id} />
      </div>
    </Shell>
  )
}
