import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, saveToken } from '../api'
import AnimatedBackground from '../components/AnimatedBackground'
import ThemeControls from '../components/ThemeControls'

export default function Login() {
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function openDemo() {
    setError('')
    setBusy(true)
    try {
      const { token } = await api('/api/auth/demo', { method: 'POST' })
      saveToken(token)
      navigate('/')
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden px-6">
      <AnimatedBackground />
      <div className="absolute right-6 top-6 z-[1]">
        <ThemeControls />
      </div>
      <div className="relative z-[1] w-full max-w-md text-center">
        <h1 className="text-3xl font-extrabold text-strong">
          Price<span className="text-accent-soft">Monitor</span>
        </h1>
        <p className="mx-auto mt-3 max-w-sm text-dim">
          Track product prices over time, spot drops at a glance, and get AI-backed buy
          recommendations.
        </p>
        <div className="mt-8 rounded-2xl border border-line bg-panel/70 p-8 shadow-2xl backdrop-blur">
          <p className="text-sm text-dim">
            No sign-up needed — everyone shares a single demo workspace.
          </p>
          <button
            onClick={openDemo}
            disabled={busy}
            className="mt-5 w-full rounded-xl bg-accent py-3 font-semibold text-white shadow-lg shadow-accent/30 transition hover:bg-accent-soft disabled:opacity-50"
          >
            {busy ? 'Opening…' : 'Open demo dashboard'}
          </button>
          {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
        </div>
      </div>
    </div>
  )
}
