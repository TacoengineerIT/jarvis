import { useState, useRef, useEffect } from 'react'
import { useJARVIS, getStateEmoji, getMoodEmoji, getStateLabel } from './hooks/useJARVIS'

export default function App() {
  const jarvis = useJARVIS()
  const [inputText, setInputText] = useState('')
  const [scrollY, setScrollY] = useState(0)
  const messagesEndRef = useRef(null)

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [jarvis.state.conversation_history])

  // Track scroll for dynamic saturation
  useEffect(() => {
    const handleScroll = (e) => setScrollY(e.target.scrollTop || 0)
    window.addEventListener('scroll', handleScroll, true)
    return () => window.removeEventListener('scroll', handleScroll, true)
  }, [])

  // Handle text input (Enter key)
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && inputText.trim() && !jarvis.loading) {
      jarvis.sendInput(inputText)
      setInputText('')
    }
  }

  // Handle voice input
  const handleVoiceClick = async () => {
    try {
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition
      if (!SR) {
        alert('Speech Recognition not supported in this browser')
        return
      }

      const recognition = new SR()
      recognition.lang = 'it-IT'

      await jarvis.triggerWakeWord()

      recognition.onstart = () => console.log('🎤 Listening...')

      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(r => r[0].transcript)
          .join('')
        if (transcript.trim()) {
          jarvis.sendInput(transcript)
        }
      }

      recognition.onerror = (event) => {
        console.error('Speech error:', event.error)
      }

      recognition.start()
    } catch (err) {
      console.error('Voice error:', err)
    }
  }

  const saturation = Math.max(60, 100 - scrollY * 0.3)

  return (
    <div
      className="w-screen h-screen bg-black text-white flex flex-col overflow-hidden"
      style={{ filter: `saturate(${saturation}%)` }}
    >
      {/* Connection Status */}
      {!jarvis.connected && (
        <div className="bg-red-900/80 text-red-100 px-4 py-2 text-center text-sm flex-shrink-0">
          ❌ {jarvis.error || 'Connecting...'}
        </div>
      )}

      {/* Header */}
      <div className="text-center py-4 border-b border-gray-700 flex-shrink-0">
        <h1 className="text-3xl font-bold tracking-widest">J.A.R.V.I.S. V4.0</h1>
        <p className="text-xs text-gray-400 mt-1">
          {jarvis.connected ? '🟢 LIVE' : '🔴 OFFLINE'} — Liquid Intelligence
        </p>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mood + State */}
        <div className="py-8 text-center border-b border-gray-700 flex-shrink-0">
          <div className="relative w-48 h-48 mx-auto mb-4">
            <div className="absolute inset-0 bg-gradient-to-br from-gray-400 to-gray-600 rounded-full shadow-2xl flex items-center justify-center">
              <div className="text-7xl">{getMoodEmoji(jarvis.state.mood)}</div>
            </div>
          </div>
          <div className="text-2xl font-bold mb-2">{getStateEmoji(jarvis.state.jarvis_state)}</div>
          <div className="text-lg text-gray-300">{getStateLabel(jarvis.state.jarvis_state)}</div>
          <div className="text-sm text-gray-500">Mood: {jarvis.state.mood_score.toFixed(1)}/10</div>
        </div>

        {/* Conversation History (Scrollable) */}
        <div className="flex-1 overflow-y-auto px-8 py-6 space-y-4">
          {jarvis.state.conversation_history.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              📭 No messages yet. Start chatting...
            </div>
          ) : (
            jarvis.state.conversation_history.map((msg, idx) => (
              <div key={idx} className="space-y-2">
                {/* User */}
                <div className="flex justify-end">
                  <div className="max-w-xs bg-blue-900/40 rounded-lg px-4 py-2">
                    <p className="text-sm text-gray-300">{msg.user}</p>
                  </div>
                </div>
                {/* JARVIS */}
                <div className="flex justify-start">
                  <div className="max-w-xs bg-gray-800/60 rounded-lg px-4 py-2">
                    <p className="text-sm text-white">{msg.response}</p>
                    <p className="text-xs text-gray-500 mt-1">{msg.mood}</p>
                  </div>
                </div>
              </div>
            ))
          )}

          {jarvis.loading && (
            <div className="text-center text-gray-400">⚙️ Processing...</div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Section */}
        <div className="border-t border-gray-700 p-6 bg-black/80 flex-shrink-0">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Scrivi a JARVIS..."
            disabled={jarvis.loading}
            className="w-full px-4 py-3 bg-gray-800 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none disabled:opacity-50"
          />

          <div className="flex gap-4 mt-4 justify-center">
            <button
              onClick={handleVoiceClick}
              disabled={jarvis.loading}
              className="w-14 h-14 rounded-full bg-gray-700 hover:bg-gray-600 disabled:opacity-50 flex items-center justify-center text-2xl transition"
              title="Voice Input"
            >
              🎤
            </button>
            <button
              className="w-14 h-14 rounded-full bg-gray-700 hover:bg-gray-600 flex items-center justify-center text-2xl transition"
              title="Settings"
            >
              ⚙️
            </button>
            <button
              className="w-14 h-14 rounded-full bg-gray-700 hover:bg-gray-600 flex items-center justify-center text-2xl transition"
              title="History"
            >
              📋
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-gray-700 px-8 py-3 bg-black/60 flex justify-between text-xs text-gray-500 flex-shrink-0">
        <div>💰 €{jarvis.state.api_cost_today.toFixed(4)}</div>
        <div>💵 €{jarvis.state.today_spent.toFixed(2)}</div>
        {jarvis.state.next_event && <div>📅 {jarvis.state.next_event}</div>}
        <div>{jarvis.connected ? '✅ Online' : '❌ Offline'}</div>
      </div>
    </div>
  )
}
