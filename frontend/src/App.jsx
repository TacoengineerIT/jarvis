/**
 * App.jsx — Root layout with sidebar navigation, top bar, and routing.
 *
 * Routes:
 *   /           → Intelligence  (main orb, voice state — full-bleed, no sidebar)
 *   /dashboard  → Dashboard     (bento grid)
 *   /academic   → Academic Hub  (RAG / notebooks)
 *   /system     → System DevOps (logs, containers, SSH)
 */
import { Routes, Route, useLocation } from 'react-router-dom'
import { useJARVIS } from './hooks/useJARVIS.js'
import NavigationDrawer from './components/NavigationDrawer.jsx'
import TopBar from './components/TopBar.jsx'
import Intelligence from './pages/Intelligence.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Academic from './pages/Academic.jsx'
import System from './pages/System.jsx'

/* Intelligence page is full-bleed (owns its own nav and bottom bar) */
const FULL_BLEED_ROUTES = ['/']

export default function App() {
  const { state, connected, error } = useJARVIS()
  const location = useLocation()
  const isFullBleed = FULL_BLEED_ROUTES.includes(location.pathname)

  return (
    <div className="h-screen w-screen overflow-hidden bg-surface-container-lowest text-on-surface">

      {/* Sidebar navigation (hidden on full-bleed routes) */}
      {!isFullBleed && <NavigationDrawer />}

      {/* Dynamic island top bar (hidden on full-bleed routes) */}
      {!isFullBleed && (
        <TopBar briefing={state.briefing} connected={connected} />
      )}

      {/* Connection error banner */}
      {error && !isFullBleed && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-[70]
                         flex items-center gap-2 px-5 py-2 rounded-full
                         bg-error/10 border border-error/30 backdrop-blur-xl">
          <span className="material-symbols-outlined text-error text-sm">wifi_off</span>
          <span className="text-xs text-error">{error}</span>
        </div>
      )}

      {/* Route canvas */}
      <Routes>
        <Route path="/"          element={<Intelligence />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/academic"  element={<Academic />} />
        <Route path="/system"    element={<System />} />
        <Route path="*"          element={<NotFound />} />
      </Routes>
    </div>
  )
}

function NotFound() {
  return (
    <div className="ml-16 flex flex-col items-center justify-center h-screen gap-4">
      <span className="material-symbols-outlined text-5xl text-on-surface-variant">
        error_outline
      </span>
      <h1 className="text-2xl font-bold text-primary-fixed">404 — Page not found</h1>
      <a href="/" className="text-sm text-tertiary hover:underline">← Back to Intelligence</a>
    </div>
  )
}
