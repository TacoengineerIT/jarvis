/**
 * Intelligence.jsx — V5.5 Polished Dashboard
 * Mercury orb, hero financial stats, status cards, bottom transcription dock.
 */
import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useJARVIS, getStateLabel } from '../hooks/useJARVIS.js'

const NAV = [
  { to: '/',          icon: 'home',           end: true  },
  { to: '/financial', icon: 'account_balance', end: false },
  { to: '/academic',  icon: 'school',          end: false },
  { to: '/system',    icon: 'terminal',        end: false },
]

export default function Intelligence() {
  const { state, connected, loading, sendInput, triggerWakeWord } = useJARVIS()
  const [inputVal, setInputVal] = useState('')

  const handleSend = () => {
    if (!inputVal.trim() || loading) return
    sendInput(inputVal.trim())
    setInputVal('')
  }

  const lastCmd = state.last_5_commands[state.last_5_commands.length - 1]

  return (
    <div className="h-screen w-screen liquid-mesh selection:bg-tertiary overflow-hidden">

      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <nav className="fixed left-0 top-0 h-screen w-20 flex flex-col items-center py-4 z-50
                      border-r border-white/5 bg-black/40 backdrop-blur-3xl">
        <div className="mb-8 p-4">
          <div className="w-10 h-10 rounded-full border border-white/10 bg-zinc-800/60
                           flex items-center justify-center">
            <span className="text-zinc-300 text-sm font-bold tracking-widest">J</span>
          </div>
        </div>

        <div className="flex flex-col gap-4 items-center flex-1 w-full px-3">
          {NAV.map(({ to, icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                isActive
                  ? 'glass-island w-full aspect-square flex items-center justify-center text-white rounded-lg'
                  : 'w-full aspect-square flex items-center justify-center text-zinc-500 hover:text-zinc-300 transition-colors'
              }
            >
              <span className="material-symbols-outlined text-xl">{icon}</span>
            </NavLink>
          ))}
        </div>

        <div className="mt-auto p-4">
          <span className="material-symbols-outlined text-zinc-500 hover:text-zinc-300 cursor-pointer text-xl">
            settings
          </span>
        </div>
      </nav>

      {/* ── Top Island ──────────────────────────────────────────────── */}
      <header className="fixed top-0 left-0 right-0 z-50 flex justify-center pointer-events-none">
        <div className="mt-4 glass-island rounded-full px-4 py-2 flex items-center gap-3
                         pointer-events-auto">
          <span className="material-symbols-outlined text-white text-base">bubble_chart</span>
          <p className="uppercase text-[10px] font-medium tracking-widest text-zinc-300 whitespace-nowrap">
            {state.briefing || 'SYSTEM NOMINAL · PORTFOLIO ACTIVE'}
          </p>
          <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
            connected ? 'bg-tertiary animate-pulse shadow-[0_0_6px_#ffdd79]' : 'bg-error'
          }`} />
        </div>
      </header>

      {/* ── Main Canvas ─────────────────────────────────────────────── */}
      <main className="ml-20 h-screen relative flex flex-col items-center justify-center p-4 overflow-hidden">

        {/* Hero Financial Stats */}
        <div className="absolute top-24 w-full max-w-xl flex justify-between px-8 z-20">
          <div>
            <p className="uppercase text-[10px] text-zinc-500 tracking-widest mb-1">Portfolio Balance</p>
            <h2 className="text-4xl font-bold text-white tracking-tight neon-shadow">
              €{(2000 - state.today_spent).toFixed(2)}
            </h2>
          </div>
          <div className="text-right">
            <p className="uppercase text-[10px] text-zinc-500 tracking-widest mb-1">Rent Gap</p>
            <h2 className="text-2xl font-bold text-tertiary tracking-tight neon-shadow">€110</h2>
          </div>
        </div>

        {/* Central Mercury Orb */}
        <div className="relative z-10 flex flex-col items-center">
          <div className="mercury-orb w-56 h-56 rounded-full mb-8 relative">
            <div className="absolute inset-0 rounded-full border border-white/20 scale-95" />
            <div className="absolute inset-0 rounded-full bg-white/5 blur-xl" />
          </div>
          <div className="text-center">
            <h1 className="text-4xl font-black uppercase tracking-widest text-white mb-1">
              {connected ? 'V5.5 ACTIVE' : 'OFFLINE'}
            </h1>
            <p className="text-zinc-500 uppercase text-[10px] tracking-widest">
              {getStateLabel(state.jarvis_state)}
            </p>
          </div>
        </div>

        {/* Status Cards */}
        <div className="absolute bottom-32 w-full max-w-4xl flex justify-between px-8">
          <div className="glass-island p-4 rounded-xl w-64">
            <div className="flex items-center gap-3 mb-4">
              <span className="material-symbols-outlined text-tertiary">bolt</span>
              <p className="uppercase text-[10px] text-zinc-400 tracking-widest">Engine Health</p>
            </div>
            <div className="flex items-end justify-between">
              <span className="text-xl font-bold text-white uppercase tracking-wider">
                {connected ? 'Optimal' : 'Offline'}
              </span>
              <span className="text-[9px] text-zinc-500 font-mono">{connected ? '99.8%' : '0%'}</span>
            </div>
            <div className="mt-4 h-0.5 w-full bg-white/5 rounded-full overflow-hidden">
              <div className={`h-full bg-white/40 transition-all duration-700 ${connected ? 'w-[99%]' : 'w-0'}`} />
            </div>
          </div>

          <div className="glass-island p-4 rounded-xl w-64">
            <div className="flex items-center gap-3 mb-4">
              <span className="material-symbols-outlined text-white">terminal</span>
              <p className="uppercase text-[10px] text-zinc-400 tracking-widest">Last Command</p>
            </div>
            <div className="bg-black/40 rounded-lg p-2 border border-white/5">
              <p className="text-[10px] font-mono text-zinc-400 truncate">
                {lastCmd?.user || 'exec: sync.io --force'}
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Transcription Dock */}
        <div className="fixed bottom-0 left-20 right-0 z-50 flex justify-center pb-8">
          <div className="max-w-lg w-full glass-island rounded-full px-6 py-4 flex items-center gap-4">
            <button
              onClick={() => triggerWakeWord()}
              className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center
                          text-tertiary active:scale-90 transition-transform flex-shrink-0"
            >
              <span className="material-symbols-outlined drop-shadow-[0_0_8px_rgba(255,221,121,0.5)]">
                keyboard_voice
              </span>
            </button>

            <input
              value={inputVal}
              onChange={e => setInputVal(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleSend() }}
              disabled={loading}
              placeholder="Instruct J.A.R.V.I.S. ..."
              className="flex-1 bg-transparent border-none focus:outline-none text-sm
                          text-white placeholder:text-zinc-600 disabled:opacity-50"
            />

            <div className="flex gap-1.5 h-4 items-end flex-shrink-0">
              <div className="w-0.5 h-2 bg-white/20 rounded-full" />
              <div className={`w-0.5 h-4 rounded-full transition-all ${
                loading ? 'bg-tertiary animate-pulse' : 'bg-white/60'
              }`} />
              <div className="w-0.5 h-3 bg-white/40 rounded-full" />
            </div>

            <button
              onClick={handleSend}
              disabled={loading || !inputVal.trim()}
              className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center
                          text-white hover:bg-white/20 disabled:opacity-30 transition-all flex-shrink-0"
            >
              <span className="material-symbols-outlined text-sm">send</span>
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
