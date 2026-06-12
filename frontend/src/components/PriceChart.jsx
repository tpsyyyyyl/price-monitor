import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { formatPrice } from '../format'

function fmtDate(iso) {
  return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

function ChartTooltip({ active, payload, currency }) {
  if (!active || !payload || !payload.length) return null
  const point = payload[0].payload
  return (
    <div className="rounded-lg border border-line bg-panel px-3 py-2 text-xs shadow-lg">
      <p className="text-faint">
        {new Date(point.scraped_at).toLocaleString('en-GB', {
          day: '2-digit',
          month: 'short',
          hour: '2-digit',
          minute: '2-digit',
        })}
      </p>
      <p className="mt-0.5 font-semibold text-strong">{formatPrice(point.price, currency)}</p>
    </div>
  )
}

export default function PriceChart({ history, currency }) {
  if (!history || history.length === 0) {
    return (
      <div className="flex h-72 items-center justify-center text-sm text-faint">
        No price history yet.
      </div>
    )
  }

  // Pad the Y-domain so small fluctuations are visible (design-intel: small changes
  // must remain readable on a trend line).
  const prices = history.map((p) => p.price)
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const pad = Math.max((max - min) * 0.25, max * 0.02, 0.5)
  const domain = [Number((min - pad).toFixed(2)), Number((max + pad).toFixed(2))]

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={history} margin={{ top: 10, right: 16, bottom: 0, left: -8 }}>
          <CartesianGrid stroke="var(--t-line)" vertical={false} />
          <XAxis
            dataKey="scraped_at"
            tickFormatter={fmtDate}
            stroke="var(--t-faint)"
            tick={{ fontSize: 12 }}
            minTickGap={24}
          />
          <YAxis
            domain={domain}
            stroke="var(--t-faint)"
            tick={{ fontSize: 12 }}
            tickFormatter={(v) => formatPrice(v, currency)}
            width={64}
          />
          <Tooltip content={<ChartTooltip currency={currency} />} />
          <Line
            type="monotone"
            dataKey="price"
            stroke="var(--color-accent)"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
