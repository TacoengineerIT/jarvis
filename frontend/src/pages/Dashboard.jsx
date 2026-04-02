/**
 * Dashboard.jsx — Bento-grid dashboard (J.A.R.V.I.S. V5.5 Dashboard design)
 * Shows: Asset Overview, Academic Progress, System Health, Priority Event, orb + voice.
 */
import { useState } from 'react'
import { useJARVIS, getMoodEmoji, getMoodColor } from '../hooks/useJARVIS.js'
import MercuryOrb from '../components/MercuryOrb.jsx'
import WaveformAnimation from '../components/WaveformAnimation.jsx'

function BentoCard({ children, className = '', colSpan = 1 }) {
  return (
    <div className={`glass-island rounded-[32px] border border-white/5 p-6
                     hover:bg-black/60 transition-all duration-500 hover:scale-[1.02]
                     col-span-${colSpan} ${className}`}>
      {children}
    </div>
  )
}

function MiniBar({ value = 0, max = 100, color = 'bg-primary', glow = '' }) {
  return (
    <div className="w-full bg-surface-variant h-0.5 rounded-full overflow-hidden">
      <div
        className={`h-full ${color} ${glow} transition-all duration-700`}
        style={{ width: `${Math.min((value / max) * 100, 100)}%` }}
      />
    </div>
  )
}

export default function Dashboard() {
  const { state, connected, loading, sendInput } = useJARVIS()
  const [inputVal, setInputVal] = useState('')

  const handleSend = () => {
    if (!inputVal.trim() || loading) return
    sendInput(inputVal.trim())
    setInputVal('')
  }

  // Financial computations
  const monthlyBudget = 2000
  const totalSpent = state.last_5_commands.reduce
    ? 0 : 0  // Will come from state when finance API populates it
  const budgetPct = Math.min((state.today_spent / (monthlyBudget / 30)) * 100, 100)
  const moodPct = (state.mood_score / 10) * 100

  return (
    <div className="flex h-screen w-full bg-surface-container-lowest overflow-hidden">
      {/* ── Background ambient ─────────────────────────────────────── */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-1/4 -left-1/4 w-[50%] h-[50%] bg-primary/5 blur-[120px] rounded-full" />
        <div className="absolute bottom-1/4 -right-1/4 w-[40%] h-[40%] bg-tertiary/5 blur-[120px] rounded-full" />
      </div>

      {/* ── Main canvas ────────────────────────────────────────────── */}
      <main className="flex-1 ml-16 relative flex items-center justify-center overflow-hidden p-8 lg:p-12">

        {/* Intelligence Hub grid */}
        <div className="w-full max-w-7xl grid grid-cols-12 gap-8 items-center z-10">

          {/* Left: Orb + headline */}
          <div className="col-span-12 lg:col-span-7 flex flex-col items-center lg:items-start space-y-10">
            <div className="relative group">
              {/* Voice reactive glow */}
              <div className="absolute inset-0 bg-tertiary/10 rounded-full blur-[100px] -z-10
                              animate-pulse" />
              <MercuryOrb jarvisState={state.jarvis_state} size="lg" />
            </div>

            <div className="space-y-4 text-center lg:text-left max-w-xl">
              <h1 className="text-4xl lg:text-6xl font-black tracking-tighter text-primary-fixed leading-tight">
                {['RECORDING','ACTIVE'].includes(state.jarvis_state)
                  ? <>Recording <span className="text-tertiary">...</span></>
                  : state.jarvis_state === 'PROCESSING'
                  ? <>Processing <span className="text-tertiary">...</span></>
                  : state.jarvis_state === 'SPEAKING'
                  ? <>Responding <span className="text-tertiary">...</span></>
                  : <>Listening for <span className="text-tertiary">"Jarvis"</span></>
                }
              </h1>

              {state.response && (
                <p className="text-on-surface-variant font-body text-base leading-relaxed max-w-md
                               border-l-2 border-tertiary/40 pl-4 italic">
                  {state.response}
                </p>
              )}
              {!state.response && (
                <p className="text-on-surface-variant font-body text-base leading-relaxed max-w-md">
                  Neural link established. Workspace synchronised across all active nodes.
                </p>
              )}
            </div>
          </div>

          {/* Right: Bento cards */}
          <div className="col-span-12 lg:col-span-5 grid grid-cols-2 gap-4">

            {/* Financial overview — full width */}
            <BentoCard colSpan={2}>
              <div className="flex justify-between items-start mb-6">
                <div className="flex flex-col gap-1">
                  <span className="text-[10px] uppercase tracking-[0.2em] text-on-surface-variant">
                    Budget Overview
                  </span>
                  <h3 className="text-2xl font-bold text-primary-fixed">
                    €{state.today_spent.toFixed(2)}
                    <span className="text-sm font-normal text-on-surface-variant ml-2">today</span>
                  </h3>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <span className="material-symbols-outlined text-tertiary">trending_up</span>
                  {state.budget_alerts.length > 0 && (
                    <span className="text-[9px] text-error font-mono">
                      {state.budget_alerts.length} ALERT{state.budget_alerts.length > 1 ? 'S' : ''}
                    </span>
                  )}
                </div>
              </div>
              <MiniBar
                value={budgetPct}
                max={100}
                color={budgetPct > 80 ? 'bg-error' : 'bg-primary'}
                glow={budgetPct > 80
                  ? 'shadow-[0_0_12px_rgba(238,125,119,0.5)]'
                  : 'shadow-[0_0_12px_rgba(255,221,121,0.4)]'}
              />
              <div className="flex justify-between text-[10px] text-on-surface-variant
                               uppercase tracking-widest mt-1.5">
                <span>Daily burn</span>
                <span>{budgetPct.toFixed(0)}% of daily limit</span>
              </div>
              {state.budget_alerts[0] && (
                <p className="mt-3 text-[10px] text-error bg-error/10 px-3 py-1 rounded-lg
                               border border-error/20">
                  ⚠ {state.budget_alerts[0].message}
                </p>
              )}
            </BentoCard>

            {/* Mood card */}
            <BentoCard>
              <span className="material-symbols-outlined text-primary-fixed mb-3 block">
                sentiment_satisfied
              </span>
              <h4 className="text-xs uppercase tracking-widest text-on-surface-variant mb-1">
                Mood
              </h4>
              <p className={`text-xl font-bold ${getMoodColor(state.mood)}`}>
                {getMoodEmoji(state.mood)} {state.mood}
              </p>
              <MiniBar
                value={state.mood_score}
                max={10}
                color="bg-primary"
                glow="shadow-[0_0_8px_rgba(198,198,200,0.4)]"
              />
              <p className="text-[10px] text-on-surface-variant mt-2 leading-tight">
                Trend: {state.mood_trend} · Score {state.mood_score.toFixed(1)}/10
              </p>
            </BentoCard>

            {/* System health card */}
            <BentoCard>
              <span className="material-symbols-outlined text-tertiary mb-3 block">bolt</span>
              <h4 className="text-xs uppercase tracking-widest text-on-surface-variant mb-1">
                System
              </h4>
              <p className="text-xl font-bold text-primary-fixed">
                {connected ? 'Online' : 'Offline'}
              </p>
              <p className="text-[10px] text-on-surface-variant mt-2 leading-tight">
                {state.last_5_commands.length} commands · WS{' '}
                {connected
                  ? <span className="text-tertiary">connected</span>
                  : <span className="text-error">disconnected</span>
                }
              </p>
            </BentoCard>

            {/* Next event — full width */}
            <BentoCard colSpan={2} className="flex items-center gap-5">
              <div className="w-14 h-14 rounded-2xl bg-surface-container flex-shrink-0
                               flex items-center justify-center border border-outline-variant/20">
                <span className="material-symbols-outlined text-tertiary">event</span>
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="text-xs uppercase tracking-widest text-tertiary mb-1">
                  Next Event
                </h4>
                {state.next_event ? (
                  <>
                    <p className="text-sm text-primary-fixed font-medium truncate">
                      {state.next_event.title}
                    </p>
                    <p className="text-[10px] text-on-surface-variant mt-0.5">
                      {state.next_event.start_time?.slice(11, 16) || '—'}
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-sm text-primary-fixed font-medium">No events scheduled</p>
                    <p className="text-[10px] text-on-surface-variant mt-0.5">
                      Calendar data loading...
                    </p>
                  </>
                )}
              </div>
            </BentoCard>
          </div>
        </div>

        {/* Transcription above footer */}
        {state.user_input && (
          <div className="absolute bottom-28 left-1/2 -translate-x-1/2 text-center max-w-xl w-full px-4">
            <p className="text-sm font-light tracking-[0.1em] text-primary-dim/60 italic truncate">
              "{state.user_input}"
            </p>
          </div>
        )}
      </main>

      {/* ── Bottom Dock ────────────────────────────────────────────── */}
      <footer className="fixed bottom-0 left-16 right-0 z-50 flex flex-col items-center pb-4">
        <div className="max-w-xl w-full px-6">
          <div className="glass-island rounded-[40px] border border-[#484848]/20 shadow-2xl
                           flex items-center gap-4 bg-black/60 mb-3">
            <div className="flex items-center gap-2 pl-4">
              <button className="w-10 h-10 rounded-full flex items-center justify-center
                                  text-primary-fixed hover:bg-white/10 transition-all">
                <span className="material-symbols-outlined">add</span>
              </button>
              <div className="h-6 w-px bg-outline-variant/30" />
            </div>
            <input
              value={inputVal}
              onChange={e => setInputVal(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleSend() }}
              placeholder='Instruct J.A.R.V.I.S. or dictate notes...'
              disabled={loading}
              className="flex-1 bg-transparent border-none focus:outline-none focus:ring-0
                          text-sm text-on-surface placeholder:text-on-surface-variant py-4
                          disabled:opacity-50"
            />
            <div className="flex items-center gap-4 pr-4">
              {['RECORDING','SPEAKING'].includes(state.jarvis_state) && (
                <WaveformAnimation active />
              )}
              <button
                onClick={handleSend}
                disabled={loading || !inputVal.trim()}
                className="w-12 h-12 rounded-full bg-primary-fixed text-on-primary-fixed
                            flex items-center justify-center
                            shadow-[0_0_20px_rgba(198,198,200,0.3)]
                            hover:scale-105 active:scale-95 transition-all
                            disabled:opacity-40"
              >
                {loading
                  ? <span className="material-symbols-outlined text-base animate-spin">progress_activity</span>
                  : <span className="material-symbols-outlined icon-filled text-base">mic</span>
                }
              </button>
            </div>
          </div>

          {/* Bottom icon row */}
          <div className="flex justify-center gap-20">
            <button className="text-on-surface-variant hover:text-primary-fixed transition-colors p-2">
              <span className="material-symbols-outlined">mic_none</span>
            </button>
            <button className="text-on-surface-variant hover:text-primary-fixed transition-colors p-2">
              <span className="material-symbols-outlined">keyboard</span>
            </button>
          </div>
        </div>
      </footer>
    </div>
  )
}
