# CHANGELOG

## v3.0 — 2026-04-01

### STT Upgrade (Module 1)
- **Replaced openai-whisper with faster-whisper** (CTranslate2 backend)
- Model: "small", device="cpu", compute_type="int8" — faster inference on CPU
- Language: Italian hardcoded, VAD filter enabled (min_silence_duration_ms=500)
- Singleton model load at startup — no repeated loading
- Updated `jarvis_listener.py` to use `jarvis_stt.transcribe_audio()`
- Updated `jarvis_voice_input.py` to use `jarvis_stt` module

### Wake Word Detection (Module 2)
- **New `jarvis_wakeword.py`** — openwakeword "hey_jarvis" model (ONNX)
- New states: `PASSIVE_LISTENING` → wake word → `ACTIVE_LISTENING` (10s timeout)
- Buffered processing: accumulates 1280-sample frames before inference
- **Optional**: falls back to continuous listening if openwakeword not installed
- Wake word suppressed during JARVIS speech (same flag as VAD suppression)
- Wired into `jarvis_agent_refactored.py` and `jarvis_listener.py`

### Home Automation (Module 3)
- **New `jarvis_home.py`** — Home Assistant REST API bridge
- Config: `config/home_assistant.json` (gitignored), token via `HA_TOKEN` env var
- Italian device aliases (e.g., "luce camera" → "light.bedroom")
- Actions: turn_on, turn_off, toggle, set_brightness, set_temperature, get_state, get_all_states
- **Optional**: gracefully disabled when HA not configured
- Wired into `jarvis_brain.py` with HOME_TRIGGERS (priority above recipe triggers)
- Created `config/home_assistant.example.json` template

### System Awareness (Module 4)
- **New `jarvis_system_eye.py`** — psutil-based context monitoring
- Detects active apps → infers context mode (developer/study/relax/busy/general)
- Time-of-day context (mattina/pranzo/pomeriggio/sera/notte)
- System stats: CPU, RAM, disk, battery
- High resource warnings (CPU >80%, RAM >85%)
- Context summary dynamically injected into Ollama system prompt via `_build_system_prompt()`

### Tests (Module 5)
- **61 new tests** (136 total, all mocked):
  - `test_stt.py` — 10 tests: model loading, singleton, transcription, int16→float32, Italian config
  - `test_wakeword.py` — 9 tests: unavailable fallback, detection threshold, buffering, reset
  - `test_home.py` — 19 tests: config, env var token, aliases, turn_on/off, brightness, state, singleton
  - `test_system_eye.py` — 17 tests: apps, stats, time context, mode detection, summary, warnings
  - Updated `test_integration.py` — 6 new tests: wakeword→command, HA pipeline, STT pipeline

### Configuration (Module 6)
- Updated `requirements.txt`: replaced `openai-whisper` with `faster-whisper>=1.0.0`, added `openwakeword>=0.6.0`
- Updated `.gitignore`: added `config/home_assistant.json`, `~/.cache/huggingface/`
- Fixed routing: HOME_TRIGGERS checked before RECIPE_TRIGGERS (prevents fuzzy false positives)
- Updated `test_config.py`: import map updated for faster-whisper

## v2.1 — 2026-03-31

### Critical Fixes

**Barge-in self-interruption (FIX 1)**
- Added `set_suppressed()` to `SmartVAD` — raises detection threshold by 3.5x when JARVIS is speaking
- Removed `min(1.0)` cap from `_EnergyBackend.is_speech()` so threshold multiplication works
- Added suppression state tracking in `JarvisListener` audio callback: detects when JARVIS starts/stops speaking
- Added 300ms post-speech cooldown with VAD reset to flush buffered speaker bleed
- Added `[VAD_SUPPRESSED]` debug logging for diagnostics
- Real human barge-in still works at loud volume (exceeds 3.5x threshold)

**Command recognition pipeline (FIX 2)**
- Added `JARVIS_SYSTEM_PROMPT` — JARVIS persona injected into every Ollama call
- Added fuzzy matching via `thefuzz` for finance and recipe trigger phrases
- Fixed "stato" keyword conflict — system info now requires "stato sistema" (not bare "stato")
- Added NLU fallback: unmatched input routes to Ollama as last resort
- Added `[BRAIN]` logging for unmatched intents

**Thread safety & shutdown (FIX 3)**
- Added `signal.SIGINT`/`SIGTERM` handler for graceful shutdown
- Added `threading.Lock` to `memory_manager.py` for concurrent read/write safety
- All threads already use `daemon=True` — verified no orphan threads

**Finance engine integration (FIX 4)**
- Rewrote `finance_engine.py` from 2-line stub to full module
- JSON persistence in `config/finances.json`
- Functions: `check_gap()`, `get_report()`, `update_finances()`, `add_income()`
- Integrated into `jarvis_brain.py` with trigger phrases: "situazione affitto", "come sto con l'affitto", "report finanziario", "quanto manca per l'affitto"

**Code quality (FIX 5)**
- Replaced `hash()` with `hashlib.md5()` in audio cache (deterministic across sessions)
- Replaced all bare `except:` with `except Exception:` across codebase
- Added `flask` to `requirements.txt` (was missing for `alexa_server.py`)
- Fixed `jarvis_config.py`: added `config_dir`, `get_voice()`, `get_local_model()`, `get_cloud_model()`
- Fixed `jarvis_control.py`: added `get_app_list()`, `get_website_list()` for dashboard
- Fixed `dashboard.py`: all broken imports and missing method calls resolved
- Security audit: no hardcoded API keys found

### New Files
- `tests/` — Full pytest test suite (75 tests, all audio mocked)
  - `test_finance_engine.py` — Gap calculation, persistence, edge cases
  - `test_intent_matching.py` — Command routing, fuzzy matching, Italian variations
  - `test_vad_barge_in.py` — Suppression, cooldown, loud barge-in, energy backend
  - `test_config.py` — Secrets scan, UTF-8 validation, requirements completeness
  - `test_voice.py` — TTS generation, stop_event, ducking, hash determinism
  - `test_integration.py` — Full pipeline, state machine, startup, barge-in abort
- `requirements-dev.txt` — pytest, pytest-cov, pytest-mock
- `CHANGELOG.md` — This file
