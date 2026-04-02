import { useRef, useState } from 'react'
import WaveformAnimation from './WaveformAnimation.jsx'

export default function CommandInput({ onSend, loading = false, jarvisState = 'LISTENING' }) {
  const [value, setValue] = useState('')
  const inputRef = useRef(null)

  const handleSend = () => {
    if (!value.trim() || loading) return
    onSend(value.trim())
    setValue('')
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const isVoiceActive = ['RECORDING', 'SPEAKING'].includes(jarvisState)

  return (
    <div className="glass-island rounded-[40px] border border-[#484848]/20 shadow-2xl
                    flex items-center gap-4 bg-black/60">
      {/* Left: add icon */}
      <div className="flex items-center gap-2 pl-4">
        <button
          className="w-10 h-10 rounded-full flex items-center justify-center
                     text-primary-fixed hover:bg-white/10 transition-all"
          title="Attach"
        >
          <span className="material-symbols-outlined">add</span>
        </button>
        <div className="h-6 w-px bg-outline-variant/30" />
      </div>

      {/* Input field */}
      <div className="flex-1">
        <input
          ref={inputRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKey}
          disabled={loading}
          placeholder="Instruct J.A.R.V.I.S. or type a command..."
          className="w-full bg-transparent border-none focus:outline-none focus:ring-0
                     text-sm text-on-surface placeholder:text-on-surface-variant/60
                     disabled:opacity-50 py-4"
        />
      </div>

      {/* Right: waveform + send button */}
      <div className="flex items-center gap-4 pr-4">
        {isVoiceActive && (
          <WaveformAnimation active={isVoiceActive} />
        )}
        <button
          onClick={handleSend}
          disabled={loading || !value.trim()}
          className="w-12 h-12 rounded-full bg-primary-fixed text-on-primary-fixed
                     flex items-center justify-center
                     shadow-[0_0_20px_rgba(198,198,200,0.3)]
                     hover:scale-105 active:scale-95 transition-all
                     disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? (
            <span className="material-symbols-outlined animate-spin text-base">progress_activity</span>
          ) : (
            <span className="material-symbols-outlined icon-filled text-base">mic</span>
          )}
        </button>
      </div>
    </div>
  )
}
