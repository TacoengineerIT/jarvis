/**
 * System.jsx — V5.5 Polished System DevOps
 * w-14 sidebar, Sentry LED grid, Node connectivity, Log streamer, right action strip.
 */
import { useState, useEffect, useRef } from 'react'
import { NavLink } from 'react-router-dom'
import { useJARVIS } from '../hooks/useJARVIS.js'

const NAV = [
  { to: '/',          icon: 'dashboard' },
  { to: '/financial', icon: 'payments'  },
  { to: '/academic',  icon: 'school'    },
  { to: '/system',    icon: 'settings'  },
]

const CONTAINERS = [
  { id: 'SRV-01', status: 'up'   },
  { id: 'DB-MGR', status: 'up'   },
  { id: 'CACHE',  status: 'up'   },
  { id: 'AUTH',   status: 'up'   },
  { id: 'NODE-A', status: 'idle' },
  { id: 'LOG-X',  status: 'up'   },
  { id: 'QUEUE',  status: 'up'   },
  { id: 'ERR-4',  status: 'err'  },
]

const INITIAL_LOGS = [
  { ts: '14:22:01.032', tag: 'SYSTEM', tagCls: 'text-tertiary',  msg: 'Kernel synchronization complete. Ready for I/O requests.' },
  { ts: '14:22:01.045', tag: 'DOCKER', tagCls: 'text-secondary', msg: 'Container "sentry-redis-master" health check passed.' },
  { ts: '14:22:02.112', tag: 'WARN',   tagCls: 'text-error',     msg: 'Detected unexpected high-entropy traffic on port 443. PC-Scuola.' },
  { ts: '14:22:02.150', tag: 'SYSTEM', tagCls: 'text-tertiary',  msg: 'Deploying mitigation protocol "JARVIS_SHIELD_V5"...' },
  { ts: '14:22:03.001', tag: 'SSH',    tagCls: 'text-secondary', msg: 'Handshake completed. Session ID: _scu001_' },
  { ts: '14:22:03.455', tag: 'INFO',   tagCls: 'text-white/30',  msg: '# Routine health sweep initiated. Estimated time: 12ms', italic: true },
  { ts: '14:22:04.220', tag: 'SYSTEM', tagCls: 'text-tertiary',  msg: 'Sub-processor orbital status at 12%. Heat sink optimal.' },
  { ts: '14:22:05.101', tag: 'DOCKER', tagCls: 'text-secondary', msg: 'Image "scuola-node-exporter" updated to latest digest.' },
]

function makeTs() {
  const n = new Date()
  return `${String(n.getHours()).padStart(2,'0')}:${String(n.getMinutes()).padStart(2,'0')}:${String(n.getSeconds()).padStart(2,'0')}.${String(n.getMilliseconds()).padStart(3,'0')}`
}

export default function System() {
  const { state, connected, loading, sendInput } = useJARVIS()
  const [logs, setLogs]     = useState(INITIAL_LOGS)
  const [cmdVal, setCmdVal] = useState('')
  const [paused, setPaused] = useState(false)
  const logEndRef           = useRef(null)

  const upCount = CONTAINERS.filter(c => c.status === 'up').length

  useEffect(() => {
    if (!state.response || paused) return
    setLogs(prev => [...prev.slice(-60), {
      ts: makeTs(), tag: 'JARVIS', tagCls: 'text-white', msg: state.response.slice(0, 160),
    }])
  }, [state.response])

  useEffect(() => {
    if (!paused) logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs, paused])

  const handleCmd = () => {
    if (!cmdVal.trim()) return
    setLogs(prev => [...prev, { ts: makeTs(), tag: 'INPUT', tagCls: 'text-tertiary', msg: `$ ${cmdVal}` }])
    sendInput(cmdVal)
    setCmdVal('')
  }

  return (
    <div className="bg-black min-h-screen font-body text-on-surface selection:bg-tertiary/30 overflow-x-hidden">

      {/* ── Sidebar (w-14) ──────────────────────────────────────────── */}
      <aside className="fixed left-0 top-0 h-full w-14 border-r border-white/5 apple-glass
                         flex flex-col items-center py-6 gap-8 z-[60]">
        <div className="flex flex-col items-center gap-1">
          <div className="w-7 h-7 rounded-full border border-white/10 bg-zinc-800/60
                           flex items-center justify-center">
            <span className="text-zinc-400 text-[8px] font-bold">J</span>
          </div>
          <span className="text-[7px] font-semibold tracking-widest text-on-surface-variant">V5.5</span>
        </div>

        <nav className="flex flex-col gap-6 items-center">
          {NAV.map(({ to, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                isActive
                  ? 'text-white bg-white/10 p-2 rounded-lg'
                  : 'text-on-surface-variant hover:text-white transition-colors p-2'
              }
            >
              {({ isActive }) => (
                <span
                  className="material-symbols-outlined !text-[20px]"
                  style={isActive ? { fontVariationSettings: "'FILL' 1" } : {}}
                >
                  {icon}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto">
          <span className="text-[8px] text-tertiary font-medium tracking-widest"
                style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)' }}>
            ACTIVE
          </span>
        </div>
      </aside>

      {/* ── Top Header ──────────────────────────────────────────────── */}
      <header className="fixed top-0 left-0 right-0 z-50 flex items-center px-4 h-14 pointer-events-none">
        <div className="pointer-events-auto rounded-full mx-auto max-w-md h-9 apple-glass
                         border border-white/10 shadow-2xl flex items-center justify-between px-4 w-full">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-on-surface-variant text-sm">blur_on</span>
            <h1 className="font-semibold uppercase tracking-widest text-[9px] text-on-surface-variant">
              Dynamic Briefing
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <div className={`w-1.5 h-1.5 rounded-full ${
              connected ? 'bg-tertiary shadow-[0_0_8px_rgba(255,221,121,0.4)]' : 'bg-error'
            }`} />
            <span className="material-symbols-outlined text-on-surface-variant text-lg">account_circle</span>
          </div>
        </div>
      </header>

      {/* ── Main Grid ───────────────────────────────────────────────── */}
      <main className="pl-14 pt-14 pb-24 min-h-screen">
        <div className="p-4 grid grid-cols-12 gap-4 max-w-[1400px] mx-auto">

          {/* ── Left Panel ──────────────────────────────────────────── */}
          <div className="col-span-12 lg:col-span-4 flex flex-col gap-4">

            {/* Sentry Core */}
            <section className="apple-glass rounded-xl p-4 border border-white/5 flex flex-col gap-5">
              <div className="flex justify-between items-center">
                <h2 className="text-[10px] font-semibold tracking-widest uppercase text-on-surface-variant">
                  Sentry Core Status
                </h2>
                <span className={`text-[10px] font-bold ${upCount >= 7 ? 'text-tertiary' : 'text-error'}`}>
                  {upCount}/{CONTAINERS.length} UP
                </span>
              </div>
              <div className="grid grid-cols-4 gap-x-2 gap-y-4">
                {CONTAINERS.map(({ id, status }) => (
                  <div key={id} className="flex flex-col items-center gap-1.5">
                    <div className={`w-full h-[2px] rounded-full ${
                      status === 'up'   ? 'bg-tertiary led-glow-active' :
                      status === 'idle' ? 'bg-white/40 opacity-40' :
                                          'bg-error led-glow-error'
                    }`} />
                    <span className={`text-[7px] font-medium tracking-tighter uppercase ${
                      status === 'err' ? 'text-error' : 'text-on-surface-variant'
                    }`}>
                      {id}
                    </span>
                  </div>
                ))}
              </div>
            </section>

            {/* Node Connectivity */}
            <section className="apple-glass rounded-xl p-4 border border-white/5 flex flex-col gap-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/10
                                 flex items-center justify-center">
                  <span className="material-symbols-outlined text-on-surface-variant !text-[18px]">terminal</span>
                </div>
                <div>
                  <h3 className="text-[10px] font-bold tracking-widest uppercase text-white">
                    PC-Scuola Cluster
                  </h3>
                  <p className={`text-[8px] uppercase font-medium tracking-widest ${
                    connected ? 'text-on-surface-variant' : 'text-error'
                  }`}>
                    {connected ? 'Link Established' : 'No Connection'}
                  </p>
                </div>
              </div>
              <div className="space-y-2.5">
                {[
                  { label: 'PROTOCOL', value: 'RSA-4096 / AES-256', cls: 'text-white'   },
                  { label: 'LATENCY',  value: connected ? '4ms' : '—', cls: 'text-tertiary' },
                  { label: 'STATE',    value: state.jarvis_state,    cls: 'text-secondary' },
                ].map(({ label, value, cls }) => (
                  <div key={label} className="flex justify-between items-center">
                    <span className="text-[9px] text-on-surface-variant font-medium">{label}</span>
                    <span className={`text-[9px] font-mono ${cls}`}>{value}</span>
                  </div>
                ))}
                <div className="w-full bg-white/5 h-[2px] rounded-full overflow-hidden mt-1">
                  <div className={`h-full transition-all duration-700 ${
                    connected ? 'w-[88%] bg-white shadow-[0_0_10px_rgba(255,255,255,0.3)]' : 'w-0'
                  }`} />
                </div>
              </div>
            </section>
          </div>

          {/* ── Right Panel: Log Streamer ───────────────────────────── */}
          <div className="col-span-12 lg:col-span-8 flex flex-col gap-4">
            <section className="flex-1 apple-glass rounded-xl border border-white/10 flex flex-col
                                  overflow-hidden min-h-[600px] shadow-2xl">

              {/* Log Header */}
              <div className="px-4 py-3 border-b border-white/10 flex justify-between items-center bg-black/40">
                <div className="flex items-center gap-2">
                  <div className={`w-1.5 h-1.5 rounded-full ${paused ? 'bg-zinc-500' : 'bg-error animate-pulse'}`} />
                  <span className="text-[9px] font-semibold tracking-widest uppercase text-white">
                    {paused ? 'Stream Paused' : 'Live Stream: Global Events'}
                  </span>
                </div>
                <div className="flex gap-4">
                  <button
                    onClick={() => setPaused(p => !p)}
                    className="material-symbols-outlined !text-[14px] text-on-surface-variant
                                cursor-pointer hover:text-white transition-colors"
                  >
                    {paused ? 'play_arrow' : 'pause'}
                  </button>
                  <button
                    onClick={() => setLogs(INITIAL_LOGS)}
                    className="material-symbols-outlined !text-[14px] text-on-surface-variant
                                cursor-pointer hover:text-white transition-colors"
                  >
                    refresh
                  </button>
                  <span className="material-symbols-outlined !text-[14px] text-on-surface-variant
                                    cursor-pointer hover:text-white transition-colors">
                    filter_list
                  </span>
                </div>
              </div>

              {/* Log Body */}
              <div className="p-4 flex-1 font-mono text-[11px] leading-relaxed overflow-y-auto space-y-1 bg-black/20">
                {logs.map((line, i) => (
                  <div key={i} className={`flex gap-3 ${line.italic ? 'italic' : ''}`}>
                    <span className="text-white/30 tabular-nums flex-shrink-0">{line.ts}</span>
                    <span className={`${line.tagCls} font-bold flex-shrink-0`}>[{line.tag}]</span>
                    <span className="text-on-surface-variant/90">{line.msg}</span>
                  </div>
                ))}
                <div ref={logEndRef} />
              </div>

              {/* Terminal Input */}
              <div className="bg-black p-3 border-t border-white/10">
                <div className="flex items-center gap-3 bg-white/5 rounded-lg px-3 py-2
                                 border border-white/5 focus-within:border-white/20 transition-all">
                  <span className="text-tertiary font-mono text-xs font-bold flex-shrink-0">$</span>
                  <input
                    value={cmdVal}
                    onChange={e => setCmdVal(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') handleCmd() }}
                    disabled={loading}
                    autoFocus
                    placeholder="Execute command on PC-Scuola..."
                    className="bg-transparent border-none focus:ring-0 text-white font-mono
                                text-xs w-full placeholder:text-white/20 disabled:opacity-50"
                  />
                  <button
                    onClick={handleCmd}
                    disabled={loading || !cmdVal.trim()}
                    className="material-symbols-outlined text-on-surface-variant hover:text-white
                                transition-colors cursor-pointer !text-[18px] disabled:opacity-30"
                  >
                    send
                  </button>
                </div>
              </div>
            </section>
          </div>
        </div>
      </main>

      {/* ── Bottom Analyzer Dock ────────────────────────────────────── */}
      <footer className="fixed bottom-4 left-0 right-0 z-50 px-4 pointer-events-none">
        <div className="pointer-events-auto mx-auto max-w-lg apple-glass border border-white/10
                         rounded-2xl h-12 shadow-2xl flex items-center justify-between px-6">
          <button className="flex items-center gap-2 text-on-surface-variant hover:text-white transition-colors">
            <span className="material-symbols-outlined !text-[18px]">mic_none</span>
            <span className="text-[9px] font-bold tracking-widest uppercase">Listening</span>
          </button>
          <div className="flex items-end gap-[3px]">
            {[2, 4, 7, 5, 3].map((h, i) => (
              <div
                key={i}
                className={`w-[2px] rounded-full ${i === 2 ? 'bg-tertiary shadow-[0_0_8px_rgba(255,221,121,0.4)]' : i === 1 || i === 3 ? 'bg-tertiary/50' : 'bg-tertiary/30'}`}
                style={{ height: `${h * 3}px` }}
              />
            ))}
          </div>
          <button className="flex items-center gap-2 text-tertiary">
            <span className="material-symbols-outlined !text-[18px]">graphic_eq</span>
            <span className="text-[9px] font-bold tracking-widest uppercase">Analyzer Active</span>
          </button>
        </div>
      </footer>

      {/* ── Right Action Strip ──────────────────────────────────────── */}
      <div className="fixed right-4 top-1/2 -translate-y-1/2 flex flex-col gap-3 z-50">
        {[
          { icon: 'bolt',    hover: 'hover:bg-white hover:text-black'     },
          { icon: 'close',   hover: 'hover:bg-error hover:text-white'     },
          { icon: 'refresh', hover: 'hover:bg-white hover:text-black'     },
        ].map(({ icon, hover }) => (
          <div
            key={icon}
            className={`apple-glass p-2.5 rounded-full border border-white/10 cursor-pointer
                         transition-all group shadow-xl ${hover}`}
          >
            <span className="material-symbols-outlined !text-[18px] group-hover:scale-110 transition-transform">
              {icon}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
