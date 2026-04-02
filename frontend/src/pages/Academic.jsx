/**
 * Academic.jsx — V5.5 Academic Hub
 * RAG Knowledge Hub: PDF upload zone, flashcard widget, RAG stats, notebooks list, bottom dock.
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
    tag: '12 Insights extracted',
    tagColor: 'text-tertiary',
    time: '14:02',
  },
  {
    id: 2,
    icon: 'auto_awesome',
    title: 'Market Economics — Master Case Study',
    meta: 'Refined via RAG augmentation',
    tag: '94% Confidence',
    tagColor: 'text-on-surface-variant',
    time: 'Yesterday',
  },
  {
    id: 3,
    icon: 'mic',
    title: 'Brainstorm: AI Safety Protocols',
    meta: 'Voice-to-Text conversion',
    tag: '32m 14s',
    tagColor: 'text-on-surface-variant',
    time: 'Oct 12',
  },
]

const FLASHCARD = {
  question: '"Explain the core principle of RAG (Retrieval-Augmented Generation)..."',
  answer:   'RAG combines retrieval of relevant documents with language generation, grounding responses in factual, up-to-date knowledge.',
  subject:  'Neural Arch',
}

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

  const ragTokens  = '1.2M'
  const ragLinks   = 8402

  // JARVIS-generated notebooks from recent academic commands
  const jarvisNotebooks = state.last_5_commands.filter(c =>
    c.input?.toLowerCase().match(/studia|esame|lezione|appunti|ripassa/)
  )

  return (
    <div className="bg-surface-container-lowest min-h-screen font-body text-on-surface
                    selection:bg-tertiary selection:text-on-tertiary overflow-x-hidden">

      {/* ── Main Content ──────────────────────────────────────────── */}
      <main className="pl-16 pt-24 pb-36 px-8 max-w-7xl mx-auto">

        {/* Hero header */}
        <div className="mb-10">
          <h2 className="text-4xl font-headline font-extrabold tracking-tight text-primary-fixed mb-1">
            Academic Hub
          </h2>
          <p className="text-on-surface-variant text-sm tracking-wide">
            ITS Bari — Unified Neural Indexing
          </p>
        </div>

        {/* Bento grid */}
        <div className="grid grid-cols-12 gap-6">

          {/* ── Left Column ─────────────────────────────────────────── */}
          <div className="col-span-12 lg:col-span-5 space-y-6">

            {/* Drop & Index */}
            <div
              onDragOver={e => { e.preventDefault(); setDragOver(true) }}
              onDragLeave={() => setDragOver(false)}
              onDrop={e => { e.preventDefault(); setDragOver(false) }}
              className={`glass-island border rounded-[32px] p-8 group
                          transition-all hover:bg-black/60 relative overflow-hidden
                          h-[320px] flex flex-col items-center justify-center text-center
                          ${dragOver ? 'border-tertiary/60 bg-tertiary/5' : 'border-outline-variant/10'}`}
            >
              {/* Background texture */}
              <div className="absolute inset-0 opacity-10 pointer-events-none
                              bg-gradient-to-br from-primary/20 to-transparent" />

              <div className="w-20 h-20 rounded-full bg-surface-container-high flex items-center
                               justify-center mb-6 border border-outline-variant/20
                               group-hover:scale-110 transition-transform duration-500">
                <span className="material-symbols-outlined text-primary text-3xl">upload_file</span>
              </div>
              <h3 className="text-xl font-headline font-bold text-primary-fixed mb-2 tracking-tight">
                Drop &amp; Index
              </h3>
              <p className="text-on-surface-variant text-sm max-w-[220px] mx-auto mb-7">
                Inject PDF, Lecture Audio, or Research Papers into the Knowledge Graph.
              </p>
              <button
                onClick={() => sendInput('index new document')}
                className="px-8 py-3 rounded-full bg-primary-fixed text-on-primary-fixed
                            font-bold text-xs uppercase tracking-widest
                            hover:scale-105 active:scale-95 transition-all"
              >
                Initialize Feed
              </button>
            </div>

            {/* Flashcard widget */}
            <div className="glass-island border border-outline-variant/10 rounded-[32px] p-6">
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-tertiary">style</span>
                  <span className="text-xs uppercase tracking-[0.15em] font-bold text-[#e2e2e4]">
                    Active Flashcards
                  </span>
                </div>
                <span className="text-[10px] text-tertiary font-bold px-2 py-0.5 rounded-full bg-tertiary/10">
                  84 Due
                </span>
              </div>
              <div className="bg-surface-container-high/50 p-4 rounded-2xl border border-outline-variant/5">
                <p className="text-sm font-medium text-on-surface leading-relaxed italic mb-3">
                  {FLASHCARD.question}
                </p>
                {showAnswer ? (
                  <div className="border-t border-outline-variant/20 pt-3">
                    <p className="text-sm text-primary-fixed leading-relaxed">
                      {FLASHCARD.answer}
                    </p>
                    <button
                      onClick={() => setShowAnswer(false)}
                      className="mt-2 text-[10px] text-on-surface-variant uppercase tracking-widest
                                  hover:text-primary transition-colors"
                    >
                      Next card →
                    </button>
                  </div>
                ) : (
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] text-on-surface-variant">
                      Subject: {FLASHCARD.subject}
                    </span>
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
          <div className="col-span-12 lg:col-span-7 space-y-6">

            {/* RAG Stats */}
            <div className="grid grid-cols-2 gap-4">
              <div className="glass-island border border-outline-variant/10 rounded-3xl p-5 flex flex-col justify-between">
                <span className="text-[10px] uppercase tracking-widest text-on-surface-variant">
                  Contextual Tokens
                </span>
                <div className="flex items-baseline gap-2 mt-2">
                  <span className="text-3xl font-black text-primary-fixed">{ragTokens}</span>
                  <span className="text-[10px] text-tertiary">+14%</span>
                </div>
                <div className="w-full bg-surface-variant h-0.5 mt-4 rounded-full overflow-hidden">
                  <div className="bg-primary h-full w-3/4 shadow-[0_0_8px_#c6c6c8]" />
                </div>
              </div>
              <div className="glass-island border border-outline-variant/10 rounded-3xl p-5 flex flex-col justify-between">
                <span className="text-[10px] uppercase tracking-widest text-on-surface-variant">
                  Semantic Links
                </span>
                <div className="flex items-baseline gap-2 mt-2">
                  <span className="text-3xl font-black text-primary-fixed">
                    {ragLinks.toLocaleString()}
                  </span>
                </div>
                <div className="w-full bg-surface-variant h-0.5 mt-4 rounded-full overflow-hidden">
                  <div className="bg-tertiary h-full w-1/2 shadow-[0_0_8px_#ffdd79]" />
                </div>
              </div>
            </div>

            {/* Generated Notebooks */}
            <div className="glass-island border border-outline-variant/10 rounded-[32px] p-8">
              <div className="flex items-center justify-between mb-7">
                <h3 className="text-lg font-headline font-bold text-primary-fixed tracking-tight">
                  Generated Notebooks
                </h3>
                <button className="text-on-surface-variant hover:text-primary transition-colors">
                  <span className="material-symbols-outlined">filter_list</span>
                </button>
              </div>

              <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
                {MOCK_NOTEBOOKS.map(nb => (
                  <div
                    key={nb.id}
                    className="group flex items-center gap-5 p-4 rounded-2xl
                                hover:bg-surface-container-high transition-all duration-300
                                border border-transparent hover:border-outline-variant/20
                                cursor-pointer"
                  >
                    <div className="w-12 h-12 rounded-xl bg-surface-container flex items-center
                                     justify-center text-primary group-hover:scale-110 transition-transform
                                     flex-shrink-0">
                      <span className="material-symbols-outlined">{nb.icon}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-start mb-1">
                        <h4 className="text-sm font-bold text-primary-fixed tracking-wide truncate pr-4">
                          {nb.title}
                        </h4>
                        <span className="text-[10px] text-on-surface-variant font-mono flex-shrink-0">
                          {nb.time}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] text-on-surface-variant">{nb.meta}</span>
                        <span className="w-1 h-1 rounded-full bg-outline-variant" />
                        <span className={`text-[11px] ${nb.tagColor}`}>{nb.tag}</span>
                      </div>
                    </div>
                    <span className="material-symbols-outlined text-on-surface-variant
                                      opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                      chevron_right
                    </span>
                  </div>
                ))}

                {/* JARVIS-generated from recent academic commands */}
                {jarvisNotebooks.map((cmd, i) => (
                  <div key={`j-${i}`}
                       className="flex items-center gap-5 p-4 rounded-2xl
                                   border border-tertiary/10 bg-tertiary/5">
                    <div className="w-12 h-12 rounded-xl bg-tertiary/10 flex items-center
                                     justify-center flex-shrink-0">
                      <span className="material-symbols-outlined text-tertiary">auto_awesome</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-bold text-primary-fixed truncate">{cmd.input}</h4>
                      <p className="text-[11px] text-on-surface-variant">{cmd.response?.slice(0, 80)}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* ── Bottom Dock ─────────────────────────────────────────────── */}
      <footer className="fixed bottom-0 left-16 right-0 z-40 px-8 pb-6 pointer-events-none">
        <div className="max-w-4xl mx-auto w-full pointer-events-auto">
          <div className="glass-island rounded-[40px] p-1 border border-[#484848]/20 shadow-2xl
                           flex items-center gap-4 bg-black/60">
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
              disabled={loading}
              placeholder="Instruct J.A.R.V.I.S. or dictate notes..."
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
                            hover:scale-105 active:scale-95 transition-all disabled:opacity-40"
              >
                {loading
                  ? <span className="material-symbols-outlined text-base animate-spin">progress_activity</span>
                  : <span className="material-symbols-outlined icon-filled text-base">mic</span>
                }
              </button>
            </div>
          </div>

          {/* Footer icon row */}
          <div className="flex justify-center items-center gap-20 py-4">
            <span className="material-symbols-outlined text-tertiary drop-shadow-[0_0_8px_rgba(255,221,121,0.5)] cursor-pointer">
              mic_none
            </span>
            <span className="material-symbols-outlined text-[#454749] hover:text-[#c6c6c8] transition-colors cursor-pointer">
              graphic_eq
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}
