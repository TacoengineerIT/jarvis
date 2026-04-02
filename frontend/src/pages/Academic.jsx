/**
 * Academic.jsx — V5.5 Polished Academic Hub
 * "Learning Architecture" hero, Drop & Index, Neural Stability, notebooks, flashcards.
 */
import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useJARVIS } from '../hooks/useJARVIS.js'

const NAV = [
  { to: '/',          icon: 'home',           label: 'Home',    end: true  },
  { to: '/financial', icon: 'account_balance', label: 'Finance', end: false },
  { to: '/academic',  icon: 'school',          label: 'Academy', end: false },
  { to: '/system',    icon: 'settings',        label: 'Config',  end: false },
]

const NOTEBOOKS = [
  {
    id: 1,
    icon: 'mic',
    title: 'Lecture: IoT Architectures',
    meta: 'Synthesized 2h ago · 14 Entities',
    tags: [
      { label: 'Bari',       cls: 'bg-white/5 border-white/5 text-on-surface-variant'    },
      { label: 'High Recall', cls: 'bg-tertiary/10 border-tertiary/20 text-tertiary'      },
    ],
  },
  {
    id: 2,
    icon: 'database',
    title: 'Advanced SQL Optimization',
    meta: 'Yesterday · 8 Entities',
    tags: [
      { label: 'SQL',       cls: 'bg-white/5 border-white/5 text-on-surface-variant' },
      { label: 'Technical', cls: 'bg-white/10 border-white/5 text-white'             },
    ],
  },
]

export default function Academic() {
  const { state, loading, sendInput, triggerWakeWord } = useJARVIS()
  const [inputVal, setInputVal]     = useState('')
  const [showAnswer, setShowAnswer] = useState(false)
  const [dragOver, setDragOver]     = useState(false)

  const handleSend = () => {
    if (!inputVal.trim() || loading) return
    sendInput(inputVal.trim())
    setInputVal('')
  }

  const jarvisNbs = state.last_5_commands.filter(c =>
    c.user?.toLowerCase().match(/studia|esame|lezione|appunti|ripassa/)
  )

  return (
    <div className="bg-black text-on-surface selection:bg-primary/20 min-h-screen overflow-x-hidden">

      {/* ── Sidebar ─────────────────────────────────────────────────── */}
      <aside className="fixed left-0 top-0 h-full z-40 flex flex-col items-center py-6
                         bg-black/40 backdrop-blur-3xl w-20 border-r border-white/5">
        <div className="mb-12">
          <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center
                           shadow-lg shadow-white/5">
            <span className="material-symbols-outlined text-black text-lg">blur_on</span>
          </div>
        </div>

        <nav className="flex flex-col gap-10 items-center">
          {NAV.map(({ to, icon, label, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                isActive
                  ? 'flex flex-col items-center gap-1.5 text-white transition-all'
                  : 'group flex flex-col items-center gap-1.5 text-on-surface-variant hover:text-white transition-all'
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className="material-symbols-outlined text-2xl"
                    style={isActive ? { fontVariationSettings: "'FILL' 1" } : {}}
                  >
                    {icon}
                  </span>
                  <span className="text-[9px] font-semibold uppercase tracking-widest">{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto pb-4">
          <div className="w-9 h-9 rounded-full ring-1 ring-white/10 bg-zinc-800/60
                           flex items-center justify-center">
            <span className="text-zinc-400 text-sm font-bold">J</span>
          </div>
        </div>
      </aside>

      {/* ── Top AppBar ──────────────────────────────────────────────── */}
      <header className="fixed top-0 left-0 right-0 z-50 flex justify-center pt-4 px-6 pointer-events-none">
        <div className="glass-card pointer-events-auto rounded-full max-w-2xl px-6 py-2.5
                         flex items-center justify-between w-full">
          <div className="flex items-center gap-3">
            <span className="material-symbols-outlined text-white text-base">blur_on</span>
            <h1 className="text-[9px] font-semibold uppercase tracking-widest text-white">Academic V5.5</h1>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex flex-col items-end">
              <span className="text-[8px] uppercase tracking-widest text-on-surface-variant font-bold">
                ITS Bari Cluster
              </span>
              <span className="text-[9px] text-tertiary font-medium">Status: Nominal</span>
            </div>
            <div className="w-2.5 h-2.5 rounded-full bg-tertiary shadow-[0_0_10px_rgba(255,221,121,0.5)]" />
          </div>
        </div>
      </header>

      {/* ── Main ────────────────────────────────────────────────────── */}
      <main className="pl-20 pt-24 pr-6 pb-32">
        <div className="max-w-6xl mx-auto grid grid-cols-12 gap-8">

          {/* Hero */}
          <section className="col-span-12 mb-4">
            <p className="text-[10px] font-semibold tracking-[0.15em] uppercase text-on-surface-variant mb-2">
              Neural Workspace
            </p>
            <h2 className="text-6xl font-light tracking-tight text-white mb-1">
              Learning <span className="font-medium">Architecture</span>
            </h2>
          </section>

          {/* ── Drop & Index ─────────────────────────────────────────── */}
          <section className="col-span-12 lg:col-span-8">
            <div
              onDragOver={e => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={e => { e.preventDefault(); setDragOver(false) }}
              className={`glass-floating rounded-3xl p-4 min-h-[360px] flex flex-col
                          items-center justify-center text-center group transition-all duration-700
                          ${dragOver ? 'border-white/30' : 'hover:border-white/20'}`}
            >
              <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 mb-8
                               flex items-center justify-center group-hover:scale-105 transition-transform duration-500">
                <span className="material-symbols-outlined text-3xl text-white/50 group-hover:text-white transition-colors">
                  upload_file
                </span>
              </div>
              <h3 className="text-2xl font-light text-white mb-3 tracking-tight">Initialize Neural Feed</h3>
              <p className="text-on-surface-variant max-w-sm mx-auto text-[13px] leading-relaxed mb-10 font-medium">
                Drag datasets or technical manuals to begin neural indexing and cross-context synthesis.
              </p>
              <div className="flex gap-4">
                <button
                  onClick={() => sendInput('index document from storage')}
                  className="bg-white text-black px-10 py-3.5 rounded-full font-bold text-[10px]
                              uppercase tracking-[0.15em] hover:bg-zinc-200 transition-colors shadow-xl shadow-white/5"
                >
                  Browse Storage
                </button>
                <button
                  onClick={() => sendInput('connect google drive')}
                  className="bg-white/5 border border-white/10 text-white px-10 py-3.5 rounded-full
                              font-bold text-[10px] uppercase tracking-[0.15em] hover:bg-white/10 transition-all"
                >
                  Connect Drive
                </button>
              </div>
            </div>
          </section>

          {/* ── Side Metrics ─────────────────────────────────────────── */}
          <section className="col-span-12 lg:col-span-4 flex flex-col gap-6">
            {/* Neural Stability */}
            <div className="glass-card rounded-3xl p-4">
              <div className="flex justify-between items-center mb-6">
                <span className="text-[10px] font-semibold tracking-[0.15em] uppercase text-on-surface-variant">
                  Neural Stability
                </span>
                <span className="material-symbols-outlined text-tertiary text-xs">monitoring</span>
              </div>
              <div className="space-y-8">
                {[
                  { label: 'Network Security',  pct: 88 },
                  { label: 'Whisper Indexing',  pct: 42 },
                ].map(({ label, pct }) => (
                  <div key={label}>
                    <div className="flex justify-between items-end mb-2.5">
                      <span className="text-[10px] uppercase tracking-widest font-bold text-white">{label}</span>
                      <span className="text-[10px] font-mono text-on-surface-variant">{pct}.00%</span>
                    </div>
                    <div className="h-[3px] w-full bg-white/5 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-white shadow-[0_0_12px_rgba(255,255,255,0.4)] transition-all duration-1000"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Current Stream */}
            <div className="glass-card rounded-3xl p-4 relative overflow-hidden h-full min-h-[160px]">
              <div className="absolute inset-0 bg-gradient-to-br from-zinc-800/40 to-zinc-900/20 pointer-events-none rounded-3xl" />
              <div className="relative z-10">
                <span className="text-[10px] font-semibold tracking-[0.15em] uppercase text-on-surface-variant block mb-4">
                  Current Stream
                </span>
                <h4 className="text-xl font-bold text-white mb-1">Cyber-Physical Systems</h4>
                <p className="text-[11px] text-tertiary uppercase tracking-wider font-semibold opacity-90">
                  Module 04: RTOS Optimization
                </p>
              </div>
            </div>
          </section>

          {/* ── Synthesized Notebooks ────────────────────────────────── */}
          <section className="col-span-12 lg:col-span-7">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-[10px] font-semibold tracking-[0.15em] uppercase text-white">
                Synthesized Notebooks
              </h3>
              <button className="text-[9px] uppercase tracking-[0.15em] text-on-surface-variant
                                  hover:text-white transition-colors font-bold">
                Archive →
              </button>
            </div>
            <div className="space-y-3">
              {NOTEBOOKS.map(nb => (
                <div
                  key={nb.id}
                  className="glass-card rounded-2xl p-4 flex items-center justify-between group
                              hover:bg-white/[0.04] transition-all cursor-pointer"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center
                                     text-white/40 group-hover:text-white transition-colors">
                      <span className="material-symbols-outlined text-xl">{nb.icon}</span>
                    </div>
                    <div>
                      <h5 className="text-[13px] font-semibold text-white">{nb.title}</h5>
                      <p className="text-[10px] text-on-surface-variant font-medium">{nb.meta}</p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    {nb.tags.map(t => (
                      <span key={t.label}
                            className={`px-2.5 py-1 border text-[8px] rounded-lg uppercase font-bold tracking-widest ${t.cls}`}>
                        {t.label}
                      </span>
                    ))}
                  </div>
                </div>
              ))}

              {/* JARVIS-generated */}
              {jarvisNbs.map((cmd, i) => (
                <div key={`j-${i}`}
                     className="glass-card rounded-2xl p-4 flex items-center gap-4 border border-tertiary/10">
                  <div className="w-10 h-10 rounded-xl bg-tertiary/10 flex items-center justify-center flex-shrink-0">
                    <span className="material-symbols-outlined text-tertiary text-xl">auto_awesome</span>
                  </div>
                  <div className="min-w-0">
                    <h5 className="text-[13px] font-semibold text-white truncate">{cmd.user}</h5>
                    <p className="text-[10px] text-on-surface-variant">{cmd.response?.slice(0, 80)}</p>
                  </div>
                </div>
              ))}

              <button
                onClick={() => sendInput('nuova sessione studio')}
                className="w-full border border-dashed border-white/10 rounded-2xl p-4
                            flex items-center justify-center gap-3 hover:bg-white/5 transition-all group"
              >
                <span className="material-symbols-outlined text-on-surface-variant group-hover:text-white transition-colors">
                  add
                </span>
                <span className="text-[10px] uppercase tracking-[0.2em] text-on-surface-variant
                                  font-bold group-hover:text-white transition-colors">
                  New Session
                </span>
              </button>
            </div>
          </section>

          {/* ── Flashcards ───────────────────────────────────────────── */}
          <section className="col-span-12 lg:col-span-5">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-[10px] font-semibold tracking-[0.15em] uppercase text-white">
                Active Flashcards
              </h3>
              <span className="px-3 py-1 bg-tertiary/10 border border-tertiary/20 text-tertiary
                                text-[8px] rounded-full font-bold uppercase tracking-widest">
                12 Actionable
              </span>
            </div>
            <div className="space-y-4">
              <div
                onClick={() => setShowAnswer(v => !v)}
                className="glass-card rounded-[2rem] p-4 min-h-[192px] flex flex-col items-center
                            justify-center text-center relative group cursor-pointer hover:border-white/20 transition-all"
              >
                <span className="absolute top-6 text-[10px] font-semibold tracking-[0.15em]
                                  uppercase text-on-surface-variant">
                  Cloud Ops
                </span>
                {showAnswer ? (
                  <p className="text-base font-light text-tertiary leading-relaxed px-6">
                    AWS splits responsibility: provider secures infrastructure, customer secures data &amp; apps.
                  </p>
                ) : (
                  <p className="text-xl font-light text-white leading-relaxed px-6">
                    Define the "Shared Responsibility Model" in AWS deployment.
                  </p>
                )}
                <div className={`absolute bottom-6 transition-opacity ${showAnswer ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
                  <span className="text-[9px] uppercase tracking-[0.2em] font-bold text-tertiary">
                    {showAnswer ? 'Tap for next card' : 'Tap to reveal answer'}
                  </span>
                </div>
              </div>

              <div className="flex gap-4">
                {[
                  { val: '142', label: 'Mastered', cls: 'text-white'   },
                  { val: '24',  label: 'Critical', cls: 'text-error'   },
                  { val: '08',  label: 'Queue',    cls: 'text-tertiary' },
                ].map(({ val, label, cls }) => (
                  <div key={label} className="flex-1 glass-card rounded-2xl p-4 text-center">
                    <span className={`block text-2xl font-light mb-1 ${cls}`}>{val}</span>
                    <span className="text-[7px] font-semibold tracking-[0.15em] uppercase text-on-surface-variant">
                      {label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>
      </main>

      {/* ── Bottom Dock ─────────────────────────────────────────────── */}
      <footer className="fixed bottom-0 left-0 right-0 z-50 flex justify-center pb-8 pointer-events-none">
        <div className="glass-card pointer-events-auto rounded-2xl mx-auto max-w-2xl w-full h-16
                         flex items-center px-4 gap-4 shadow-2xl">
          <button
            onClick={() => triggerWakeWord()}
            className="w-10 h-10 rounded-full bg-white/5 border border-white/10 text-tertiary
                        flex items-center justify-center hover:scale-110 transition-all flex-shrink-0"
          >
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>mic</span>
          </button>

          {/* Waveform */}
          <div className="flex items-center gap-1 h-6 px-4 flex-shrink-0">
            {[2, 4, 6, 3, 5, 3, 4, 2].map((h, i) => (
              <div
                key={i}
                className={`w-1 rounded-full ${i >= 2 && i <= 5 ? 'bg-tertiary animate-pulse' : 'bg-white/20'}`}
                style={{ height: `${h * 3}px`, animationDelay: `${i * 0.15}s` }}
              />
            ))}
          </div>

          {/* Input */}
          <input
            value={inputVal}
            onChange={e => setInputVal(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') handleSend() }}
            disabled={loading}
            placeholder="Studia, esame, appunti..."
            className="flex-1 bg-transparent border-none focus:outline-none text-sm
                        text-on-surface placeholder:text-on-surface-variant/50 disabled:opacity-50"
          />

          <button
            onClick={() => {}}
            className="text-on-surface-variant hover:text-white transition-colors pr-2 flex-shrink-0"
          >
            <span className="material-symbols-outlined text-lg">keyboard_arrow_up</span>
          </button>
        </div>
      </footer>
    </div>
  )
}
