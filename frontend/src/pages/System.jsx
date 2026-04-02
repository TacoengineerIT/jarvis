/**
 * System.jsx — V5.5 Apple-style System DevOps
 * apple-glass panels, JetBrains Mono terminal, led-glow container grid, refined sidebar.
 */
import { useState, useEffect, useRef } from 'react'
import { useJARVIS } from '../hooks/useJARVIS.js'

const INITIAL_LOGS = [
  { ts: '14:22:01.032', tag: 'SYSTEM',  tagCls: 'text-tertiary',   msg: 'Kernel synchronization complete. Ready for I/O requests.' },
  { ts: '14:22:01.045', tag: 'DOCKER',  tagCls: 'text-secondary',  msg: 'Container "sentry-redis-master" health check passed.' },
  { ts: '14:22:02.112', tag: 'WARN',    tagCls: 'text-error',      msg: 'Detected high-entropy traffic on port 443 (PC-Scuola).' },
  { ts: '14:22:02.150', tag: 'SYSTEM',  tagCls: 'text-tertiary',   msg: 'Deploying mitigation protocol "JARVIS_SHIELD_V4"...' },
  { ts: '14:22:03.001', tag: 'SSH',     tagCls: 'text-secondary',  msg: 'Handshake completed. Session ID: _scu001_' },
  { ts: '14:22:03.455', tag: 'INFO',    tagCls: 'text-zinc-600',   msg: '# Routine health sweep initiated. Estimated time: 12ms', italic: true },
  { ts: '14:22:04.220', tag: 'SYSTEM',  tagCls: 'text-tertiary',   msg: 'Sub-processor orbital status at 12%. Heat sink optimal.' },
  { ts: '14:22:05.101', tag: 'DOCKER',  tagCls: 'text-secondary',  msg: 'Image "scuola-node-exporter" updated to latest digest.' },
]

const CONTAINERS = [
  { id: 'SRV-01',  status: 'up'   },
  { id: 'DB-MGR',  status: 'up'   },
  { id: 'CACHE',   status: 'up'   },
  { id: 'AUTH',    status: 'up'   },
  { id: 'NODE-A',  status: 'idle' },
  { id: 'LOG-X',   status: 'up'   },
  { id: 'QUEUE',   status: 'up'   },
  { id: 'ERR-4',   status: 'err'  },
]

function ContainerLed({ id, status }) {
  const cls = {
    up:   'led-glow-active border',
    idle: 'led-glow-idle border',
    err:  'led-glow-error border',
  }[status] || 'border border-zinc-800 bg-zinc-900'

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className={`w-full h-1.5 rounded-full ${cls}`} />
      <span className={`text-[8px] tracking-widest font-mono uppercase ${
        status === 'err' ? 'text-error' : status === 'up' ? 'text-tertiary' : 'text-zinc-600'
      }`}>
        {id}
      </span>
    </div>
  )
}

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
      ts:     makeTs(),
      tag:    'JARVIS',
      tagCls: 'text-white',
      msg:    state.response.slice(0, 160),
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
    <div className="bg-black min-h-screen text-white pl-16">

      {/* ── Header ─────────────────────────────────────────────────── */}
      <div className="px-10 pt-10 pb-6 border-b border-white/5">
        <div className="flex items-end justify-between">
          <div>
            <h1 className="text-3xl font-black tracking-tight text-white">System DevOps</h1>
            <p className="text-zinc-500 text-sm mt-1 font-mono">PC-Scuola · Intel i7-6700HQ</p>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <p className="text-[9px] uppercase tracking-widest text-zinc-600">Containers</p>
              <p className={`text-lg font-bold font-mono ${upCount >= 7 ? 'text-tertiary' : 'text-error'}`}>
                {upCount}/{CONTAINERS.length}
              </p>
            </div>
            <div className="text-right">
              <p className="text-[9px] uppercase tracking-widest text-zinc-600">Link</p>
              <p className={`text-lg font-bold font-mono ${connected ? 'text-tertiary' : 'text-error'}`}>
                {connected ? 'UP' : 'DOWN'}
              </p>
            </div>
            <div className="text-right">
              <p className="text-[9px] uppercase tracking-widest text-zinc-600">API Cost</p>
              <p className="text-lg font-bold font-mono text-white">
                €{(state.api_cost_today || 0).toFixed(4)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Main Grid ─────────────────────────────────────────────── */}
      <main className="px-8 pt-6 pb-24 grid grid-cols-12 gap-6">

        {/* ── Left column ─────────────────────────────────────────── */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-5">

          {/* Container LED grid */}
          <section className="apple-glass rounded-[28px] border border-white/8 p-6">
            <div className="flex justify-between items-center mb-5">
              <h2 className="text-[10px] font-bold tracking-widest uppercase text-zinc-400">
                Sentry Core
              </h2>
              <span className={`text-[10px] font-bold font-mono ${upCount >= 7 ? 'text-tertiary' : 'text-error'}`}>
                {upCount}/{CONTAINERS.length} ACTIVE
              </span>
            </div>
            <div className="grid grid-cols-4 gap-4">
              {CONTAINERS.map(c => <ContainerLed key={c.id} {...c} />)}
            </div>
          </section>

          {/* SSH Status */}
          <section className="apple-glass rounded-[28px] border border-white/8 p-6">
            <div className="flex items-center gap-4 mb-5">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center
                               border ${connected ? 'led-glow-active' : 'led-glow-error'}`}>
                <span className="material-symbols-outlined text-sm text-white">terminal</span>
              </div>
              <div>
                <h3 className="text-xs font-bold tracking-wider text-white uppercase">
                  PC-Scuola Cluster
                </h3>
                <p className={`text-[9px] font-mono tracking-widest uppercase mt-0.5 ${
                  connected ? 'text-tertiary' : 'text-error'
                }`}>
                  {connected ? 'SSH Link Established' : 'No Connection'}
                </p>
              </div>
            </div>
            <div className="space-y-3">
              {[
                { label: 'Protocol', value: 'RSA-4096 / AES-256' },
                { label: 'Latency',  value: connected ? '4ms' : '—',  valueColor: connected ? 'text-tertiary' : 'text-zinc-600' },
                { label: 'JARVIS Core', value: state.jarvis_state, valueColor: state.jarvis_state !== 'LISTENING' ? 'text-tertiary' : 'text-secondary' },
              ].map(({ label, value, valueColor = 'text-zinc-300' }) => (
                <div key={label} className="flex justify-between items-center text-[10px] font-mono">
                  <span className="text-zinc-600 uppercase tracking-widest">{label}</span>
                  <span className={valueColor}>{value}</span>
                </div>
              ))}
              <div className="w-full bg-zinc-800 h-0.5 rounded-full overflow-hidden mt-1">
                <div className={`h-full transition-all duration-500 ${
                  connected ? 'w-[88%] bg-primary shadow-[0_0_8px_#c6c6c8]' : 'w-0'
                }`} />
              </div>
            </div>
          </section>

          {/* Right command strip (as buttons in sidebar on mobile, inline here) */}
          <div className="flex gap-3">
            {[
              { icon: 'bolt',    color: 'hover:text-tertiary',  title: 'Power'   },
              { icon: 'cancel',  color: 'hover:text-error',     title: 'Kill'    },
              { icon: 'refresh', color: 'hover:text-white',     title: 'Restart' },
            ].map(({ icon, color, title }) => (
              <button
                key={icon}
                title={title}
                className={`flex-1 apple-glass rounded-2xl border border-white/8 py-3
                             flex items-center justify-center cursor-pointer
                             hover:scale-105 transition-transform group`}
              >
                <span className={`material-symbols-outlined text-zinc-600 ${color} transition-colors`}>
                  {icon}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* ── Center: Log stream ──────────────────────────────────── */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-0">
          <section className="apple-glass rounded-[28px] border border-white/8
                               flex flex-col overflow-hidden" style={{ minHeight: '520px' }}>

            {/* Log header */}
            <div className="px-6 py-4 border-b border-white/5 flex justify-between items-center bg-black/20">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${paused ? 'bg-zinc-600' : 'bg-error animate-pulse'}`} />
                <span className="text-[10px] font-mono tracking-widest uppercase text-zinc-400">
                  {paused ? 'Stream Paused' : 'Live · JARVIS + System'}
                </span>
              </div>
              <div className="flex items-center gap-4">
                <button
                  onClick={() => setPaused(p => !p)}
                  className="material-symbols-outlined text-sm text-zinc-600
                              hover:text-white transition-colors cursor-pointer"
                >
                  {paused ? 'play_arrow' : 'pause'}
                </button>
                <button
                  onClick={() => setLogs(INITIAL_LOGS)}
                  className="material-symbols-outlined text-sm text-zinc-600
                              hover:text-white transition-colors cursor-pointer"
                >
                  refresh
                </button>
              </div>
            </div>

            {/* Log body */}
            <div className="p-6 flex-1 overflow-y-auto space-y-1 font-mono">
              {logs.map((line, i) => (
                <div key={i} className={`flex gap-4 text-[11px] leading-loose ${line.italic ? 'italic' : ''}`}>
                  <span className="text-zinc-700 flex-shrink-0">{line.ts}</span>
                  <span className={`${line.tagCls} flex-shrink-0`}>[{line.tag}]</span>
                  <span className="text-zinc-300">{line.msg}</span>
                </div>
              ))}
              <div ref={logEndRef} />
            </div>

            {/* Terminal input */}
            <div className="bg-black/60 px-6 py-4 border-t border-white/5">
              <div className="flex items-center gap-4">
                <span className="text-tertiary font-bold font-mono text-sm flex-shrink-0">$</span>
                <input
                  value={cmdVal}
                  onChange={e => setCmdVal(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') handleCmd() }}
                  disabled={loading}
                  autoFocus
                  placeholder="Execute command on JARVIS..."
                  className="bg-transparent border-none focus:outline-none text-white
                              font-mono text-sm w-full placeholder:text-zinc-700
                              disabled:opacity-50"
                />
                <button
                  onClick={handleCmd}
                  disabled={loading || !cmdVal.trim()}
                  className="material-symbols-outlined text-zinc-600 hover:text-tertiary
                              transition-colors cursor-pointer disabled:opacity-30 text-sm"
                >
                  send
                </button>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
