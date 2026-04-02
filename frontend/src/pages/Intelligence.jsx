/**
 * Intelligence.jsx — V5.5 Polished Intelligence Interface
 * Own sidebar, financial stats header, large central orb, status cards footer.
 */
import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useJARVIS, getStateLabel } from '../hooks/useJARVIS.js'
import MercuryOrb from '../components/MercuryOrb.jsx'
import WaveformAnimation from '../components/WaveformAnimation.jsx'

const NAV = [
  { to: '/',          icon: 'home',            label: 'Intel'     },
  { to: '/dashboard', icon: 'dashboard',        label: 'Dash'      },
  { to: '/financial', icon: 'account_balance',  label: 'Finance'   },
  { to: '/academic',  icon: 'school',           label: 'Academic'  },
  { to: '/system',    icon: 'terminal',         label: 'System'    },
]

export default function Intelligence() {
  const { state, connected, loading, error, sendInput } = useJARVIS()
  const [inputVal, setInputVal] = useState('')

  const handleSend = () => {
    if (!inputVal.trim() || loading) return
    sendInput(inputVal.trim())
    setInputVal('')
  }

  const rentGap     = 110
  const portfolio   = (2000 - state.today_spent).toFixed(2)
  const budgetPct   = Math.min((state.today_spent / 15) * 100, 100)
  const lastCmd     = state.last_5_commands[state.last_5_commands.length - 1]

  const headline = {
    RECORDING:  <>Recording <span className="text-tertiary">...</span></>,
    ACTIVE:     <>Recording <span className="text-tertiary">...</span></>,
    PROCESSING: <>Processing <span className="text-tertiary">...</span></>,
    SPEAKING:   <>Responding <span className="text-tertiary">...</span></>,
  }[state.jarvis_state] || <>V5.5 <span className="text-tertiary">Active</span></>

  return (
    <div className="h-screen w-screen bg-black flex overflow-hidden">

      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <nav className="flex-shrink-0 w-20 h-full flex flex-col py-8 z-50
                      border-r border-white/5 apple-glass items-center gap-0">
        <div className="flex flex-col items-center mb-10">
          <div className="w-9 h-9 rounded-full bg-zinc-800/60 flex items-center justify-center mb-2">
            <div className="w-full h-full mercury-gradient rounded-full opacity-80" />
          </div>
          <span className="font-bold tracking-widest text-[8px] uppercase text-zinc-400">
            JARVIS
          </span>
        </div>

        <div className="flex flex-col gap-5 items-center flex-1">
          {NAV.map(({ to, icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                isActive
                  ? 'flex flex-col items-center gap-1 text-white bg-white/10 rounded-2xl w-14 h-14 justify-center transition-all duration-300 scale-105'
                  : 'flex flex-col items-center gap-1 text-zinc-500 hover:text-zinc-200 hover:bg-white/5 transition-all duration-300 w-14 h-14 rounded-2xl justify-center'
              }
            >
              <span className="material-symbols-outlined text-xl">{icon}</span>
              <span className="text-[7px] uppercase tracking-widest">{label}</span>
            </NavLink>
          ))}
        </div>

        <div className="mt-auto flex flex-col items-center gap-3">
          <div className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-tertiary shadow-[0_0_6px_#ffdd79]' : 'bg-error'}`} />
        </div>
      </nav>

      {/* ── Main ────────────────────────────────────────────────────── */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">

        {/* ── Financial Stats Header ─────────────────────────────────── */}
        <header className="flex-shrink-0 flex items-center gap-6 px-10 py-4
                            border-b border-white/5 apple-glass">
          {error && (
            <div className="flex items-center gap-2 text-error text-xs mr-2">
              <span className="material-symbols-outlined text-sm">wifi_off</span>
              {error}
            </div>
          )}

          <div className="flex items-baseline gap-2">
            <span className="text-[10px] uppercase tracking-widest text-zinc-500">Portfolio</span>
            <span className="text-lg font-bold text-white">€{portfolio}</span>
          </div>

          <div className="w-px h-5 bg-white/10" />

          <div className="flex items-baseline gap-2">
            <span className="text-[10px] uppercase tracking-widest text-zinc-500">Rent Gap</span>
            <span className="text-lg font-bold text-tertiary">€{rentGap}</span>
          </div>

          <div className="w-px h-5 bg-white/10" />

          <div className="flex items-baseline gap-2">
            <span className="text-[10px] uppercase tracking-widest text-zinc-500">Daily</span>
            <span className="text-sm font-semibold text-zinc-200">€{state.today_spent.toFixed(2)}</span>
          </div>

          {/* Budget bar */}
          <div className="flex-1 max-w-xs">
            <div className="h-0.5 w-full bg-zinc-800 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-700 rounded-full ${
                  budgetPct > 80 ? 'bg-error' : 'bg-tertiary'
                }`}
                style={{ width: `${budgetPct}%` }}
              />
            </div>
          </div>

          <div className="ml-auto flex items-center gap-3">
            <div className="overflow-hidden max-w-[200px]">
              <p className="text-[10px] text-zinc-500 tracking-widest whitespace-nowrap marquee-text">
                {state.briefing || 'BRIEFING: All systems nominal · Neural link stable'}
              </p>
            </div>
            <div className={`w-2 h-2 rounded-full flex-shrink-0 ${connected ? 'bg-tertiary shadow-[0_0_6px_#ffdd79]' : 'bg-error'}`} />
          </div>
        </header>

        {/* ── Center Canvas ─────────────────────────────────────────── */}
        <div className="flex-1 flex items-center justify-center relative overflow-hidden">
          {/* Ambient glow */}
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-96 h-96
                            bg-primary/5 blur-[120px] rounded-full" />
            <div className="absolute bottom-1/4 right-1/4 w-64 h-64
                            bg-tertiary/5 blur-[80px] rounded-full" />
          </div>

          <div className="flex flex-col items-center gap-8 z-10">
            {/* Large orb ~w-56 */}
            <div className="relative w-56 h-56 flex-shrink-0">
              <MercuryOrb jarvisState={state.jarvis_state} size="lg" />
            </div>

            <div className="text-center">
              <h1 className="text-4xl font-black tracking-tighter text-white mb-2 uppercase">
                {headline}
              </h1>
              <p className="text-zinc-500 tracking-[0.2em] text-[10px] uppercase">
                {connected ? getStateLabel(state.jarvis_state) : 'Awaiting connection'}
              </p>
              {state.mood && (
                <p className="text-2xl mt-3">{state.mood}</p>
              )}
            </div>
          </div>
        </div>

        {/* ── Status Cards ──────────────────────────────────────────── */}
        <div className="flex-shrink-0 grid grid-cols-3 gap-0 border-t border-white/5">
          {/* Engine state */}
          <div className="apple-glass px-8 py-5 border-r border-white/5">
            <p className="text-[9px] uppercase tracking-widest text-zinc-600 mb-1">Engine State</p>
            <p className="text-sm font-bold text-white">{getStateLabel(state.jarvis_state)}</p>
            <div className="flex items-center gap-2 mt-2">
              <div className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-tertiary animate-pulse' : 'bg-error'}`} />
              <span className="text-[9px] text-zinc-500 uppercase tracking-widest">
                {connected ? 'HTTP Link Active' : 'Disconnected'}
              </span>
            </div>
          </div>

          {/* Last command */}
          <div className="apple-glass px-8 py-5 border-r border-white/5">
            <p className="text-[9px] uppercase tracking-widest text-zinc-600 mb-1">Last Command</p>
            {lastCmd ? (
              <>
                <p className="text-sm font-mono text-white truncate">{lastCmd.user || lastCmd.input}</p>
                <p className="text-[10px] text-zinc-500 mt-1 truncate italic">{lastCmd.response?.slice(0, 60)}</p>
              </>
            ) : (
              <p className="text-sm text-zinc-600">—</p>
            )}
          </div>

          {/* API cost */}
          <div className="apple-glass px-8 py-5">
            <p className="text-[9px] uppercase tracking-widest text-zinc-600 mb-1">API Cost</p>
            <p className="text-sm font-bold text-white">€{state.api_cost_today.toFixed(4)}</p>
            <p className="text-[10px] text-zinc-500 mt-1">{state.last_5_commands.length} requests today</p>
          </div>
        </div>

        {/* ── Transcription Dock ─────────────────────────────────────── */}
        <div className="flex-shrink-0 border-t border-white/5 apple-glass px-8 py-4">
          <div className="max-w-2xl mx-auto flex items-center gap-4">
            <span className={`material-symbols-outlined flex-shrink-0 transition-colors ${
              ['RECORDING','SPEAKING'].includes(state.jarvis_state)
                ? 'text-tertiary drop-shadow-[0_0_8px_rgba(255,221,121,0.5)]'
                : 'text-zinc-600'
            }`}>
              keyboard_voice
            </span>

            <input
              value={inputVal}
              onChange={e => setInputVal(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleSend() }}
              disabled={loading}
              placeholder="Instruct J.A.R.V.I.S. ..."
              className="flex-1 bg-transparent border-none focus:outline-none text-sm
                          text-white placeholder:text-zinc-600 disabled:opacity-50"
            />

            {['RECORDING','SPEAKING'].includes(state.jarvis_state) ? (
              <WaveformAnimation active />
            ) : (
              <button
                onClick={handleSend}
                disabled={loading || !inputVal.trim()}
                className="w-8 h-8 rounded-full bg-white text-black flex items-center justify-center
                            hover:scale-105 active:scale-95 transition-all disabled:opacity-30"
              >
                <span className="material-symbols-outlined text-sm">send</span>
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
