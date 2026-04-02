/**
 * Academic.jsx — V5.5 Polished Academic Hub
 * Learning Architecture hero, dual-upload buttons, Neural Stability metrics, notebooks.
 */
import { useState } from 'react'
import { useJARVIS } from '../hooks/useJARVIS.js'
import WaveformAnimation from '../components/WaveformAnimation.jsx'

const MOCK_NOTEBOOKS = [
  {
    id: 1,
    icon: 'description',
    title: 'Deep Learning Foundations: Lec 04',
    meta: 'Transcription & Index complete',
    tag: '12 Insights',
    tagColor: 'text-tertiary',
    time: '14:02',
  },
  {
    id: 2,
    icon: 'auto_awesome',
    title: 'Market Economics — Master Case Study',
    meta: 'Refined via RAG augmentation',
    tag: '94% Confidence',
    tagColor: 'text-zinc-500',
    time: 'Yesterday',
  },
  {
    id: 3,
    icon: 'mic',
    title: 'Brainstorm: AI Safety Protocols',
    meta: 'Voice-to-Text conversion',
    tag: '32m 14s',
    tagColor: 'text-zinc-500',
    time: 'Oct 12',
  },
]

const FLASHCARD = {
  question: '"Explain the core principle of RAG (Retrieval-Augmented Generation)..."',
  answer:   'RAG combines retrieval of relevant documents with language generation, grounding responses in factual, up-to-date knowledge.',
  subject:  'Neural Arch',
}

const NEURAL_METRICS = [
  { label: 'Index Depth',   value: '94%',   bar: 94,  color: 'bg-primary'    },
  { label: 'Recall Score',  value: '88%',   bar: 88,  color: 'bg-tertiary'   },
  { label: 'Sync Stability',value: '100%',  bar: 100, color: 'bg-secondary'  },
]

export default function Academic() {
  const { state, loading, sendInput } = useJARVIS()
  const [inputVal, setInputVal]     = useState('')
  const [showAnswer, setShowAnswer] = useState(false)
  const [dragOver, setDragOver]     = useState(false)

  const handleSend = () => {
    if (!inputVal.trim() || loading) return
    sendInput(inputVal.trim())
    setInputVal('')
  }

  const jarvisNotebooks = state.last_5_commands.filter(c =>
    c.input?.toLowerCase().match(/studia|esame|lezione|appunti|ripassa/)
  )

  return (
    <div className="bg-black min-h-screen text-white pl-16 pb-32 overflow-x-hidden">

      {/* ── Hero Header ──────────────────────────────────────────── */}
      <div className="px-10 pt-10 pb-2">
        <div className="flex items-end justify-between">
          <div>
            <p className="text-[10px] uppercase tracking-widest text-zinc-600 mb-2">
              ITS Bari · Neural Indexing v2
            </p>
            <h1 className="text-4xl font-black tracking-tight text-white">
              Learning Architecture
            </h1>
          </div>
          <div className="flex items-center gap-3 pb-1">
            <span className="text-[10px] text-zinc-500 uppercase tracking-widest">RAG</span>
            <div className="w-1.5 h-1.5 rounded-full bg-tertiary shadow-[0_0_6px_#ffdd79] animate-pulse" />
            <span className="text-[10px] text-tertiary uppercase tracking-widest">Live</span>
          </div>
        </div>

        {/* Neural Stability metrics strip */}
        <div className="flex gap-8 mt-6 pb-6 border-b border-white/5">
          {NEURAL_METRICS.map(m => (
            <div key={m.label} className="flex items-center gap-4">
              <div className="w-24">
                <div className="flex justify-between text-[9px] text-zinc-600 uppercase tracking-widest mb-1">
                  <span>{m.label}</span>
                  <span className="text-zinc-400">{m.value}</span>
                </div>
                <div className="h-0.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div className={`h-full ${m.color} rounded-full`} style={{ width: `${m.bar}%` }} />
                </div>
              </div>
            </div>
          ))}
          <div className="ml-auto flex items-center gap-2">
            <span className="text-[10px] text-zinc-500">1.2M tokens</span>
            <span className="w-1 h-1 rounded-full bg-zinc-700" />
            <span className="text-[10px] text-zinc-500">8,402 semantic links</span>
            <span className="w-1 h-1 rounded-full bg-zinc-700" />
            <span className="text-[10px] text-tertiary">84 flashcards due</span>
          </div>
        </div>
      </div>

      {/* ── Main Grid ─────────────────────────────────────────────── */}
      <main className="px-8 pt-6 grid grid-cols-12 gap-6">

        {/* ── Left Column ─────────────────────────────────────────── */}
        <div className="col-span-12 lg:col-span-5 space-y-5">

          {/* Document Upload Zone */}
          <div
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={e => { e.preventDefault(); setDragOver(false) }}
            className={`apple-glass border rounded-[32px] p-8 relative overflow-hidden
                        h-[260px] flex flex-col items-center justify-center text-center
                        transition-all duration-300
                        ${dragOver ? 'border-tertiary/50 bg-tertiary/5' : 'border-white/8 hover:border-white/15'}`}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent
                            pointer-events-none rounded-[32px]" />
            <div className="w-16 h-16 rounded-2xl bg-zinc-800/60 flex items-center justify-center
                             mb-5 border border-white/8 relative z-10 transition-transform
                             hover:scale-110 duration-500">
              <span className="material-symbols-outlined text-zinc-300 text-2xl">upload_file</span>
            </div>
            <h3 className="text-base font-bold text-white mb-1 relative z-10">
              Drop &amp; Index Documents
            </h3>
            <p className="text-zinc-500 text-xs mb-5 relative z-10 max-w-[200px]">
              PDF · Lecture Audio · Research Papers
            </p>

            {/* Two upload buttons */}
            <div className="flex gap-3 relative z-10">
              <button
                onClick={() => sendInput('index document from storage')}
                className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/10
                            border border-white/15 text-xs text-white
                            hover:bg-white/15 active:scale-95 transition-all"
              >
                <span className="material-symbols-outlined text-sm">folder_open</span>
                Browse Storage
              </button>
              <button
                onClick={() => sendInput('connect google drive')}
                className="flex items-center gap-2 px-4 py-2 rounded-full bg-white/10
                            border border-white/15 text-xs text-white
                            hover:bg-white/15 active:scale-95 transition-all"
              >
                <span className="material-symbols-outlined text-sm">cloud_sync</span>
                Connect Drive
              </button>
            </div>
          </div>

          {/* Flashcard widget */}
          <div className="apple-glass border border-white/8 rounded-[28px] p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="material-symbols-outlined text-tertiary text-sm">style</span>
                <span className="text-xs uppercase tracking-widest font-bold text-zinc-200">
                  Active Flashcards
                </span>
              </div>
              <span className="text-[9px] text-tertiary font-bold px-2 py-0.5 rounded-full
                                bg-tertiary/10 border border-tertiary/20 uppercase tracking-widest">
                84 due
              </span>
            </div>
            <div className="bg-zinc-800/40 p-4 rounded-2xl border border-white/5">
              <p className="text-sm text-zinc-200 leading-relaxed italic mb-3">
                {FLASHCARD.question}
              </p>
              {showAnswer ? (
                <div className="border-t border-white/10 pt-3">
                  <p className="text-sm text-white leading-relaxed">
                    {FLASHCARD.answer}
                  </p>
                  <button
                    onClick={() => setShowAnswer(false)}
                    className="mt-2 text-[10px] text-zinc-500 uppercase tracking-widest
                                hover:text-white transition-colors"
                  >
                    Next card →
                  </button>
                </div>
              ) : (
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-zinc-600">Subject: {FLASHCARD.subject}</span>
                  <button
                    onClick={() => setShowAnswer(true)}
                    className="text-tertiary text-[10px] font-bold uppercase tracking-widest
                                hover:text-tertiary/80 transition-colors"
                  >
                    Reveal Answer
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── Right Column ────────────────────────────────────────── */}
        <div className="col-span-12 lg:col-span-7 space-y-5">

          {/* RAG Stats grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="apple-glass border border-white/8 rounded-[24px] p-5">
              <span className="text-[10px] uppercase tracking-widest text-zinc-500">Contextual Tokens</span>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-3xl font-black text-white">1.2M</span>
                <span className="text-[10px] text-tertiary">+14%</span>
              </div>
              <div className="w-full bg-zinc-800 h-0.5 mt-3 rounded-full overflow-hidden">
                <div className="bg-primary h-full w-3/4 shadow-[0_0_8px_#c6c6c8]" />
              </div>
            </div>
            <div className="apple-glass border border-white/8 rounded-[24px] p-5">
              <span className="text-[10px] uppercase tracking-widest text-zinc-500">Semantic Links</span>
              <div className="flex items-baseline gap-2 mt-2">
                <span className="text-3xl font-black text-white">8,402</span>
              </div>
              <div className="w-full bg-zinc-800 h-0.5 mt-3 rounded-full overflow-hidden">
                <div className="bg-tertiary h-full w-1/2 shadow-[0_0_8px_#ffdd79]" />
              </div>
            </div>
          </div>

          {/* Generated Notebooks */}
          <div className="apple-glass border border-white/8 rounded-[32px] p-6">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-base font-bold text-white">Generated Notebooks</h3>
              <button className="text-zinc-600 hover:text-zinc-300 transition-colors">
                <span className="material-symbols-outlined text-sm">filter_list</span>
              </button>
            </div>

            <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
              {MOCK_NOTEBOOKS.map(nb => (
                <div
                  key={nb.id}
                  className="group flex items-center gap-4 p-3 rounded-2xl
                              hover:bg-white/5 transition-all duration-200
                              border border-transparent hover:border-white/8 cursor-pointer"
                >
                  <div className="w-10 h-10 rounded-xl bg-zinc-800/60 flex items-center justify-center
                                   text-zinc-300 group-hover:scale-110 transition-transform flex-shrink-0
                                   border border-white/5">
                    <span className="material-symbols-outlined text-sm">{nb.icon}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start mb-0.5">
                      <h4 className="text-xs font-bold text-white truncate pr-4">{nb.title}</h4>
                      <span className="text-[9px] text-zinc-600 font-mono flex-shrink-0">{nb.time}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] text-zinc-500">{nb.meta}</span>
                      <span className="w-1 h-1 rounded-full bg-zinc-700" />
                      <span className={`text-[10px] ${nb.tagColor}`}>{nb.tag}</span>
                    </div>
                  </div>
                  <span className="material-symbols-outlined text-zinc-700
                                    opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 text-sm">
                    chevron_right
                  </span>
                </div>
              ))}

              {jarvisNotebooks.map((cmd, i) => (
                <div key={`j-${i}`}
                     className="flex items-center gap-4 p-3 rounded-2xl
                                 border border-tertiary/15 bg-tertiary/5">
                  <div className="w-10 h-10 rounded-xl bg-tertiary/10 flex items-center
                                   justify-center flex-shrink-0 border border-tertiary/20">
                    <span className="material-symbols-outlined text-tertiary text-sm">auto_awesome</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="text-xs font-bold text-white truncate">{cmd.input}</h4>
                    <p className="text-[10px] text-zinc-500">{cmd.response?.slice(0, 80)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* ── Bottom Dock ─────────────────────────────────────────────── */}
      <footer className="fixed bottom-0 left-16 right-0 z-40 px-8 pb-5 pointer-events-none">
        <div className="max-w-2xl mx-auto pointer-events-auto">
          <div className="apple-glass rounded-[40px] border border-white/8 shadow-2xl
                           flex items-center gap-4 px-6 py-4">
            <span className="material-symbols-outlined text-zinc-600 flex-shrink-0">school</span>
            <input
              value={inputVal}
              onChange={e => setInputVal(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') handleSend() }}
              disabled={loading}
              placeholder="Studia, esame, appunti..."
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
              {loading
                ? <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span>
                : <span className="material-symbols-outlined text-sm">send</span>
              }
            </button>
          </div>
        </div>
      </footer>
    </div>
  )
}
