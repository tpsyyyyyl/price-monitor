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

export default function ResultCard({ item }) {
  const entries = Object.entries(item || {}).filter(([, v]) => !isEmpty(v))

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
    </div>
  )
}
