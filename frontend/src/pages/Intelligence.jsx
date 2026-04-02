/**
 * Intelligence.jsx — Main orb page (J.A.R.V.I.S. V5.0 "Liquid Intelligence" design)
 * Mobile-responsive. Shows: briefing pill, central orb, memory island, finance island,
 * live transcription, bottom nav with text input.
 */
import { useState } from 'react'
import { useJARVIS, getMoodEmoji, getMoodColor, getStateLabel } from '../hooks/useJARVIS.js'
import MercuryOrb from '../components/MercuryOrb.jsx'
import WaveformAnimation from '../components/WaveformAnimation.jsx'

export default function Intelligence() {
  const { state, connected, loading, error, sendInput } = useJARVIS()
  const [inputVal, setInputVal] = useState('')

  const handleSend = () => {
    if (!inputVal.trim() || loading) return
    sendInput(inputVal.trim())
    setInputVal('')
  }

  const todayBudget = 15
  const pct = Math.min((state.today_spent / todayBudget) * 100, 100)

  return (
    <div className="fixed inset-0 flex flex-col items-center bg-surface-container-lowest overflow-hidden">
      {/* Background ambient blobs */}
      <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] rounded-full bg-primary/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-5%] w-[40%] h-[40%] rounded-full bg-tertiary/5 blur-[100px] pointer-events-none" />

      {/* ── Top Nav ─────────────────────────────────────────────── */}
      <header className="w-full max-w-md px-4 mt-4">
        <div className="flex items-center justify-between px-5 h-14 rounded-full
                        border border-[#484848]/15 bg-black/40 backdrop-blur-3xl
                        shadow-[0_32px_32px_rgba(198,198,200,0.06)]">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-[#c6c6c8]">bubble_chart</span>
            <span className="text-[#e2e2e4] font-bold tracking-widest uppercase text-sm">
              J.A.R.V.I.S. V4.0
            </span>
          </div>
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-tertiary shadow-[0_0_8px_#ffdd79]' : 'bg-error'}`} />
        </div>
      </header>

      {/* ── Briefing Ticker ──────────────────────────────────────── */}
      <div className="w-full max-w-lg px-4 mt-3">
        <div className="liquid-glass rounded-full px-5 py-2 flex items-center justify-between
                        border border-outline-variant/10">
          <div className="flex items-center gap-4 overflow-hidden flex-1">
            <div className="flex items-center gap-2 flex-shrink-0">
              <div className="w-2 h-2 rounded-full bg-tertiary shadow-[0_0_8px_#ffdd79]" />
              <span className="text-[10px] font-bold tracking-[0.2em] uppercase text-on-surface-variant">
                Live
              </span>
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-medium tracking-wide text-primary-fixed whitespace-nowrap
                            marquee-text">
                {state.briefing}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 pl-4 border-l border-outline-variant/20">
            <span className="material-symbols-outlined text-xs text-on-surface-variant">dns</span>
            <span className={`text-[10px] font-mono ${connected ? 'text-tertiary' : 'text-error'}`}>
              {connected ? 'STABLE' : 'OFFLINE'}
            </span>
          </div>
        </div>
      </div>

      {/* ── Error banner ─────────────────────────────────────────── */}
      {error && (
        <div className="w-full max-w-lg px-4 mt-2">
          <div className="flex items-center gap-2 px-4 py-2 rounded-full bg-error/10 border border-error/20">
            <span className="material-symbols-outlined text-error text-sm">warning</span>
            <span className="text-xs text-error">{error}</span>
          </div>
        </div>
      )}

      {/* ── Main Canvas ──────────────────────────────────────────── */}
      <main className="flex-1 relative w-full flex items-center justify-center">

        {/* Left Island: Contextual Memory */}
        <div className="absolute left-6 top-1/2 -translate-y-1/2 hidden lg:flex flex-col w-56">
          <div className="liquid-glass p-5 rounded-[2.5rem] border border-outline-variant/5
                          hover:scale-[1.02] transition-all duration-700">
            <span className="text-[10px] uppercase tracking-[0.3em] text-on-surface-variant mb-4 block">
              Contextual Memory
            </span>
            <div className="space-y-4">
              {state.last_5_commands.slice(-2).reverse().map((cmd, i) => (
                <div key={i} className="group">
                  <p className="text-[10px] text-secondary mb-1">
                    {i === 0 ? 'Last command' : 'Previous'}
                  </p>
                  <p className="text-sm font-medium tracking-tight text-primary-fixed
                                group-hover:text-tertiary transition-colors line-clamp-1">
                    {cmd.input}
                  </p>
                </div>
              ))}
              {state.last_5_commands.length === 0 && (
                <p className="text-[11px] text-on-surface-variant/50 italic">
                  No commands yet...
                </p>
              )}
            </div>
            <div className="mt-5 pt-4 border-t border-outline-variant/10">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-on-surface-variant">Mood</span>
                <span className={`text-[11px] font-mono ${getMoodColor(state.mood)}`}>
                  {getMoodEmoji(state.mood)} {state.mood}
                </span>
              </div>
              <div className="mt-2">
                <div className="flex justify-between mb-1">
                  <span className="text-[10px] text-on-surface-variant">Mood Score</span>
                  <span className="text-[10px] font-mono text-primary">{state.mood_score.toFixed(1)}/10</span>
                </div>
                <div className="h-0.5 w-full bg-surface-variant rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary shadow-[0_0_8px_rgba(198,198,200,0.5)] transition-all duration-700"
                    style={{ width: `${(state.mood_score / 10) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Central Orb */}
        <div className="flex flex-col items-center">
          <MercuryOrb jarvisState={state.jarvis_state} size="lg" />
        </div>

        {/* Right Island: Financial Watchdog */}
        <div className="absolute right-6 top-1/2 -translate-y-1/2 hidden lg:flex flex-col w-56">
          <div className="liquid-glass p-5 rounded-[2.5rem] border border-outline-variant/5
                          hover:scale-[1.02] transition-all duration-700">
            <div className="flex justify-between items-start mb-5">
              <span className="text-[10px] uppercase tracking-[0.3em] text-on-surface-variant">
                Watchdog
              </span>
              <span className="material-symbols-outlined text-sm text-tertiary">
                account_balance_wallet
              </span>
            </div>
            <div className="mb-4">
              <span className="text-3xl font-light tracking-tighter text-primary-fixed">
                €{state.today_spent.toFixed(2)}
              </span>
              {state.budget_alerts.length > 0 && (
                <span className="text-[10px] text-error ml-2 font-mono">⚠ ALERT</span>
              )}
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-[10px] font-mono text-on-surface-variant">
                <span>Daily Spend</span>
                <span>€{todayBudget.toFixed(2)} limit</span>
              </div>
              <div className="h-0.5 w-full bg-surface-variant rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-700 ${
                    pct > 90 ? 'bg-error shadow-[0_0_8px_rgba(238,125,119,0.4)]'
                    : pct > 70 ? 'bg-tertiary shadow-[0_0_8px_rgba(255,221,121,0.4)]'
                    : 'bg-primary shadow-[0_0_8px_rgba(198,198,200,0.4)]'
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
            {/* Budget alerts */}
            {state.budget_alerts.slice(0, 2).map((a, i) => (
              <div key={i} className="mt-3 px-2 py-1 rounded-lg bg-error/10 border border-error/20">
                <p className="text-[9px] text-error">{a.message}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Live transcription area */}
        <div className="absolute bottom-20 left-1/2 -translate-x-1/2 w-full max-w-xl px-6 text-center">
          {state.user_input && (
            <p className="text-sm tracking-wide text-on-surface-variant opacity-50 italic mb-1 line-clamp-1">
              "{state.user_input}"
            </p>
          )}
          {state.response && (
            <p className="text-base font-medium tracking-tight text-primary-fixed line-clamp-2">
              {state.response}
            </p>
          )}
        </div>
      </main>

      {/* ── Bottom Nav / Input Dock ──────────────────────────────── */}
      <footer className="w-full max-w-lg px-4 pb-6 pt-2">
        {/* Text input row */}
        <div className="liquid-glass rounded-full border border-[#484848]/20 flex items-center gap-3 px-4 py-2 mb-3">
          <input
            value={inputVal}
            onChange={e => setInputVal(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') handleSend() }}
            placeholder="Scrivi a JARVIS..."
            disabled={loading}
            className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0
                       text-sm text-on-surface placeholder:text-on-surface-variant/50
                       disabled:opacity-50"
          />
          {['RECORDING','SPEAKING'].includes(state.jarvis_state) && (
            <WaveformAnimation active />
          )}
          <button
            onClick={handleSend}
            disabled={loading || !inputVal.trim()}
            className="w-8 h-8 rounded-full bg-primary-fixed text-on-primary-fixed
                       flex items-center justify-center text-sm
                       hover:scale-105 active:scale-95 transition-all
                       disabled:opacity-40"
          >
            <span className="material-symbols-outlined text-sm">send</span>
          </button>
        </div>

        {/* Icon row */}
        <nav className="flex justify-around items-center px-4">
          <button className="text-on-surface-variant p-3 hover:text-primary-fixed transition-all">
            <span className="material-symbols-outlined">mic_none</span>
          </button>
          <button className="bg-[#c6c6c8] text-black rounded-full p-3
                             shadow-[0_0_15px_rgba(255,221,121,0.4)]">
            <span className="material-symbols-outlined icon-filled">memory</span>
          </button>
          <button className="text-on-surface-variant p-3 hover:text-primary-fixed transition-all">
            <span className="material-symbols-outlined">account_balance_wallet</span>
          </button>
          <button className="text-on-surface-variant p-3 hover:text-primary-fixed transition-all">
            <span className="material-symbols-outlined">settings</span>
          </button>
        </nav>
      </footer>
    </div>
  )
}
