/**
 * Financial.jsx — V5.5 Financial Survival Command Center
 * Rent gap hero, daily burn, runway, expense chart, freelance hunter leads.
 */
import { useState } from 'react'
import { useJARVIS } from '../hooks/useJARVIS.js'
import WaveformAnimation from '../components/WaveformAnimation.jsx'

const MONTHS = ['Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb']
const EXPENSES = [780, 920, 850, 1100, 960, 1040]
const MAX_EXP = Math.max(...EXPENSES)

const LEADS = [
  { id: 1, title: 'React Dev — Startup Bari',   rate: '€30/h',  match: 92, tag: 'Remote',  hot: true  },
  { id: 2, title: 'Node.js API — Freelancer.it', rate: '€25/h',  match: 87, tag: 'Contract', hot: false },
  { id: 3, title: 'UI/UX Figma — Design Agency', rate: '€400 fix', match: 75, tag: 'Fixed',  hot: false },
  { id: 4, title: 'Python Script — DataLab',     rate: '€200 fix', match: 70, tag: 'Fixed',  hot: false },
]

export default function Financial() {
  const { state, loading, sendInput } = useJARVIS()
  const [inputVal, setInputVal] = useState('')
  const [activePeriod, setActivePeriod] = useState('6M')

  const handleSend = () => {
    if (!inputVal.trim() || loading) return
    sendInput(inputVal.trim())
    setInputVal('')
  }

  const rentGap    = 110
  const dailyBurn  = 42.50
  const runway     = 14
  const monthlyBudget = 2000
  const spent      = 960
  const remaining  = monthlyBudget - spent
  const spentPct   = Math.round((spent / monthlyBudget) * 100)

  return (
    <div className="bg-black min-h-screen text-white pl-16 pb-32 overflow-x-hidden">

      {/* ── Header ─────────────────────────────────────────────────── */}
      <div className="px-10 pt-10 pb-6">
        <h1 className="text-3xl font-black tracking-tight text-white mb-1">Financial Survival</h1>
        <p className="text-zinc-500 text-sm tracking-wide">Bari Operations · April 2026</p>
      </div>

      {/* ── Hero: Rent Gap ─────────────────────────────────────────── */}
      <div className="mx-8 mb-6 apple-glass rounded-[32px] border border-white/8 p-8
                      relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-tertiary/5 blur-[80px] rounded-full pointer-events-none" />
        <div className="relative z-10 grid grid-cols-3 gap-8 items-center">
          <div>
            <p className="text-[10px] uppercase tracking-widest text-zinc-500 mb-2">Rent Gap</p>
            <div className="flex items-baseline gap-2">
              <span className="text-5xl font-black text-tertiary">€{rentGap}</span>
              <span className="text-zinc-500 text-sm">/ needed</span>
            </div>
            <p className="text-xs text-zinc-600 mt-2">Due in {runway} days · Urgente</p>
          </div>

          <div className="border-l border-white/5 pl-8">
            <p className="text-[10px] uppercase tracking-widest text-zinc-500 mb-2">Daily Burn</p>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-white">€{dailyBurn.toFixed(2)}</span>
            </div>
            <div className="mt-3 w-full bg-zinc-800 h-0.5 rounded-full overflow-hidden">
              <div className="h-full bg-primary w-[68%] rounded-full shadow-[0_0_8px_#c6c6c8]" />
            </div>
            <p className="text-[10px] text-zinc-600 mt-1">68% of €62.50 target</p>
          </div>

          <div className="border-l border-white/5 pl-8">
            <p className="text-[10px] uppercase tracking-widest text-zinc-500 mb-2">Runway</p>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-white">{runway}</span>
              <span className="text-zinc-500 text-sm">days</span>
            </div>
            <div className="mt-3 flex gap-1">
              {Array.from({ length: 20 }).map((_, i) => (
                <div
                  key={i}
                  className={`flex-1 h-2 rounded-sm ${i < runway ? 'bg-tertiary/70' : 'bg-zinc-800'}`}
                />
              ))}
            </div>
            <p className="text-[10px] text-zinc-600 mt-1">
              {runway > 10 ? 'Stable' : 'Warning'} · Needs €{rentGap} injection
            </p>
          </div>
        </div>
      </div>

      {/* ── Main Grid ─────────────────────────────────────────────── */}
      <div className="grid grid-cols-12 gap-6 px-8">

        {/* ── Left: Monthly Budget + Expense Chart ───────────────── */}
        <div className="col-span-12 lg:col-span-7 space-y-6">

          {/* Budget progress */}
          <div className="apple-glass rounded-[28px] border border-white/8 p-6">
            <div className="flex justify-between items-start mb-5">
              <div>
                <p className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1">Monthly Budget</p>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-bold text-white">€{spent}</span>
                  <span className="text-zinc-500 text-sm">/ €{monthlyBudget}</span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-[10px] uppercase tracking-widest text-zinc-500 mb-1">Remaining</p>
                <span className={`text-lg font-bold ${remaining < 200 ? 'text-error' : 'text-tertiary'}`}>
                  €{remaining}
                </span>
              </div>
            </div>
            <div className="w-full bg-zinc-800 rounded-full h-2 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  spentPct > 85 ? 'bg-error' : spentPct > 65 ? 'bg-tertiary' : 'bg-primary'
                }`}
                style={{ width: `${spentPct}%` }}
              />
            </div>
            <div className="flex justify-between text-[9px] text-zinc-600 uppercase tracking-widest mt-1.5">
              <span>{spentPct}% consumed</span>
              <span>€{(dailyBurn * runway).toFixed(0)} projected to end</span>
            </div>
          </div>

          {/* Expense SVG chart */}
          <div className="apple-glass rounded-[28px] border border-white/8 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-sm font-bold text-white">Expense Trend</h3>
              <div className="flex gap-2">
                {['3M','6M','1Y'].map(p => (
                  <button
                    key={p}
                    onClick={() => setActivePeriod(p)}
                    className={`text-[9px] uppercase tracking-widest px-3 py-1 rounded-full transition-all ${
                      activePeriod === p
                        ? 'bg-white/10 text-white'
                        : 'text-zinc-600 hover:text-zinc-400'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>

            {/* SVG Bar Chart */}
            <div className="h-36 flex items-end gap-3">
              {MONTHS.map((month, i) => {
                const pct = (EXPENSES[i] / MAX_EXP) * 100
                const isLatest = i === MONTHS.length - 1
                return (
                  <div key={month} className="flex-1 flex flex-col items-center gap-1">
                    <span className="text-[9px] text-zinc-500">{isLatest ? `€${EXPENSES[i]}` : ''}</span>
                    <div className="w-full rounded-t-lg relative overflow-hidden"
                         style={{ height: `${pct}%`, minHeight: '8px' }}>
                      <div
                        className={`w-full h-full rounded-t-lg transition-all duration-700 ${
                          isLatest
                            ? 'bg-tertiary shadow-[0_0_12px_rgba(255,221,121,0.3)]'
                            : 'bg-zinc-700'
                        }`}
                      />
                    </div>
                    <span className="text-[8px] text-zinc-600 uppercase">{month}</span>
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* ── Right: Expense breakdown + Freelance leads ─────────── */}
        <div className="col-span-12 lg:col-span-5 space-y-6">

          {/* Expense breakdown */}
          <div className="apple-glass rounded-[28px] border border-white/8 p-6">
            <h3 className="text-sm font-bold text-white mb-5">Breakdown</h3>
            <div className="space-y-4">
              {[
                { label: 'Rent',       amount: 400, color: 'bg-primary',   pct: 42 },
                { label: 'Food',       amount: 280, color: 'bg-secondary',  pct: 29 },
                { label: 'Transport',  amount: 120, color: 'bg-tertiary',   pct: 12 },
                { label: 'Tech/Tools', amount: 100, color: 'bg-zinc-500',   pct: 10 },
                { label: 'Other',      amount:  60, color: 'bg-zinc-700',   pct:  7 },
              ].map(({ label, amount, color, pct }) => (
                <div key={label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-zinc-400">{label}</span>
                    <span className="text-white font-mono">€{amount}</span>
                  </div>
                  <div className="w-full bg-zinc-800 rounded-full h-0.5 overflow-hidden">
                    <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Freelance Hunter */}
          <div className="apple-glass rounded-[28px] border border-white/8 p-6">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-sm font-bold text-white">Freelance Hunter</h3>
              <span className="text-[9px] text-tertiary bg-tertiary/10 px-2 py-0.5 rounded-full
                                border border-tertiary/20 uppercase tracking-widest">
                {LEADS.length} leads
              </span>
            </div>
            <div className="space-y-3">
              {LEADS.map(lead => (
                <div
                  key={lead.id}
                  className={`flex items-center gap-4 p-3 rounded-2xl border transition-all
                              hover:bg-white/5 cursor-pointer group
                              ${lead.hot ? 'border-tertiary/20 bg-tertiary/5' : 'border-white/5'}`}
                >
                  {lead.hot && (
                    <span className="material-symbols-outlined text-tertiary text-sm flex-shrink-0">
                      local_fire_department
                    </span>
                  )}
                  {!lead.hot && (
                    <span className="material-symbols-outlined text-zinc-700 text-sm flex-shrink-0">
                      work_outline
                    </span>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-white truncate">{lead.title}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[9px] text-zinc-500 uppercase tracking-widest">{lead.tag}</span>
                      <span className="w-1 h-1 rounded-full bg-zinc-700" />
                      <span className="text-[9px] text-zinc-500">{lead.match}% match</span>
                    </div>
                  </div>
                  <span className={`text-xs font-bold flex-shrink-0 ${lead.hot ? 'text-tertiary' : 'text-zinc-400'}`}>
                    {lead.rate}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ── Bottom Dock ─────────────────────────────────────────────── */}
      <footer className="fixed bottom-0 left-16 right-0 z-40 px-8 pb-5 pointer-events-none">
        <div className="max-w-2xl mx-auto pointer-events-auto">
          <div className="apple-glass rounded-[40px] border border-white/8 shadow-2xl
                           flex items-center gap-4 px-6 py-4">
            <span className="material-symbols-outlined text-zinc-600 flex-shrink-0">account_balance</span>
            <input
              value={inputVal}
              onChange={e => setInputVal(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleSend() }}
              disabled={loading}
              placeholder="Ask JARVIS about finances..."
              className="flex-1 bg-transparent border-none focus:outline-none text-sm
                          text-white placeholder:text-zinc-600 disabled:opacity-50"
            />
            {['RECORDING','SPEAKING'].includes(state.jarvis_state) && (
              <WaveformAnimation active />
            )}
            <button
              onClick={handleSend}
              disabled={loading || !inputVal.trim()}
              className="w-9 h-9 rounded-full bg-white text-black flex items-center justify-center
                          hover:scale-105 active:scale-95 transition-all disabled:opacity-30"
            >
              <span className="material-symbols-outlined text-sm">send</span>
            </button>
          </div>
        </div>
      </footer>
    </div>
  )
}
