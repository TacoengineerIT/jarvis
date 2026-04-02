/**
 * useJARVIS.js — HTTP Polling Only (NO WebSocket)
 * Simple, reliable, works on Windows
 */

import { useCallback, useEffect, useState } from 'react'

const API_URL = 'http://localhost:5000'

const DEFAULT_STATE = {
  jarvis_state: 'LISTENING',
  mood: '😐',
  mood_score: 5.0,
  user_input: '',
  response: '',
  timestamp: new Date().toISOString(),
  last_5_commands: [],
  api_cost_today: 0.0,
  today_spent: 0.0,
  next_event: null,
  briefing: '',
  budget_alerts: [],
}

export function useJARVIS() {
  const [state, setState] = useState(DEFAULT_STATE)
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // HTTP Polling — aggiorna stato ogni 500ms
  useEffect(() => {
    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`${API_URL}/api/state`, {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
        })

        if (!res.ok) throw new Error(`HTTP ${res.status}`)

        const data = await res.json()
        setState(prev => ({
          ...prev,
          ...data,
        }))

        if (!connected) {
          setConnected(true)
          setError(null)
          console.log('✅ Connected to JARVIS (HTTP polling)')
        }
      } catch (err) {
        console.error('❌ Poll error:', err)
        setConnected(false)
        setError(err.message)
      }
    }, 500)

    return () => clearInterval(pollInterval)
  }, [connected])

  // Invia input al backend
  const sendInput = useCallback((text) => {
    text = text?.trim()
    if (!text) return

    setLoading(true)
    setState(prev => ({
      ...prev,
      user_input: text,
      jarvis_state: 'PROCESSING',
    }))

    fetch(`${API_URL}/api/input`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    })
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(data => {
        if (data.error) {
          setError(data.error)
          setLoading(false)
        } else {
          setState(prev => ({
            ...prev,
            response: data.response,
            mood: data.mood || prev.mood,
            mood_score: data.mood_score || prev.mood_score,
            jarvis_state: data.jarvis_state || 'LISTENING',
          }))
          setError(null)
          setLoading(false)
        }
      })
      .catch(err => {
        console.error('❌ Send error:', err)
        setError(err.message)
        setLoading(false)
      })
  }, [])

  return { state, connected, loading, error, sendInput }
}

// Helper functions
export const getStateEmoji = (state) => {
  const map = {
    'LISTENING':  '💤',
    'ACTIVE':     '🔴',
    'RECORDING':  '🎙️',
    'PROCESSING': '⚙️',
    'SPEAKING':   '🔊',
    'COOLDOWN':   '⏱️',
    'ERROR':      '❌',
  }
  return map[state] || '❓'
}

export const getMoodEmoji = (mood) => {
  // Se mood è già un emoji, ritorna
  if (mood && mood.length === 2) return mood

  // Altrimenti mappa dal nome
  const map = {
    'happy':     '😊',
    'excited':   '🤩',
    'calm':      '😌',
    'neutral':   '😐',
    'tired':     '😴',
    'anxious':   '😰',
    'stressed':  '😤',
    'sad':       '😢',
    'angry':     '😠',
    'depressed': '😞',
  }
  return map[mood] || '😐'
}

export const getMoodColor = (mood) => {
  const map = {
    happy:     'text-tertiary',
    excited:   'text-tertiary',
    calm:      'text-primary',
    neutral:   'text-on-surface-variant',
    tired:     'text-secondary',
    anxious:   'text-error',
    stressed:  'text-error',
    sad:       'text-primary-dim',
    angry:     'text-error',
    depressed: 'text-error-dim',
  }
  return map[mood] || 'text-on-surface-variant'
}

export const getStateLabel = (state) => {
  const map = {
    'LISTENING':  'In ascolto',
    'RECORDING':  'Registrazione',
    'PROCESSING': 'Elaborazione',
    'SPEAKING':   'Risposta',
    'COOLDOWN':   'Attesa',
  }
  return map[state] || state
}
