"""
main.py — JARVIS v4.0 Entry Point

Modes:
  python main.py             # Voice + wake word (default)
  python main.py --text      # Text-only (no mic)
  python main.py --debug     # Verbose logging

Voice pipeline:
  Wake word ("hey jarvis") → WebRTC VAD → Google STT → JarvisCore → edge-tts → pygame
"""

import argparse
import asyncio
import hashlib
import io
import json
import logging
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

# Force UTF-8 output on Windows (handles emoji in print statements)
if hasattr(sys.stdout, "buffer") and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer") and sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ------------------------------------------------------------------ #
# Logging                                                              #
# ------------------------------------------------------------------ #

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "jarvis.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("jarvis.main")

# ------------------------------------------------------------------ #
# Config                                                               #
# ------------------------------------------------------------------ #

CONFIG_PATH = Path("config.json")


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        logger.warning("config.json not found — using defaults")
        return {}
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json.load(f)


# ------------------------------------------------------------------ #
# TTS Cache (SQLite-backed)                                            #
# ------------------------------------------------------------------ #

CACHE_DIR = Path("cache") / "tts"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DB = CACHE_DIR / "cache.db"


def _init_tts_cache():
    conn = sqlite3.connect(CACHE_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tts_cache (
            text_hash TEXT PRIMARY KEY,
            text      TEXT,
            filepath  TEXT,
            timestamp REAL
        )
    """)
    conn.commit()
    conn.close()


def _get_cached_tts(text: str) -> Optional[str]:
    """Return cached MP3 path if exists and fresh (< TTL)."""
    text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    try:
        conn = sqlite3.connect(CACHE_DB)
        row = conn.execute(
            "SELECT filepath, timestamp FROM tts_cache WHERE text_hash = ?",
            (text_hash,),
        ).fetchone()
        conn.close()
        if row:
            filepath, ts = row
            ttl = 168 * 3600  # 7 days default
            if time.time() - ts < ttl and Path(filepath).exists():
                return filepath
    except Exception:
        pass
    return None


def _save_tts_cache(text: str, filepath: str):
    text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
    try:
        conn = sqlite3.connect(CACHE_DB)
        conn.execute(
            "INSERT OR REPLACE INTO tts_cache (text_hash, text, filepath, timestamp) VALUES (?, ?, ?, ?)",
            (text_hash, text[:200], filepath, time.time()),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _cleanup_old_cache(max_age_hours: int = 168):
    """Delete TTS cache entries older than max_age_hours."""
    cutoff = time.time() - (max_age_hours * 3600)
    try:
        conn = sqlite3.connect(CACHE_DB)
        rows = conn.execute(
            "SELECT filepath FROM tts_cache WHERE timestamp < ?", (cutoff,)
        ).fetchall()
        for (fp,) in rows:
            try:
                Path(fp).unlink(missing_ok=True)
            except Exception:
                pass
        conn.execute("DELETE FROM tts_cache WHERE timestamp < ?", (cutoff,))
        conn.commit()
        conn.close()
    except Exception:
        pass


# ------------------------------------------------------------------ #
# Voice dependency check                                               #
# ------------------------------------------------------------------ #

def _check_voice_deps() -> bool:
    missing = []
    try:
        import speech_recognition  # noqa
    except ImportError:
        missing.append("SpeechRecognition")
    try:
        import webrtcvad  # noqa
    except ImportError:
        missing.append("webrtcvad / webrtcvad-wheels")
    try:
        import sounddevice  # noqa
    except ImportError:
        missing.append("sounddevice")
    if missing:
        logger.warning("Missing voice deps: %s — falling back to text mode", missing)
        return False
    return True


def _check_mic_available() -> bool:
    """Check if at least one input (microphone) device is accessible."""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        has_input = any(d["max_input_channels"] > 0 for d in devices)
        if not has_input:
            logger.warning("[MIC] Nessun dispositivo di input trovato")
            return False
        logger.info("[MIC] Microfono disponibile (%d dispositivi totali)", len(devices))
        return True
    except Exception as e:
        logger.error("[MIC] Errore check microfono: %s", e)
        return False


# ------------------------------------------------------------------ #
# STT: WebRTC VAD + Google Speech Recognition                         #
# ------------------------------------------------------------------ #

async def listen_once(config: dict) -> tuple[str, bytes]:
    """Record a single utterance using VAD + Google STT."""
    import speech_recognition as sr
    import webrtcvad
    import sounddevice as sd
    import numpy as np

    mic_cfg = config.get("microphone", {})
    stt_cfg = config.get("speech_recognition", {})

    RATE = mic_cfg.get("sample_rate", 16000)
    FRAME_DURATION_MS = mic_cfg.get("chunk_duration_ms", 30)
    FRAME_SIZE = int(RATE * FRAME_DURATION_MS / 1000)
    VAD_AGG = mic_cfg.get("vad_aggressiveness", 2)
    SILENCE_FRAMES = int(600 / FRAME_DURATION_MS)  # ~600ms silence to end
    TIMEOUT_SECONDS = stt_cfg.get("timeout_seconds", 10)
    MAX_FRAMES = int(TIMEOUT_SECONDS * 1000 / FRAME_DURATION_MS)
    LANGUAGE = stt_cfg.get("language", "it-IT")

    vad = webrtcvad.Vad(VAD_AGG)
    rec = sr.Recognizer()

    print("\n🎤 In ascolto, Sir...", flush=True)

    audio_frames = []
    speech_started = False
    silence_count = 0
    done = asyncio.Event()

    def callback(indata, frame_count, time_info, status):
        nonlocal speech_started, silence_count
        pcm = (indata[:, 0] * 32768).astype("int16").tobytes()
        is_speech = False
        try:
            is_speech = vad.is_speech(pcm, RATE)
        except Exception:
            pass
        if is_speech:
            speech_started = True
            silence_count = 0
        elif speech_started:
            silence_count += 1
        audio_frames.append(pcm)
        if speech_started and silence_count >= SILENCE_FRAMES:
            done.set()
        if len(audio_frames) >= MAX_FRAMES:
            done.set()

    device_id = mic_cfg.get("device_id")
    stream_kwargs = dict(
        samplerate=RATE, channels=1, dtype="float32",
        blocksize=FRAME_SIZE, callback=callback,
    )
    if device_id is not None:
        stream_kwargs["device"] = device_id

    try:
        with sd.InputStream(**stream_kwargs):
            try:
                await asyncio.wait_for(done.wait(), timeout=TIMEOUT_SECONDS)
            except asyncio.TimeoutError:
                logger.warning("[STT] Timeout dopo %ds senza audio", TIMEOUT_SECONDS)
    except Exception as e:
        logger.error("[STT] Errore apertura microfono: %s", e)
        return "", b""

    if not audio_frames:
        return "", b""

    raw = b"".join(audio_frames)

    # Google STT
    try:
        audio_data = sr.AudioData(raw, RATE, 2)
        transcript = rec.recognize_google(audio_data, language=LANGUAGE)
        logger.info("[STT] %s", transcript)
        print(f"📝 \"{transcript}\"")
        return transcript, raw
    except sr.UnknownValueError:
        logger.debug("STT: no speech recognized")
        return "", raw
    except sr.RequestError as e:
        logger.error("STT network error: %s", e)
        print("⚠️  Errore connessione STT. Riprovo...")
        return "", raw


# ------------------------------------------------------------------ #
# TTS: edge-tts + pygame + caching                                    #
# ------------------------------------------------------------------ #

async def speak(text: str, config: dict = None):
    """Generate TTS with edge-tts, cache result, play via pygame."""
    config = config or {}
    voice_cfg = config.get("voice", {})
    voice = voice_cfg.get("tts_voice", "it-IT-DiegoNeural")
    cache_enabled = voice_cfg.get("tts_cache_enabled", True)

    # Check cache first
    if cache_enabled:
        cached_path = _get_cached_tts(text)
        if cached_path:
            logger.debug("TTS cache hit: %s", cached_path)
            await _play_audio(cached_path)
            return

    # Generate new TTS
    try:
        import edge_tts

        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        mp3_path = str(CACHE_DIR / f"{text_hash}.mp3")

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(mp3_path)

        if cache_enabled:
            _save_tts_cache(text, mp3_path)

        await _play_audio(mp3_path)

    except Exception as e:
        logger.error("TTS error: %s", e)
        print(f"JARVIS: {text}")


async def _play_audio(filepath: str):
    """Play MP3 via pygame (non-blocking)."""
    try:
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.1)
        pygame.mixer.music.unload()
    except Exception as e:
        logger.error("Audio playback error: %s", e)


# ------------------------------------------------------------------ #
# Wake word listener                                                   #
# ------------------------------------------------------------------ #

async def _wait_for_wakeword(config: dict) -> bool:
    """
    Listen for wake word using openwakeword.
    Returns True when detected, False if unavailable (skip to always-on).
    """
    ww_cfg = config.get("wake_word", {})
    if not ww_cfg.get("enabled", True):
        return True  # Wake word disabled → always active

    try:
        from jarvis_wakeword import WakeWordDetector
        import sounddevice as sd
        import numpy as np
    except ImportError as e:
        logger.warning("Wake word deps missing (%s) — always-on mode", e)
        return True

    detector = WakeWordDetector(threshold=ww_cfg.get("threshold", 0.5))
    if not detector.available:
        logger.info("Wake word model not available — always-on mode")
        return True

    print("💤 In ascolto passivo... dì 'Hey JARVIS'", flush=True)

    detected = asyncio.Event()
    RATE = 16000
    CHUNK = 1280  # openwakeword frame size

    def callback(indata, frame_count, time_info, status):
        chunk_i16 = (indata[:, 0] * 32768).astype("int16")
        if detector.process_chunk(chunk_i16):
            detected.set()

    mic_cfg = config.get("microphone", {})
    device_id = mic_cfg.get("device_id")
    stream_kwargs = dict(
        samplerate=RATE, channels=1, dtype="float32",
        blocksize=CHUNK, callback=callback,
    )
    if device_id is not None:
        stream_kwargs["device"] = device_id

    try:
        with sd.InputStream(**stream_kwargs):
            await detected.wait()
    except Exception as e:
        logger.error("[WAKEWORD] Errore apertura microfono: %s", e)
        return False

    detector.reset()
    print("✨ JARVIS attivato!", flush=True)
    return True


# ------------------------------------------------------------------ #
# JarvisApp                                                            #
# ------------------------------------------------------------------ #

class JarvisApp:
    def __init__(self, config: dict, text_mode: bool = False):
        from jarvis_memory import JarvisMemory
        from jarvis_mood import MoodDetector
        from jarvis_core import JarvisCore
        from jarvis_actions import JarvisActions

        self.config = config
        self.text_mode = text_mode

        api_key = os.getenv("ANTHROPIC_API_KEY") or config.get("anthropic_api_key")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY not set! Set env var or config.json")
            sys.exit(1)

        self.memory = JarvisMemory()
        self.mood_detector = MoodDetector()
        self.core = JarvisCore(api_key=api_key, memory=self.memory, mood_detector=self.mood_detector)
        self.actions = JarvisActions(config)

        # Home automation (optional)
        self.home = None
        try:
            from jarvis_home import get_bridge
            bridge = get_bridge()
            if bridge.available:
                self.home = bridge
        except Exception:
            pass

        self._running = True

    async def run(self):
        _init_tts_cache()
        _cleanup_old_cache()

        print("=" * 60)
        print("  J.A.R.V.I.S. v4.0 — Online, Sir.")
        stats = self.memory.stats()
        print(f"  Memoria: {stats['conversations']} conversazioni, {stats['mood_days_tracked']} giorni di mood")
        if self.home:
            print("  Home Assistant: connesso")
        print("=" * 60)

        await speak("JARVIS operativo, Sir. Come posso aiutarla?", self.config)

        if self.text_mode:
            await self._text_loop()
        else:
            voice_ok = _check_voice_deps()
            mic_ok = _check_mic_available() if voice_ok else False
            if voice_ok and mic_ok:
                await self._voice_loop()
            else:
                if voice_ok and not mic_ok:
                    logger.warning("[MAIN] Microfono non disponibile. Fallback a text mode.")
                    print("[MAIN] Microfono non disponibile. Modalità testo attiva.")
                else:
                    logger.info("Falling back to text mode (missing deps)")
                await self._text_loop()

    async def _voice_loop(self):
        ww_enabled = self.config.get("wake_word", {}).get("enabled", True)

        while self._running:
            try:
                # Wait for wake word (if enabled)
                if ww_enabled:
                    await _wait_for_wakeword(self.config)

                # Active listening — record + STT
                transcript, audio_bytes = await listen_once(self.config)

                if not transcript:
                    if ww_enabled:
                        continue  # Back to wake word listening
                    else:
                        await speak("Mi scusi Sir, non ho sentito nulla.", self.config)
                        continue

                # Check for exit commands
                if transcript.lower().strip() in ("esci", "exit", "quit", "spegniti", "ciao jarvis"):
                    break

                await self._handle_input(transcript, audio_bytes)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error("Voice loop error: %s", e)
                await asyncio.sleep(1)

        await self._shutdown()

    async def _text_loop(self):
        print("Modalità testo attiva. Digita 'quit' per uscire.\n")
        while self._running:
            try:
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input("\nTu: ").strip()
                )
                if not user_input:
                    continue
                if user_input.lower() in ("quit", "exit", "esci"):
                    break
                await self._handle_input(user_input, None)
            except (KeyboardInterrupt, EOFError):
                break

        await self._shutdown()

    async def _handle_input(self, text: str, audio_bytes):
        # 1. Home automation (if configured)
        if self.home:
            home_triggers = ["accendi", "spegni", "luce", "luci", "temperatura", "stato casa"]
            if any(t in text.lower() for t in home_triggers):
                from jarvis_home import get_bridge
                # Simple routing
                u = text.lower()
                if "accendi" in u:
                    device = u.split("accendi")[-1].strip()
                    response = self.home.turn_on(device)
                elif "spegni" in u:
                    device = u.split("spegni")[-1].strip()
                    response = self.home.turn_off(device)
                elif "stato casa" in u:
                    response = self.home.get_all_states()
                else:
                    response = None

                if response:
                    print(f"\nJARVIS: {response}\n")
                    await speak(response, self.config)
                    return

        # 2. Deterministic actions (git, time, apps)
        intent_guess = self.core._classify_intent(text)
        action_response = await self.actions.execute(intent_guess, text)
        if action_response:
            print(f"\nJARVIS: {action_response}\n")
            await speak(action_response, self.config)
            return

        # 3. Full LLM reasoning (Sonnet/Haiku)
        result = await self.core.process(text, audio_bytes)
        response = result["response"]
        mood = result["mood"]
        model = result["model"]

        print(f"\nJARVIS [{model}] {mood['emoji']}: {response}\n")
        await speak(response, self.config)

    async def _shutdown(self):
        self._running = False
        await speak("Arrivederci, Sir. JARVIS offline.", self.config)
        print("JARVIS offline.")


# ------------------------------------------------------------------ #
# Entry point                                                          #
# ------------------------------------------------------------------ #

async def _main():
    parser = argparse.ArgumentParser(description="JARVIS v4.0")
    parser.add_argument("--text", action="store_true", help="Text-only mode (no mic)")
    parser.add_argument("--voice", action="store_true", help="Voice + wake word (default)")
    parser.add_argument("--debug", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    config = load_config()

    # --text forces text mode
    text_mode = args.text
    app = JarvisApp(config, text_mode=text_mode)
    await app.run()


if __name__ == "__main__":
    asyncio.run(_main())
