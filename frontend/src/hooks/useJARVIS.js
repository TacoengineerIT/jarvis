/**
 * useJARVIS — React hook for real-time JARVIS WebSocket connection.
 *
 * Returns:
 *   state       — full JARVIS state object (mood, user_input, response, ...)
 *   connected   — WebSocket connected?
 *   loading     — processing a command?
 *   error       — last error string or null
 *   sendInput   — (text: string) => void
 *   reconnect   — () => void  force reconnect
 */

import { useCallback, useEffect, useRef, useState } from 'react'

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8765/ws'

const DEFAULT_STATE = {
  jarvis_state:    'LISTENING',
  mood:            'neutral',
  mood_score:      5.0,
  mood_trend:      'stable',
  user_input:      '',
  response:        '',
  timestamp:       '',
  last_5_commands: [],
  api_cost_today:  0.0,
  today_spent:     0.0,
  next_event:      null,
  briefing:        'Connessione al sistema in corso...',
  budget_alerts:   [],
}

export function useJARVIS() {
  const [state, setState]       = useState(DEFAULT_STATE)
  const [connected, setConnected] = useState(false)
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState(null)

  const wsRef       = useRef(null)
  const retryTimer  = useRef(null)
  const retryCount  = useRef(0)
  const MAX_RETRIES = 10

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    try {
      const ws = new WebSocket(WS_URL)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        setError(null)
        retryCount.current = 0
        console.info('[JARVIS WS] Connected')
      }

      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data)
          if (msg.type === 'state') {
            setState(prev => ({ ...prev, ...msg }))
            if (msg.jarvis_state === 'LISTENING') setLoading(false)
            if (msg.jarvis_state === 'PROCESSING') setLoading(true)
          }
        } catch {
          // ignore malformed messages
        }
      }

      ws.onclose = () => {
        setConnected(false)
        setLoading(false)
        if (retryCount.current < MAX_RETRIES) {
          const delay = Math.min(1000 * 2 ** retryCount.current, 30000)
          retryCount.current += 1
          retryTimer.current = setTimeout(connect, delay)
          console.warn(`[JARVIS WS] Reconnecting in ${delay}ms (attempt ${retryCount.current})`)
        } else {
          setError('Connessione persa. Riavvia il server JARVIS.')
        }
      }

      ws.onerror = () => {
        setError('Errore WebSocket — server non raggiungibile')
      }
    } catch (e) {
      setError(`Impossibile connettersi: ${e.message}`)
    }
  }, [])

  // Connect on mount, cleanup on unmount
  useEffect(() => {
    connect()
    return () => {
      clearTimeout(retryTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  const sendInput = useCallback((text) => {
    text = text?.trim()
    if (!text) return
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'input', text }))
      setLoading(true)
      setState(prev => ({ ...prev, user_input: text, jarvis_state: 'PROCESSING' }))
    } else {
      // Fallback: HTTP POST
      fetch('/api/input', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ text }),
      }).catch(e => setError(`HTTP fallback failed: ${e.message}`))
      setLoading(true)
    }
  }, [])

  const reconnect = useCallback(() => {
    retryCount.current = 0
    clearTimeout(retryTimer.current)
    wsRef.current?.close()
    connect()
  }, [connect])

  return { state, connected, loading, error, sendInput, reconnect }
}

// ── Helpers (exported for use in components) ──────────────────────

export function getStateEmoji(jarvisState) {
  const map = {
    LISTENING:  '💤',
    ACTIVE:     '👂',
    RECORDING:  '🎙️',
    PROCESSING: '⚙️',
    SPEAKING:   '🔊',
    COOLDOWN:   '⏱️',
  }
  return map[jarvisState] || '❓'
}

export function getStateLabel(jarvisState) {
  const map = {
    LISTENING:  'In ascolto',
    ACTIVE:     'Attivo',
    RECORDING:  'Registrazione',
    PROCESSING: 'Elaborazione',
    SPEAKING:   'Risposta',
    COOLDOWN:   'Attesa',
  }
  return map[jarvisState] || jarvisState
}

export function getMoodEmoji(mood) {
  const map = {
    happy:     '😊',
    excited:   '🤩',
    calm:      '😌',
    neutral:   '😐',
    tired:     '😴',
    anxious:   '😰',
    stressed:  '😤',
    sad:       '😢',
    angry:     '😠',
    depressed: '😞',
  }
  return map[mood] || '😐'
}

export function getMoodColor(mood) {
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
