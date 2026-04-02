/**
 * Financial.jsx — V5.5 Polished Financial Survival
 * Rent gap hero, daily burn, runway, SVG expense chart, freelance hunter.
 */
import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useJARVIS } from '../hooks/useJARVIS.js'

const NAV = [
  { to: '/',          icon: 'home',           end: true  },
  { to: '/financial', icon: 'account_balance', end: false },
  { to: '/academic',  icon: 'school',          end: false },
  { to: '/system',    icon: 'settings',        end: false },
]

const LEADS = [
  { id: 1, match: '92% System Match', title: 'UI/UX Audit: NeoBank',       rate: '€75.00', hot: true  },
  { id: 2, match: '78% System Match', title: 'React Micro-component',       rate: '€40.00', hot: false },
]

export default function Financial() {
  const { state, connected, loading, sendInput, triggerWakeWord } = useJARVIS()
  const [inputVal, setInputVal] = useState('')

  const handleSend = () => {
    if (!inputVal.trim() || loading) return
    sendInput(inputVal.trim())
    setInputVal('')
  }

  const rentGap       = state.rent_gap ?? 110
  const dailyBurn     = state.daily_burn ?? 42.50
  const runway        = state.runway ?? 14
  const monthlyBudget = state.monthly_budget ?? 2000
  const monthlySpent  = state.monthly_spent ?? 960
  const progress      = Math.min(Math.round(((monthlyBudget - rentGap) / monthlyBudget) * 100), 100)

  return (
    <div className="bg-black min-h-screen text-on-surface selection:bg-tertiary/30 overflow-x-hidden">

      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <aside className="fixed left-0 top-0 h-full z-40 flex flex-col items-center py-8
                         bg-black/40 backdrop-blur-3xl w-20 border-r border-white/5">
        <div className="mb-12">
          <span className="material-symbols-outlined text-white text-3xl">blur_on</span>
        </div>
        <nav className="flex flex-col gap-12 flex-1 items-center">
          {NAV.map(({ to, icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                isActive
                  ? 'text-white scale-110 transition-all'
                  : 'text-zinc-500 hover:text-white transition-colors'
              }
            >
              <span className="material-symbols-outlined text-2xl">{icon}</span>
            </NavLink>
          ))}
        </nav>
        <div className="mt-auto">
          <div className="w-10 h-10 rounded-full border border-white/10 bg-zinc-800/60
                           flex items-center justify-center">
            <span className="text-zinc-400 text-sm font-bold">J</span>
          </div>
        </div>
      </aside>

      {/* ── Top Status Bar ───────────────────────────────────────────── */}
      <header className="fixed top-0 left-20 right-0 z-50 flex justify-center h-16 pointer-events-none">
        <div className="mt-4 glass-island rounded-full px-6 py-2 flex items-center gap-4 pointer-events-auto">
          <span className="material-symbols-outlined text-white text-xs animate-pulse">blur_on</span>
          <div className="overflow-hidden w-64">
            <p className="uppercase text-[9px] font-bold text-zinc-400 tracking-widest whitespace-nowrap marquee-text">
              SYSTEMS NOMINAL · MISSING TO RENT: €{rentGap} · FREELANCE PIPELINE: {LEADS.length} ACTIVE · BURN RATE: -12%
            </p>
          </div>
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-error'}`} />
        </div>
      </header>

      {/* ── Main ────────────────────────────────────────────────────── */}
      <main className="ml-20 pt-24 px-8 pb-36 max-w-[1440px] mx-auto">
        <div className="grid grid-cols-12 gap-4">

          {/* ── Primary Objective Hero ──────────────────────────────── */}
          <section className="col-span-12 lg:col-span-8">
            <div className="floating-card rounded-[2rem] p-6 flex flex-col justify-between
                             h-[420px] relative overflow-hidden">
              <div className="flex justify-between items-start z-10">
                <div>
                  <span className="uppercase text-[10px] text-zinc-500 font-bold tracking-widest">
                    Priority Objective
                  </span>
                  <h1 className="text-5xl font-black mt-2 tracking-tight text-white uppercase">
                    Missing to Rent
                  </h1>
                </div>
                <div className="text-right">
                  <span className={`font-bold text-7xl ${rentGap > 0 ? 'red-neon-glow text-error' : 'text-green-400'}`}>
                  €{rentGap.toFixed(2)}
                </span>
                  <p className="uppercase text-[10px] text-error/80 mt-2 font-bold tracking-widest">
                    Deficit Remaining
                  </p>
                </div>
              </div>

              <div className="z-10">
                <div className="flex justify-between items-end mb-4">
                  <div className="space-y-1">
                    <span className="uppercase text-[10px] text-zinc-500 font-bold tracking-widest">
                      Survival Progress
                    </span>
                    <div className="text-2xl font-bold text-white">
                      {progress}%{' '}
                      <span className="text-zinc-500 text-sm font-normal">SECURED</span>
                    </div>
                  </div>
                  <p className="text-sm text-zinc-400 max-w-xs leading-relaxed text-right">
                    Gap analyzed. High-probability freelance nodes identified. Deployment ready.
                  </p>
                </div>
                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-error rounded-full shadow-[0_0_15px_rgba(238,125,119,0.5)] transition-all duration-1000"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              <div className="absolute -right-20 -bottom-20 w-96 h-96 bg-error/5 blur-[120px]
                               rounded-full pointer-events-none" />
            </div>
          </section>

          {/* ── Burn Metrics ──────────────────────────────────────────── */}
          <section className="col-span-12 lg:col-span-4 flex flex-col gap-4">
            {/* Daily Burn */}
            <div className="floating-card rounded-[2rem] p-6 flex-1 flex flex-col justify-between">
              <div>
                <span className="uppercase text-[10px] text-zinc-500 font-bold tracking-widest">
                  Daily Burn Rate
                </span>
                <h3 className="text-5xl font-bold text-white mt-2 transition-all duration-500">€{dailyBurn.toFixed(2)}</h3>
              </div>
              <div className="flex items-center justify-between mt-4">
                <div className="flex items-center gap-2 px-3 py-1 bg-green-500/10
                                 border border-green-500/20 rounded-full">
                  <span className="material-symbols-outlined text-green-500 text-sm">trending_down</span>
                  <span className="text-green-500 text-[10px] font-bold uppercase tracking-widest">
                    12% Decrease
                  </span>
                </div>
                <div className="flex items-end gap-1.5 h-12">
                  {[50, 66, 33, 100].map((h, i) => (
                    <div
                      key={i}
                      className={`w-2.5 rounded-t-sm ${i === 3 ? 'bg-tertiary shadow-[0_0_10px_rgba(255,221,121,0.3)]' : 'bg-white/10'}`}
                      style={{ height: `${h}%` }}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Runway */}
            <div className="floating-card rounded-[2rem] p-6 flex-1 flex flex-col justify-between">
              <div>
                <span className="uppercase text-[10px] text-zinc-500 font-bold tracking-widest">
                  Runway Forecast
                </span>
                <h3 className="text-5xl font-bold text-white mt-2 transition-all duration-500">
                  {runway}{' '}
                  <span className="text-xl text-zinc-500">Days</span>
                </h3>
              </div>
              <div className="flex justify-end">
                <div className="w-12 h-12 glass-island rounded-2xl flex items-center justify-center">
                  <span className="material-symbols-outlined text-tertiary text-2xl">hourglass_empty</span>
                </div>
              </div>
            </div>
          </section>

          {/* ── Expense Flux Chart ────────────────────────────────────── */}
          <section className="col-span-12 lg:col-span-8">
            <div className="floating-card rounded-[2rem] p-6 h-full">
              <div className="flex justify-between items-center mb-10">
                <h2 className="uppercase text-xs font-black text-white tracking-widest">Expense Flux</h2>
                <div className="flex gap-6">
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-zinc-600" />
                    <span className="uppercase text-[9px] font-bold text-zinc-500 tracking-widest">Target</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-tertiary" />
                    <span className="uppercase text-[9px] font-bold text-tertiary tracking-widest">Actual</span>
                  </div>
                </div>
              </div>

              <div className="h-52 w-full px-2">
                <svg viewBox="0 0 1000 200" className="w-full h-full overflow-visible">
                  <line x1="0" x2="1000" y1="0"   y2="0"   stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                  <line x1="0" x2="1000" y1="100" y2="100" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                  <line x1="0" x2="1000" y1="200" y2="200" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                  <path
                    d="M0,120 L150,110 L300,130 L450,115 L600,125 L750,105 L900,110 L1000,100"
                    fill="none" stroke="rgba(255,255,255,0.1)" strokeDasharray="8,4" strokeWidth="1.5"
                  />
                  <path
                    d="M0,150 C100,145 200,140 300,120 C400,100 500,75 600,90 C700,105 850,50 1000,20"
                    fill="none" stroke="#ffdd79" strokeWidth="3" strokeLinecap="round"
                    className="drop-shadow-[0_0_8px_rgba(255,221,121,0.4)]"
                  />
                  <circle cx="600"  cy="90" r="5" fill="#000" stroke="#ffdd79" strokeWidth="2" />
                  <circle cx="1000" cy="20" r="5" fill="#000" stroke="#ffdd79" strokeWidth="2" />
                </svg>
                <div className="flex justify-between mt-6">
                  {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map(d => (
                    <span key={d} className="uppercase text-[9px] text-zinc-600 font-bold tracking-widest">{d}</span>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* ── Freelance Hunter ─────────────────────────────────────── */}
          <section className="col-span-12 lg:col-span-4">
            <div className="floating-card rounded-[2rem] p-6 h-full flex flex-col">
              <h2 className="uppercase text-xs font-black text-white tracking-widest mb-8">
                Freelance Hunter
              </h2>
              <div className="space-y-3 flex-1">
                {LEADS.map(lead => (
                  <div
                    key={lead.id}
                    className={`p-4 rounded-2xl border transition-all cursor-pointer hover:border-white/15
                                ${lead.hot ? 'bg-white/5 border-white/8' : 'bg-white/[0.03] border-white/5 opacity-60'}`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <span className={`uppercase text-[8px] font-bold tracking-widest ${
                          lead.hot ? 'text-tertiary' : 'text-zinc-500'
                        }`}>
                          {lead.match}
                        </span>
                        <h4 className="text-sm font-bold text-white mt-1">{lead.title}</h4>
                      </div>
                      <span className="text-sm font-mono text-white">{lead.rate}</span>
                    </div>
                  </div>
                ))}
              </div>
              <button
                onClick={() => sendInput('scan network leads')}
                className="w-full mt-8 py-4 rounded-xl glass-island hover:bg-white/10 transition-all
                            uppercase text-[10px] font-black text-white tracking-widest"
              >
                Scan Network Leads
              </button>
            </div>
          </section>
        </div>
      </main>

      {/* ── Bottom Dock ─────────────────────────────────────────────── */}
      <footer className="fixed bottom-0 left-20 right-0 z-50 flex justify-center pb-8 pointer-events-none">
        <div className="w-full max-w-2xl px-6 pointer-events-auto">
          <div className="glass-island rounded-3xl p-4 flex items-center gap-6
                           shadow-[0_32px_64px_rgba(0,0,0,0.8)]">
            <button
              onClick={() => triggerWakeWord()}
              className="w-14 h-14 rounded-2xl bg-white/10 flex items-center justify-center
                          text-tertiary hover:scale-105 active:scale-95 transition-transform flex-shrink-0"
            >
              <span className="material-symbols-outlined text-2xl drop-shadow-[0_0_8px_rgba(255,221,121,0.5)]">
                mic
              </span>
            </button>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${loading ? 'bg-tertiary animate-pulse' : 'bg-zinc-600'}`} />
                <span className="uppercase text-[9px] font-black text-zinc-500 tracking-widest">
                  {loading ? 'Processing...' : 'Aural Input Ready'}
                </span>
              </div>
              <input
                value={inputVal}
                onChange={e => setInputVal(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleSend() }}
                disabled={loading}
                placeholder="J.A.R.V.I.S., analizza le finanze..."
                className="w-full bg-transparent border-none focus:outline-none text-sm
                            text-zinc-200 placeholder:text-zinc-600 disabled:opacity-50"
              />
            </div>
            <div className="flex items-end gap-1 px-2 flex-shrink-0">
              {[3, 6, 8, 4].map((h, i) => (
                <div
                  key={i}
                  className={`w-1 rounded-full ${i === 2 ? 'bg-tertiary animate-pulse' : 'bg-tertiary/30'}`}
                  style={{ height: `${h * 3}px` }}
                />
              ))}
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
