/**
 * Intelligence.jsx — V5.5 Intelligence Interface
 * Own sidebar (w-20 + labels), central orb, top-left portfolio island,
 * bottom-right system island, bottom transcription dock.
 */
import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useJARVIS, getStateLabel } from '../hooks/useJARVIS.js'
import MercuryOrb from '../components/MercuryOrb.jsx'
import WaveformAnimation from '../components/WaveformAnimation.jsx'

const NAV = [
  { to: '/',          icon: 'home',            label: 'Dashboard' },
  { to: '/dashboard', icon: 'account_balance', label: 'Financial' },
  { to: '/academic',  icon: 'school',          label: 'Academic'  },
  { to: '/system',    icon: 'terminal',        label: 'System'    },
]

export default function Intelligence() {
  const { state, connected, loading, error, sendInput } = useJARVIS()
  const [inputVal, setInputVal] = useState('')

  const handleSend = () => {
    if (!inputVal.trim() || loading) return
    sendInput(inputVal.trim())
    setInputVal('')
  }

  const budgetPct = Math.min((state.today_spent / 15) * 100, 100)
  const lastCmd = state.last_5_commands[state.last_5_commands.length - 1]

  const headline = {
    RECORDING:  <>Recording <span className="text-tertiary">...</span></>,
    ACTIVE:     <>Recording <span className="text-tertiary">...</span></>,
    PROCESSING: <>Processing <span className="text-tertiary">...</span></>,
    SPEAKING:   <>Responding <span className="text-tertiary">...</span></>,
  }[state.jarvis_state] || <>V5.5 <span className="text-tertiary">Active</span></>

  return (
    <div className="h-screen w-screen liquid-mesh flex overflow-hidden">

      {/* ── Own Sidebar ─────────────────────────────────────────────── */}
      <nav className="flex-shrink-0 w-20 h-full flex flex-col py-8 z-50
                      border-r border-zinc-800/15 bg-neutral-950/40 backdrop-blur-3xl
                      shadow-[0_0_32px_rgba(198,198,200,0.06)] items-center">
        {/* Logo */}
        <div className="flex flex-col items-center mb-10">
          <div className="w-10 h-10 rounded-full bg-zinc-800/50 flex items-center
                           justify-center mb-2 overflow-hidden">
            <div className="w-full h-full mercury-gradient rounded-full opacity-80" />
          </div>
          <span className="font-bold tracking-[0.05em] text-[10px] uppercase text-zinc-300">
            J.A.R.V.I.S.
          </span>
        </div>

        {/* Nav items */}
        <div className="flex flex-col gap-6 items-center flex-1">
          {NAV.map(({ to, icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                isActive
                  ? 'flex flex-col items-center justify-center text-zinc-100 bg-zinc-800/50 rounded-xl w-14 h-14 transition-all duration-500 scale-105'
                  : 'flex flex-col items-center justify-center text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/30 transition-all duration-300 w-14 h-14 rounded-xl'
              }
            >
              <span className="material-symbols-outlined">{icon}</span>
              <span className="text-[8px] uppercase tracking-[0.05em] mt-1">{label}</span>
            </NavLink>
          ))}
        </div>

        {/* Settings */}
        <div className="mt-auto flex flex-col items-center gap-5">
          <span className="material-symbols-outlined text-zinc-500 hover:text-zinc-300
                            cursor-pointer transition-colors">
            settings
          </span>
        </div>
      </nav>

      {/* ── Main Canvas ─────────────────────────────────────────────── */}
      <main className="flex-1 h-screen relative flex items-center justify-center p-12 overflow-hidden">

        {/* Background ambient blobs */}
        <div className="absolute top-0 left-0 w-full h-64 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-full h-64 bg-gradient-to-t from-tertiary/5 to-transparent pointer-events-none" />
        <div className="absolute top-1/4 right-1/4 w-64 h-64 floating-blob opacity-20 pointer-events-none" />
        <div className="absolute bottom-1/4 left-1/3 w-96 h-96 floating-blob opacity-10 pointer-events-none" />

        {/* ── Top Dynamic Island ──────────────────────────────────────── */}
        <header className="absolute top-0 left-0 right-0 flex justify-center pointer-events-none z-40">
          <div className="pointer-events-auto rounded-full max-w-md mx-auto mt-4 px-6 py-2
                           bg-neutral-950/40 backdrop-blur-2xl text-zinc-300
                           shadow-[0_0_20px_rgba(198,198,200,0.1)]
                           flex items-center gap-4 border border-white/5">
            <span className="material-symbols-outlined text-zinc-100 text-sm">bubble_chart</span>
            <div className="overflow-hidden flex-1">
              <p className="font-medium tracking-[0.1em] text-xs font-semibold whitespace-nowrap marquee-text">
                {state.briefing || 'MORNING BRIEFING: All systems nominal. Schedule optimized.'}
              </p>
            </div>
            <div className={`w-2 h-2 rounded-full flex-shrink-0 ${connected ? 'bg-tertiary shadow-[0_0_8px_#ffdd79]' : 'bg-error'}`} />
          </div>
        </header>

        {/* Error banner */}
        {error && (
          <div className="absolute top-20 left-1/2 -translate-x-1/2 z-50
                           flex items-center gap-2 px-5 py-2 rounded-full
                           bg-error/10 border border-error/30 backdrop-blur-xl">
            <span className="material-symbols-outlined text-error text-sm">wifi_off</span>
            <span className="text-xs text-error">{error}</span>
          </div>
        )}

        {/* ── Central Orb + Headline ──────────────────────────────────── */}
        <div className="relative z-10 flex flex-col items-center -mt-16">
          <div className="absolute inset-0 blur-[40px] bg-tertiary/15 pointer-events-none" />
          <MercuryOrb jarvisState={state.jarvis_state} size="md" />
          <div className="text-center mt-10">
            <h1 className="text-3xl font-black tracking-tighter text-primary-fixed mb-1 uppercase">
              {headline}
            </h1>
            <p className="text-on-surface-variant tracking-[0.2em] text-[10px] uppercase">
              {connected ? 'Neural link established' : 'Awaiting connection'}
            </p>
          </div>
        </div>

        {/* ── Top-left Floating Island: Portfolio / Watchdog ─────────── */}
        <div className="absolute top-28 left-8 glass-card p-6 rounded-3xl w-68
                        transition-all duration-500 hover:bg-neutral-900/50 hover:scale-[1.02]
                        cursor-default hidden lg:block">
          <div className="flex justify-between items-start mb-5">
            <div>
              <p className="text-on-surface-variant tracking-[0.1em] text-[10px] uppercase mb-1">
                Watchdog
              </p>
              <h2 className="text-2xl font-bold text-primary-fixed tracking-tight">
                €{state.today_spent.toFixed(2)}
                <span className="text-sm font-normal text-on-surface-variant ml-2">today</span>
              </h2>
            </div>
            <span className="material-symbols-outlined text-tertiary">account_balance_wallet</span>
          </div>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-[9px] uppercase tracking-widest text-on-surface-variant mb-1.5">
                <span>Daily Limit</span>
                <span>€15.00 · {budgetPct.toFixed(0)}%</span>
              </div>
              <div className="h-0.5 w-full bg-surface-variant rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-700 ${
                    budgetPct > 90 ? 'bg-error shadow-[0_0_8px_rgba(238,125,119,0.4)]'
                    : budgetPct > 70 ? 'bg-tertiary shadow-[0_0_8px_rgba(255,221,121,0.4)]'
                    : 'bg-primary shadow-[0_0_8px_#ffdd79]'
                  }`}
                  style={{ width: `${budgetPct}%` }}
                />
              </div>
            </div>
            {state.budget_alerts[0] && (
              <p className="text-[9px] text-error bg-error/10 px-2 py-1 rounded-lg border border-error/20 truncate">
                ⚠ {state.budget_alerts[0].message}
              </p>
            )}
            <div className="flex items-center gap-2 text-[10px] text-on-surface-variant pt-1">
              <span className="material-symbols-outlined text-xs">schedule</span>
              <span>Last sync: now</span>
            </div>
          </div>
        </div>

        {/* ── Bottom-right Floating Island: System / Engine ──────────── */}
        <div className="absolute bottom-28 right-8 glass-card p-6 rounded-3xl w-68
                        transition-all duration-500 hover:bg-neutral-900/50 hover:scale-[1.02]
                        cursor-default hidden lg:block">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-8 h-8 rounded-lg bg-surface-container-highest flex items-center justify-center">
              <span className="material-symbols-outlined text-sm text-primary">terminal</span>
            </div>
            <div>
              <p className="text-on-surface-variant tracking-[0.1em] text-[10px] uppercase">
                Engine Status
              </p>
              <h3 className="text-sm font-semibold text-primary-fixed uppercase tracking-wider">
                {connected ? 'Optimal' : 'Offline'}
              </h3>
            </div>
          </div>
          <div className="space-y-3">
            <div className="p-3 bg-white/5 rounded-xl border border-white/5">
              <p className="text-[9px] text-on-surface-variant uppercase tracking-widest mb-1">
                JARVIS State
              </p>
              <p className="text-xs text-primary-fixed font-mono">
                {getStateLabel(state.jarvis_state)}
              </p>
            </div>
            {lastCmd && (
              <div className="p-3 bg-white/5 rounded-xl border border-white/5">
                <p className="text-[9px] text-on-surface-variant uppercase tracking-widest mb-1">
                  Last Command
                </p>
                <p className="text-xs text-on-surface font-mono truncate">
                  {lastCmd.input}
                </p>
              </div>
            )}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <div className={`w-2 h-2 rounded-full ${connected ? 'bg-tertiary animate-pulse' : 'bg-error'}`} />
                <span className="text-[9px] text-on-surface-variant uppercase tracking-widest">
                  WebSocket
                </span>
              </div>
              <span className="text-[9px] text-on-surface-variant uppercase tracking-widest">
                {state.last_5_commands.length} cmds
              </span>
            </div>
          </div>
        </div>

        {/* ── Bottom Transcription Dock ────────────────────────────────── */}
        <div className="fixed bottom-0 left-20 right-0 z-50 flex justify-center pb-8">
          <div className="max-w-xl w-full glass-card rounded-full px-8 py-4
                           flex items-center gap-5 border border-white/5">
            <span className={`material-symbols-outlined flex-shrink-0 ${
              ['RECORDING','SPEAKING'].includes(state.jarvis_state)
                ? 'text-tertiary drop-shadow-[0_0_8px_rgba(255,221,121,0.5)]'
                : 'text-on-surface-variant'
            }`}>
              keyboard_voice
            </span>

            {state.user_input || state.response ? (
              <div className="flex-1 flex items-center gap-2 overflow-hidden">
                {state.user_input && (
                  <span className="text-on-surface-variant text-sm truncate italic">
                    "{state.user_input}"
                  </span>
                )}
                {state.response && !state.user_input && (
                  <span className="text-primary-fixed text-sm truncate">
                    {state.response}
                  </span>
                )}
              </div>
            ) : (
              <input
                value={inputVal}
                onChange={e => setInputVal(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleSend() }}
                disabled={loading}
                placeholder="Instruct J.A.R.V.I.S. ..."
                className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0
                            text-sm text-on-surface placeholder:text-on-surface-variant/50
                            disabled:opacity-50"
              />
            )}

            {['RECORDING','SPEAKING'].includes(state.jarvis_state) ? (
              <WaveformAnimation active />
            ) : (
              <button
                onClick={handleSend}
                disabled={loading || !inputVal.trim()}
                className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-fixed text-on-primary-fixed
                            flex items-center justify-center hover:scale-105 active:scale-95
                            transition-all disabled:opacity-40"
              >
                <span className="material-symbols-outlined text-sm">send</span>
              </button>
            )}
          </div>
        </div>

        {/* Mobile-only bottom nav */}
        <div className="md:hidden fixed bottom-0 left-0 right-0 z-50 flex justify-center pb-6
                         bg-neutral-950/20 backdrop-blur-xl rounded-t-[3rem] border-t border-zinc-800/10">
          <div className="flex items-center gap-12 py-4">
            <span className="material-symbols-outlined text-tertiary drop-shadow-[0_0_8px_rgba(255,221,121,0.5)]">
              keyboard_voice
            </span>
            <span className="material-symbols-outlined text-zinc-600 hover:text-zinc-300">graphic_eq</span>
            <span className="material-symbols-outlined text-zinc-600 hover:text-zinc-300">blur_on</span>
          </div>
        </div>
      </main>
    </div>
  )
}
