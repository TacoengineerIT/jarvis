# JARVIS v3.0 — Project Context

## Overview
Personal JARVIS-style AI assistant with continuous voice listening, wake word detection, PC control, home automation, system awareness, RAG system, and cinematic personality. Built on Windows (Intel i7-6700HQ, 16GB RAM, GTX 960M 4GB).

## Architecture

### Core Pipeline
```
Mic → sounddevice InputStream → float32→int16
  → Calibration (1s ambient noise) → VAD suppression check
  → WakeWordDetector (openwakeword "hey_jarvis") → PASSIVE→ACTIVE transition
  → SmartVAD.process_chunk() → on_speech_end(audio)
  → faster-whisper transcribe(audio, language="it") → on_transcript(text)
  → JarvisAgent._transcript_queue → _process_utterance()
  → jarvis_brain.process_input() → home/finance/recipe/action/ollama
  → SystemEye context → dynamic Ollama system prompt
  → jarvis_voice.say() → edge-tts subprocess → pygame playback
  → duck_music() ←→ restore_music()
```

### State Machine
```
[PASSIVE_LISTENING] → wake word → [ACTIVE_LISTENING] (10s timeout)
[ACTIVE_LISTENING] → voice detected → [LISTENING]
[LISTENING] → utterance complete → [PROCESSING] (STT + Brain routing)
[PROCESSING] → response ready → [SPEAKING] (TTS + ducking)
[SPEAKING] → TTS done → [ACTIVE_LISTENING] or [IDLE]
Any state → barge-in → [IDLE]
No wake word module → always [IDLE] (backward compatible)
```

### Modules
| File | Purpose |
|------|---------|
| `jarvis_agent_refactored.py` | Main agent: state machine, wake word + VAD listener loop, CLI fallback, signal handlers |
| `jarvis_brain.py` | Command routing: home/finance/recipe triggers (fuzzy), action verbs, Ollama LLM with SystemEye context |
| `jarvis_stt.py` | **NEW** faster-whisper STT: CTranslate2 backend, "small" model, int8 CPU, Italian, VAD filter |
| `jarvis_wakeword.py` | **NEW** openwakeword "hey_jarvis" detector, optional (falls back to continuous listening) |
| `jarvis_home.py` | **NEW** Home Assistant REST API bridge: device aliases, turn_on/off, brightness, temperature, state |
| `jarvis_system_eye.py` | **NEW** System awareness: active apps, CPU/RAM/battery, time context, mode detection (dev/study/relax) |
| `jarvis_voice.py` | Edge-TTS generation + pygame playback + music ducking, hashlib audio cache |
| `jarvis_listener.py` | Background mic thread → VAD → faster-whisper STT → transcript callback, suppression + cooldown |
| `jarvis_vad_smart.py` | VAD state machine: silero-vad or energy-based backend, suppression multiplier |
| `jarvis_voice_input.py` | CLI-mode STT input (faster-whisper, numpy array direct) |
| `jarvis_config.py` | Singleton config with dotted key access, get_voice(), get_local_model() |
| `jarvis_control.py` | PC automation: open apps, system info, app/website lists |
| `jarvis_rag.py` | RAG document search with ChromaDB (stub) |
| `finance_engine.py` | Rent gap tracker: JSON persistence, check_gap(), get_report(), update_finances() |
| `survival_recipes.py` | 10 Italian budget recipes, filtered by cost/time/tag |
| `memory_manager.py` | Conversation memory with thread-safe file locking |
| `alexa_server.py` | Flask endpoint for Alexa skill integration |
| `dashboard.py` | Streamlit UI control panel |

## Tech Stack
- Python 3.11, pygame, sounddevice, edge-tts, faster-whisper (CTranslate2)
- openwakeword (optional, for "hey_jarvis" wake word)
- Ollama local (llama3.1:8b), thefuzz for intent matching
- Home Assistant REST API (optional)
- psutil for system awareness
- ChromaDB, Sentence Transformers (RAG)
- Flask + ngrok for Alexa integration
- Streamlit for dashboard
- PowerShell terminal, venv at `.\venv\`

## Barge-in System
- **Problem solved**: JARVIS's own TTS audio was triggering the VAD via speaker→mic bleed
- **Fix**: `SmartVAD.set_suppressed(True)` raises the energy threshold by 3.5x during speech
- **Cooldown**: 300ms post-speech suppression prevents residual bleed from triggering
- **Real barge-in**: Very loud human voice close to mic (amplitude > 3.5x threshold) still passes
- **Debug logging**: `[VAD_SUPPRESSED]` messages when suppression activates/deactivates

## Wake Word System
- **Model**: openwakeword "hey_jarvis" (ONNX inference)
- **Flow**: PASSIVE_LISTENING → wake word detected → ACTIVE_LISTENING (10s timeout)
- **Optional**: If openwakeword not installed, falls back to continuous listening (no wake word needed)
- **Suppression**: Wake word detection is suppressed when JARVIS is speaking (same as VAD)

## Home Automation
- **Backend**: Home Assistant REST API (`/api/states`, `/api/services/{domain}/{service}`)
- **Config**: `config/home_assistant.json` (gitignored) — URL, token, device aliases
- **Token**: Prefer `HA_TOKEN` env var over config file
- **Aliases**: Italian device names → entity_id (e.g., "luce camera" → "light.bedroom")
- **Actions**: turn_on, turn_off, toggle, set_brightness, set_temperature, get_state, get_all_states
- **Optional**: Works without HA configured — commands gracefully fall through to other handlers

## System Awareness
- **Module**: `jarvis_system_eye.py` with psutil
- **Context modes**: developer, study, relax, busy, general — detected from running apps
- **Time context**: mattina, ora di pranzo, pomeriggio, sera, notte
- **Dynamic prompt**: SystemEye summary injected into Ollama system prompt for context-aware responses
- **Warnings**: High CPU (>80%) and high RAM (>85%) noted in context

## Command Recognition (routing priority)
1. **Finance triggers**: "situazione affitto", "report finanziario", "quanto manca" → fuzzy matched via thefuzz
2. **Home automation**: "accendi", "spegni", "luce", "temperatura" → HA bridge (if configured)
3. **Recipe triggers**: "cosa cucino", "ricetta", "fame" → fuzzy matched
4. **Action verbs**: "apri", "avvia", "lancia" + app name → tool use (subprocess/webbrowser)
5. **Questions**: Routed to Ollama with JARVIS persona + SystemEye context
6. **NLU fallback**: Unmatched input → Ollama as general fallback

## Testing
```bash
python -m pytest tests/ -v         # 136 tests, all mocked (no real audio)
python test_vad_system.py          # Legacy standalone VAD tests
python test_vad_system.py --mic    # + live mic test (optional)
```

## Coding Conventions
- Language: Italian for user-facing strings/TTS, English for code comments and variable names
- Personality: JARVIS addresses user as "Tony" or "Sir", British-butler style but in Italian
- Randomize responses — never use static/repetitive phrases
- All files must be UTF-8 encoded
- Voice: `it-IT-DiegoNeural` (Edge-TTS) — do NOT change
- Music: AC/DC "Back in Black" via pygame — do NOT remove

## FEATURES TO IMPLEMENT/COMPLETE
- Complete RAG system (`jarvis_rag.py`) with ChromaDB + Sentence Transformers for university PDFs
- Complete the Streamlit dashboard (currently functional but some pages are placeholders)
- Add proper logging instead of print statements
- Web search integration via duckduckgo-search
