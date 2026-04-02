import { useCallback, useEffect, useState } from 'react'

const API_URL = 'http://localhost:5000'

const DEFAULT_STATE = {
  jarvis_state: 'LISTENING',
  mood: '😐',
  mood_score: 5.0,
  mood_trend: 'stable',
  user_input: '',
  response: '',
  timestamp: new Date().toISOString(),
  last_5_commands: [],
  conversation_history: [],
  api_cost_today: 0.0,
  today_spent: 0.0,
  next_event: null,
  briefing: '',
  budget_alerts: [],
  error: null
}

export function useJARVIS() {
  const [state, setState] = useState(DEFAULT_STATE)
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // HTTP Polling every 500ms
  useEffect(() => {
    const poll = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/state`)
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setState(data)
        if (!connected) {
          setConnected(true)
          setError(null)
        }
      } catch (err) {
        setConnected(false)
        setError(err.message)
      }
    }, 500)
    return () => clearInterval(poll)
  }, [connected])

  const sendInput = useCallback((text) => {
    text = text?.trim()
    if (!text) return
    setLoading(true)
    setState(prev => ({ ...prev, user_input: text, jarvis_state: 'PROCESSING' }))

    fetch(`${API_URL}/api/input`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    })
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          setError(data.error)
        } else {
          setState(prev => ({
            ...prev,
            response: data.response,
            mood: data.mood,
            mood_score: data.mood_score,
            jarvis_state: 'LISTENING',
            conversation_history: data.conversation_history,
          }))
          setError(null)
        }
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  const triggerWakeWord = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/wake`, { method: 'POST' })
      const data = await res.json()
      if (data.success) setState(prev => ({ ...prev, jarvis_state: 'ACTIVE' }))
    } catch (err) {
      console.error('Wake error:', err)
    }
  }, [])

  return { state, connected, loading, error, sendInput, triggerWakeWord }
}

export const getStateEmoji = (state) => {
  const map = {
    'LISTENING':  '💤',
    'RECORDING':  '🎙️',
    'PROCESSING': '⚙️',
    'SPEAKING':   '🔊',
    'ACTIVE':     '🔴',
    'COOLDOWN':   '⏱️',
    'ERROR':      '❌',
  }
  return map[state] || '❓'
}

export const getMoodEmoji = (mood) => mood && mood.length === 2 ? mood : '😐'

export const getMoodColor = (mood) => {
  const map = { '😊': 'text-tertiary', '😞': 'text-error', '😤': 'text-error' }
  return map[mood] || 'text-on-surface-variant'
}

export const getStateLabel = (state) => {
  const map = {
    'LISTENING':  'In ascolto',
    'RECORDING':  'Registrazione',
    'PROCESSING': 'Elaborazione',
    'SPEAKING':   'Risposta',
    'ACTIVE':     'Attivo',
    'COOLDOWN':   'Attesa',
  }
  return map[state] || state
}
