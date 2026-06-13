import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, saveToken } from '../api'
import ParticleField from '../components/ParticleField'
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
      <ParticleField />
      <div className="absolute right-6 top-6 z-10">
        <ThemeControls />
      </div>
      <div className="relative z-10 w-full max-w-md text-center">
        <h1 className="font-sans text-3xl font-bold tracking-wide text-strong">
          EXTRACT<span className="ml-1.5 inline-block h-2.5 w-2.5 rounded-full bg-accent align-middle" />
        </h1>
        <p className="mx-auto mt-3 max-w-sm text-dim">
          Track product prices over time, spot drops at a glance, and get AI-backed buy
          recommendations.
        </p>
        <div className="glass mt-8 p-8 text-left shadow-2xl">
          <p className="text-center text-sm text-dim">
            No sign-up needed — everyone shares a single demo workspace.
          </p>
          <button
            onClick={openDemo}
            disabled={busy}
            className="glow mt-5 w-full rounded-xl bg-accent py-3 font-semibold text-white transition disabled:opacity-50"
            style={{ transition: `all 0.2s var(--ease)` }}
          >
            {busy ? 'Opening…' : 'Open demo dashboard'}
          </button>
          {error && <p className="mt-4 text-center text-sm text-red-400">{error}</p>}
        </div>
      </div>
    </div>
  )
}
