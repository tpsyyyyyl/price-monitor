import { Link, useNavigate } from 'react-router-dom'
import { clearToken } from '../api'
import AnimatedBackground from './AnimatedBackground'
import ThemeControls from './ThemeControls'

export default function Shell({ children }) {
  const navigate = useNavigate()

  function logout() {
    clearToken()
    navigate('/login')
  }

  return (
    <div className="relative min-h-screen overflow-hidden">
      <AnimatedBackground />
      <nav className="sticky top-0 z-10 border-b border-line bg-ink/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Link to="/" className="text-lg font-bold text-strong">
            Price<span className="text-accent-soft">Monitor</span>
          </Link>
          <div className="flex items-center gap-3 text-sm">
            <ThemeControls />
            <button
              onClick={logout}
              className="rounded-lg border border-line px-3 py-1.5 text-body transition hover:border-dim hover:text-strong"
            >
              Log out
            </button>
          </div>
        </div>
      </nav>
      <main className="relative z-[1] mx-auto max-w-5xl px-6 py-10">{children}</main>
    </div>
  )
}
