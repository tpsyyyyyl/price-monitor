import { NavLink, useNavigate } from 'react-router-dom'
import { clearToken } from '../api'
import ParticleField from './ParticleField'
import ThemeControls from './ThemeControls'

export default function Shell({ children }) {
  const navigate = useNavigate()

  function logout() {
    clearToken()
    navigate('/login')
  }

  return (
    <div className="relative min-h-screen overflow-hidden">
      <ParticleField />
      <nav className="glass sticky top-0 z-20 rounded-none border-x-0 border-t-0">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
          <span className="font-sans text-lg font-bold tracking-wide text-strong">
            EXTRACT<span className="ml-1 inline-block h-2 w-2 rounded-full bg-accent align-middle" />
          </span>
          <div className="flex items-center gap-6">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `relative text-sm font-medium transition-colors duration-200 ${
                  isActive
                    ? 'text-strong after:absolute after:-bottom-0.5 after:left-0 after:h-0.5 after:w-full after:rounded-full after:bg-accent after:content-[""]'
                    : 'text-dim hover:text-body'
                }`
              }
            >
              Extract
            </NavLink>
            <NavLink
              to="/tracker"
              className={({ isActive }) =>
                `relative text-sm font-medium transition-colors duration-200 ${
                  isActive
                    ? 'text-strong after:absolute after:-bottom-0.5 after:left-0 after:h-0.5 after:w-full after:rounded-full after:bg-accent after:content-[""]'
                    : 'text-dim hover:text-body'
                }`
              }
            >
              Tracker
            </NavLink>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <ThemeControls />
            <button
              onClick={logout}
              className="rounded-lg border border-line px-3 py-1.5 text-body transition hover:border-accent hover:text-strong"
              style={{ transition: `all 0.2s var(--ease)` }}
            >
              Log out
            </button>
          </div>
        </div>
      </nav>
      <main className="relative z-10 mx-auto max-w-5xl px-6 py-10">{children}</main>
    </div>
  )
}
