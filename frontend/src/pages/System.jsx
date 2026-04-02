/**
 * System.jsx — V5.5 System DevOps
 * Docker Sentry grid, SSH status, API cost, real-time log stream, right command strip.
 */
import { useState, useEffect, useRef } from 'react'
import { useJARVIS } from '../hooks/useJARVIS.js'

const INITIAL_LOGS = [
  { ts: '14:22:01.032', tag: 'SYSTEM',  tagCls: 'text-tertiary',              msg: 'Kernel synchronization complete. Ready for I/O requests.' },
  { ts: '14:22:01.045', tag: 'DOCKER',  tagCls: 'text-secondary',             msg: 'Container "sentry-redis-master" health check passed.' },
  { ts: '14:22:02.112', tag: 'WARN',    tagCls: 'text-error',                 msg: 'Detected high-entropy traffic on port 443 (PC-Scuola).', errCls: 'text-error-dim' },
  { ts: '14:22:02.150', tag: 'SYSTEM',  tagCls: 'text-tertiary',              msg: 'Deploying mitigation protocol "JARVIS_SHIELD_V4"...' },
  { ts: '14:22:03.001', tag: 'SSH',     tagCls: 'text-secondary',             msg: 'Handshake completed. Session ID: _scu001_' },
  { ts: '14:22:03.455', tag: 'INFO',    tagCls: 'text-on-surface-variant/40', msg: '# Routine health sweep initiated. Estimated time: 12ms', italic: true },
  { ts: '14:22:04.220', tag: 'SYSTEM',  tagCls: 'text-tertiary',              msg: 'Sub-processor orbital status at 12%. Heat sink optimal.' },
  { ts: '14:22:05.101', tag: 'DOCKER',  tagCls: 'text-secondary',             msg: 'Image "scuola-node-exporter" updated to latest digest.' },
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

function StatusLed({ id, status }) {
  const cls = {
    up:   'border-tertiary bg-tertiary/20 shadow-[0_0_8px_rgba(255,221,121,0.4)]',
    idle: 'border-primary  bg-primary/20 opacity-60',
    err:  'border-error    bg-error/20   shadow-[0_0_8px_rgba(238,125,119,0.4)]',
  }[status] || 'border-outline-variant bg-surface-variant'

  return (
    <div className="flex flex-col items-center gap-2">
      <div className={`w-10 h-1 border rounded-full ${cls}`} />
      <span className={`text-[8px] tracking-widest ${status === 'err' ? 'text-error' : 'text-on-surface-variant'}`}>
        {id}
      </span>
    </div>
  )
}

function makeTs() {
  const now = new Date()
  return `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}.${String(now.getMilliseconds()).padStart(3,'0')}`
}

export default function System() {
  const { state, connected, loading, sendInput } = useJARVIS()
  const [logs, setLogs]     = useState(INITIAL_LOGS)
  const [cmdVal, setCmdVal] = useState('')
  const [paused, setPaused] = useState(false)
  const logEndRef           = useRef(null)

  const upCount = CONTAINERS.filter(c => c.status === 'up').length

  // Append JARVIS response to log stream
  useEffect(() => {
    if (!state.response || paused) return
    setLogs(prev => [...prev.slice(-50), {
      ts:     makeTs(),
      tag:    'JARVIS',
      tagCls: 'text-primary-fixed',
      msg:    state.response.slice(0, 140),
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
    <div className="bg-surface-container-lowest font-body text-on-surface min-h-screen selection:bg-tertiary/30">

      {/* ── Main grid ──────────────────────────────────────────────── */}
      <main className="pl-20 pt-24 pb-20 min-h-screen grid grid-cols-12 gap-6 p-8">

        {/* ── Left column ─────────────────────────────────────────── */}
        <div className="col-span-12 lg:col-span-4 flex flex-col gap-6">

          {/* Sentry Docker Grid */}
          <section className="liquid-glass rounded-xl p-6 border border-outline-variant/15
                               flex flex-col gap-5 hover:scale-[1.01] transition-transform">
            <div className="flex justify-between items-center">
              <h2 className="text-[10px] font-medium tracking-[0.2em] uppercase text-on-surface-variant">
                Sentry Core Status
              </h2>
              <span className={`text-[10px] font-bold ${upCount >= 7 ? 'text-tertiary' : 'text-error'}`}>
                {upCount}/{CONTAINERS.length} UP
              </span>
            </div>
            <div className="grid grid-cols-4 gap-4">
              {CONTAINERS.map(c => <StatusLed key={c.id} {...c} />)}
            </div>
          </section>

          {/* SSH Status */}
          <section className="liquid-glass rounded-xl p-6 border border-outline-variant/15 flex flex-col gap-4">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-full bg-surface-container-high border border-outline-variant/20">
                <span className="material-symbols-outlined text-primary">terminal</span>
              </div>
              <div>
                <h3 className="text-xs font-bold tracking-wider text-primary-fixed uppercase">
                  PC-Scuola Cluster
                </h3>
                <p className={`text-[10px] tracking-widest uppercase ${connected ? 'text-tertiary' : 'text-error'}`}>
                  {connected ? 'SSH Link Established' : 'No Connection'}
                </p>
              </div>
            </div>
            <div className="flex flex-col gap-3 pt-1">
              <div className="flex justify-between items-center text-[10px]">
                <span className="text-on-surface-variant uppercase tracking-widest">Protocol</span>
                <span className="text-primary-fixed">RSA-4096 / AES-256</span>
              </div>
              <div className="flex justify-between items-center text-[10px]">
                <span className="text-on-surface-variant uppercase tracking-widest">WS Latency</span>
                <span className="text-tertiary">{connected ? '4ms' : '—'}</span>
              </div>
              <div className="flex justify-between items-center text-[10px]">
                <span className="text-on-surface-variant uppercase tracking-widest">JARVIS Core</span>
                <span className={state.jarvis_state !== 'LISTENING' ? 'text-tertiary' : 'text-secondary'}>
                  {state.jarvis_state}
                </span>
              </div>
              <div className="w-full bg-surface-variant h-0.5 rounded-full overflow-hidden">
                <div className={`h-full transition-all duration-500 ${
                  connected ? 'w-[88%] bg-primary shadow-[0_0_8px_#c6c6c8]' : 'w-0'
                }`} />
              </div>
            </div>
          </section>

          {/* API Cost tracker */}
          <section className="liquid-glass rounded-xl p-6 border border-outline-variant/15">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[10px] uppercase tracking-widest text-on-surface-variant">API Cost Today</h3>
              <span className="material-symbols-outlined text-sm text-secondary">monetization_on</span>
            </div>
            <p className="text-2xl font-light text-primary-fixed">
              €{(state.api_cost_today || 0).toFixed(4)}
            </p>
            <p className="text-[10px] text-on-surface-variant mt-1">
              {state.last_5_commands.length} requests · Haiku + Sonnet
            </p>
          </section>
        </div>

        {/* ── Center column: Log streamer ────────────────────────── */}
        <div className="col-span-12 lg:col-span-8 flex flex-col gap-6">
          <section className="flex-1 liquid-glass rounded-xl border border-outline-variant/15
                               flex flex-col overflow-hidden min-h-[520px]">

            {/* Log header */}
            <div className="px-6 py-4 border-b border-outline-variant/10 flex justify-between
                             items-center bg-black/20">
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${paused ? 'bg-secondary' : 'bg-error animate-pulse'}`} />
                <span className="text-[10px] font-medium tracking-[0.2em] uppercase text-[#c6c6c8]">
                  {paused ? 'Stream Paused' : 'Live Stream: JARVIS + System'}
                </span>
              </div>
              <div className="flex gap-4">
                <button
                  onClick={() => setPaused(p => !p)}
                  className="material-symbols-outlined text-xs text-on-surface-variant
                              cursor-pointer hover:text-primary transition-colors"
                >
                  {paused ? 'play_arrow' : 'pause'}
                </button>
                <button
                  onClick={() => setLogs(INITIAL_LOGS)}
                  className="material-symbols-outlined text-xs text-on-surface-variant
                              cursor-pointer hover:text-primary transition-colors"
                >
                  refresh
                </button>
                <span className="material-symbols-outlined text-xs text-on-surface-variant
                                  cursor-pointer hover:text-primary transition-colors">
                  filter_list
                </span>
              </div>
            </div>

            {/* Log body */}
            <div className="p-6 flex-1 overflow-y-auto space-y-1">
              {logs.map((line, i) => (
                <div key={i} className={`log-line ${line.italic ? 'italic' : ''}`}>
                  <span className="text-primary-container/60 flex-shrink-0 font-mono">{line.ts}</span>
                  <span className={`${line.tagCls} flex-shrink-0 font-mono`}>[{line.tag}]</span>
                  <span className={line.errCls || 'text-on-surface'}>{line.msg}</span>
                </div>
              ))}
              <div ref={logEndRef} />
            </div>

            {/* Terminal input */}
            <div className="bg-black/60 p-4 border-t border-outline-variant/10">
              <div className="flex items-center gap-4 group">
                <span className="text-tertiary font-bold font-mono">$</span>
                <input
                  value={cmdVal}
                  onChange={e => setCmdVal(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') handleCmd() }}
                  disabled={loading}
                  autoFocus
                  placeholder="Execute command on JARVIS..."
                  className="bg-transparent border-none focus:outline-none focus:ring-0
                              text-primary-fixed font-mono text-sm w-full
                              placeholder:text-on-surface-variant/30 disabled:opacity-50"
                />
                <button
                  onClick={handleCmd}
                  disabled={loading || !cmdVal.trim()}
                  className="material-symbols-outlined text-primary-container
                              group-hover:text-tertiary transition-colors cursor-pointer
                              disabled:opacity-40"
                >
                  send
                </button>
              </div>
            </div>
          </section>
        </div>
      </main>

      {/* ── Bottom Dock ─────────────────────────────────────────────── */}
      <footer className="fixed bottom-0 left-0 w-full z-50 flex justify-center items-center
                          gap-20 pb-4 h-16 rounded-t-[32px] bg-[#0e0e0e]/40 backdrop-blur-2xl
                          border-t border-[#484848]/15">
        <div className="flex items-center gap-10 bg-surface-container-high/40 px-10 py-2
                         rounded-full border border-outline-variant/10">
          <button className="text-[#454749] hover:text-[#c6c6c8] transition-colors flex items-center gap-2">
            <span className="material-symbols-outlined">mic_none</span>
            <span className="text-[10px] font-bold tracking-[0.2em] uppercase text-on-surface-variant">
              Listening
            </span>
          </button>
          <div className="h-4 w-px bg-outline-variant/20" />
          <div className="flex items-end gap-1 h-8">
            {[3,5,8,6,4].map((h,i) => (
              <div
                key={i}
                className="w-1 bg-tertiary/60 rounded-full waveform-bar"
                style={{ height: `${h * 3}px`, animationDelay: `${i * 0.1}s` }}
              />
            ))}
          </div>
          <div className="h-4 w-px bg-outline-variant/20" />
          <button className="text-[#ffdd79] drop-shadow-[0_0_8px_rgba(255,221,121,0.5)]
                              flex items-center gap-2">
            <span className="material-symbols-outlined">graphic_eq</span>
            <span className="text-[10px] font-bold tracking-[0.2em] uppercase">Analyzer</span>
          </button>
        </div>
      </footer>

      {/* ── Right command strip ──────────────────────────────────────── */}
      <div className="fixed right-6 top-1/2 -translate-y-1/2 flex flex-col gap-4 z-40">
        {[
          { icon: 'bolt',    hover: 'group-hover:text-tertiary',      title: 'Power'   },
          { icon: 'cancel',  hover: 'group-hover:text-error',         title: 'Kill'    },
          { icon: 'refresh', hover: 'group-hover:text-primary-fixed', title: 'Restart' },
        ].map(({ icon, hover, title }) => (
          <button
            key={icon}
            title={title}
            className="liquid-glass p-3 rounded-full border border-outline-variant/10
                        cursor-pointer hover:scale-110 transition-transform group"
          >
            <span className={`material-symbols-outlined text-primary ${hover} transition-colors`}>
              {icon}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
