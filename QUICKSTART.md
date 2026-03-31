# JARVIS - Quick Start Guide

**Personal AI Assistant per Antonio (Tony)**  
Versione v1.1 — offline-first, voice + Ollama + memoria

---

## Avvio rapido

```bash
# 1. Attiva l'ambiente virtuale
cd C:\Users\A1600apulia\Desktop\jarvis_scuola
.\venv\Scripts\activate

# 2. (Prima volta) Installa dipendenze
pip install -r requirements.txt

# 3. (Prima volta) Scarica modello Whisper
python -c "import whisper; whisper.load_model('base')"

# 4. Avvia Ollama in background
ollama serve   # oppure usa il systray se Ollama Desktop è installato
ollama pull llama3.1:8b

# 5. Avvia JARVIS
python jarvis_agent_refactored.py
```

---

## Comandi principali

| Comando | Azione |
|---------|--------|
| `voce` | Attiva microfono (5 sec) |
| `muto` | Toggle output vocale |
| `status` | Mostra stato sistemi |
| `help` | Lista comandi |
| `exit` | Chiudi JARVIS |
| `apri chrome` | Apre Chrome |
| `apri spotify` / `youtube` / `notepad` | App launcher |
| `screenshot` | Cattura schermata Desktop |
| `cpu` / `ram` | Info sistema |
| `affitto` / `finanze` | Stato budget (gap 110€) |
| `ricetta` / `ricetta con 2 euro` | Suggerisce ricetta economica |
| `crea file con [testo]` | Salva file in Desktop/JARVIS_Files/ |
| *Qualsiasi domanda* | Risponde Ollama (llama3.1:8b) |

---

## Architettura

```
Tony (testo o voce)
    │
    ▼
jarvis_agent_refactored.py   ← Main loop
    │
    ├── jarvis_brain.py       ← Routing intelligente
    │       ├── Comandi → execute_action() (tools diretti)
    │       └── Domande → ask_ollama() (llama3.1:8b)
    │
    ├── jarvis_voice.py       ← Output TTS (edge-tts, DiegoNeural)
    ├── jarvis_voice_input.py ← Input mic (Whisper base, no FFmpeg)
    ├── memory_manager.py     ← Persistenza scambi (memory.json)
    └── survival_recipes.py  ← Database ricette economiche
```

---

## Troubleshooting

### Ollama non risponde
```bash
ollama serve          # avvia il server
ollama list           # verifica llama3.1:8b è installato
ollama pull llama3.1:8b
```
JARVIS funziona anche senza Ollama (modalità tool-only).

### FFmpeg mancante (Whisper warning)
Non è necessario! Il modulo voice usa numpy array direttamente.  
Per installarlo comunque:
```bash
# Scoop
scoop install ffmpeg

# Chocolatey
choco install ffmpeg
```

### Microfono non rilevato
JARVIS chiede automaticamente input testo come fallback.  
Verifica il microfono in Impostazioni → Sistema → Audio.

### edge-tts non funziona
```bash
pip install edge-tts --upgrade
```
JARVIS stampa il testo su console anche senza TTS.

### Memory corrotta
```bash
python -c "from memory_manager import clear_memory; clear_memory()"
```

### Dipendenza mancante
```bash
pip install -r requirements.txt
```

---

## File principali

| File | Descrizione |
|------|-------------|
| `jarvis_agent_refactored.py` | Entry point principale |
| `jarvis_brain.py` | Routing AI + tool use |
| `jarvis_voice_input.py` | Trascrizione vocale (Whisper) |
| `jarvis_voice.py` | Sintesi vocale (edge-tts) |
| `memory_manager.py` | Memoria persistente |
| `survival_recipes.py` | Ricette italiane economiche |
| `config/jarvis_config.json` | Configurazione globale |
| `config/finances.json` | Budget (target: 110€) |
| `memory.json` | Ultimi 20 scambi (auto-creato) |
| `Desktop/JARVIS_Files/` | File creati da JARVIS |

---

## Roadmap

- [ ] Alexa skill integration (port 5000)
- [ ] Dashboard Streamlit write controls
- [ ] Web search via DuckDuckGo
- [ ] Integrazione calendario universitario
- [ ] Mobile app (iOS/Android)
