# JARVIS v2 — Master Fix & Test Prompt for Claude Code
# Copia e incolla questo in Claude Code dopo aver fatto `cd` nella cartella del progetto

"""
Read CLAUDE.md and every .py file in this project. Then execute this plan in order:

═══════════════════════════════════════════════
PHASE 1: DIAGNOSTIC SCAN
═══════════════════════════════════════════════

1. List every .py file with a 1-line description of what it does
2. Map the full audio pipeline: mic input → VAD → STT → intent parse → action → TTS → speaker
3. Identify all external dependencies (pip packages) and verify they're in requirements.txt
4. Flag any hardcoded API keys, secrets, file paths that should be in config
5. Check every file for UTF-8 encoding issues

═══════════════════════════════════════════════
PHASE 2: CRITICAL FIXES
═══════════════════════════════════════════════

FIX 1 — BARGE-IN SELF-INTERRUPTION (if not already fixed):
- Add an `is_jarvis_speaking` threading.Event flag
- Set it BEFORE TTS playback starts, clear it AFTER playback ends + 300ms cooldown
- In the VAD listener loop: if is_jarvis_speaking is set, multiply the energy threshold by 4x
  (this allows real human barge-in at loud volume but ignores speaker bleed)
- Add debug logging: [VAD_SUPPRESSED] when ignoring audio during speech

FIX 2 — COMMAND RECOGNITION PIPELINE:
- Trace why voice commands aren't being recognized
- Verify STT transcription output (add logging of raw transcription text)
- Check intent matching: is it keyword-based? fuzzy? Does it handle Italian well?
- Add fallback: if no intent matched, log the transcription and send to Claude for NLU
- Ensure common Italian commands work: "apri chrome", "che ore sono", "situazione affitto",
  "cerca su google", "chiudi tutto", "metti musica", "volume su/giù"

FIX 3 — THREAD SAFETY & SHUTDOWN:
- All shared state must use threading.Lock or threading.Event
- CTRL+C must: stop VAD listener, stop TTS playback, stop music, close pyaudio stream, exit clean
- No orphan threads — use daemon=True or explicit join with timeout
- Add try/except around all thread entry points

FIX 4 — FINANCE ENGINE INTEGRATION:
- Import finance_engine.py into the agent
- Add intent triggers: "situazione affitto", "come sto con l'affitto", "report finanziario",
  "quanto mi manca per l'affitto", "aggiorna entrate a [X] euro"
- On match: call check_gap() or aggiorna_entrate(), speak the .tts field

FIX 5 — CODE QUALITY:
- Replace all bare `except:` with `except Exception:`
- Replace deprecated `hash()` calls with hashlib if used for caching
- Add type hints to all function signatures
- Ensure all file operations use encoding='utf-8'
- Remove any dead code or unused imports

═══════════════════════════════════════════════
PHASE 3: AUTOMATED TEST SUITE
═══════════════════════════════════════════════

Create `tests/` directory with pytest tests:

tests/test_finance_engine.py:
- test_check_gap_zero_entrate: fresh file, gap should equal target
- test_check_gap_partial: set entrate to 50, verify gap = 60
- test_check_gap_coperto: set entrate to 120, verify coperto=True, gap=0
- test_aggiorna_entrate: update to 80, verify persistence in JSON
- test_tts_output_not_empty: verify tts string is always non-empty
- test_tts_randomization: call 10 times, verify not all identical

tests/test_intent_matching.py:
- test_open_app_commands: "apri chrome", "apri spotify", "apri word" → correct app action
- test_website_commands: "cerca su google python", "apri youtube" → correct URL action
- test_system_commands: "che ore sono", "volume su", "spegni il pc" → correct system action
- test_finance_commands: "situazione affitto", "quanto mi manca" → finance action triggered
- test_unknown_command: gibberish text → fallback to Claude/conversation mode
- test_italian_variations: "aprimi chrome", "metti su chrome", "fammi vedere chrome" → same action

tests/test_vad_barge_in.py:
- Mock pyaudio stream — simulate energy levels numerically, never open a real mic.
- test_speaking_flag_suppresses_vad: simulate is_jarvis_speaking=True, verify VAD ignores audio
- test_normal_vad_detects_speech: simulate is_jarvis_speaking=False, verify VAD triggers
- test_cooldown_after_speech: verify VAD stays suppressed for 300ms after speech ends
- test_loud_barge_in_during_speech: simulate very high energy during speech, verify it passes

tests/test_config.py:
- test_no_hardcoded_keys: scan all .py files for patterns like "sk-", "key-", API key formats
- test_utf8_encoding: verify all .py files are valid UTF-8
- test_requirements_complete: verify all imports have matching entries in requirements.txt

tests/test_voice.py:
- CRITICAL: Mock ALL audio playback (pygame.mixer, pyaudio, subprocess calls to media players).
  Tests must NEVER produce actual sound output. Verify files/bytes are generated, not played.
- test_tts_generates_audio: call TTS with a short phrase, verify audio file/bytes produced (mocked playback)
- test_tts_italian_voice: verify the configured voice is it-IT-DiegoNeural

tests/test_integration.py:
- CRITICAL: Mock ALL audio I/O (microphone input, speaker output, pygame, pyaudio).
  No real audio devices should be opened during tests.
- test_full_command_pipeline: simulate audio transcription "apri chrome" → verify action fired
- test_finance_pipeline: simulate "situazione affitto" → verify TTS string contains euro amount
- test_startup_sequence: verify startup phrases are randomized and all systems initialize

═══════════════════════════════════════════════
PHASE 4: RUN TESTS & VERIFY
═══════════════════════════════════════════════

1. Create requirements-dev.txt with pytest, pytest-cov, pytest-mock
2. Run: python -m pytest tests/ -v --tb=short
3. Fix any failing tests
4. Run again until all pass
5. Show me the final test results

═══════════════════════════════════════════════
PHASE 5: DOCUMENTATION
═══════════════════════════════════════════════

1. Update CLAUDE.md with current architecture after fixes
2. Add docstrings to every module and public function
3. Create a CHANGELOG.md noting all fixes made in this session

IMPORTANT CONSTRAINTS:
- Do NOT change the personality or TTS voice (it-IT-DiegoNeural)
- Do NOT remove the Back in Black startup music
- Do NOT change the audio ducking behavior (music fades when JARVIS speaks)
- Keep all user-facing text in Italian
- Keep code comments in English
- Test with `python -m pytest` not `pytest` directly (venv compatibility)
- ALL tests must mock audio I/O: no real microphone, no real speaker, no real pygame.mixer playback.
  Use pytest-mock/unittest.mock to patch pyaudio.open, pygame.mixer, edge-tts async calls, and
  any subprocess that would produce sound. The PC must stay SILENT during the entire test suite.
"""
