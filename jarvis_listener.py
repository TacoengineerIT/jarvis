"""
JARVIS Listener v3 — Ascolto continuo robusto.
Uses faster-whisper (CTranslate2) for STT.
  - STT serializzato (un trascrittore alla volta)
  - Print() diretti per visibilità (non logger)
  - Audio level display ogni 2s
  - Stream riavvia automaticamente se crasha
  - reset_vad() NON chiamato automaticamente (solo su barge-in)
  - Calibrazione separata da elaborazione
"""
import threading
import numpy as np
import time
from typing import Callable, Optional

from jarvis_vad_smart import SmartVAD, SAMPLE_RATE, CHUNK_SAMPLES
from jarvis_stt import transcribe_audio, preload as preload_stt

CALIBRATION_CHUNKS = 32          # ~1s
LEVEL_PRINT_CHUNKS  = 64         # stampa livello audio ogni ~2s
STREAM_RETRY_DELAY  = 2.0        # secondi prima di riavviare stream dopo crash


class JarvisListener:
    """
    Ascolta dal microfono in background H24.
    audio  →  VAD  →  Whisper (serializzato)  →  on_transcript(text)
    """

    def __init__(
        self,
        on_transcript: Callable[[str], None],
        on_barge_in:   Optional[Callable[[], None]] = None,
        is_speaking_fn: Optional[Callable[[], bool]] = None,
    ):
        self.on_transcript   = on_transcript
        self.on_barge_in     = on_barge_in    or (lambda: None)
        self.is_speaking_fn  = is_speaking_fn or (lambda: False)

        self._running       = False
        self._thread: Optional[threading.Thread] = None

        # Calibrazione
        self._calibrating   = True
        self._noise_buf     = []
        self._level_counter = 0
        self._last_rms      = 0.0

        # Barge-in suppression: prevent JARVIS from hearing its own TTS
        self._was_speaking      = False
        self._cooldown_until    = 0.0   # timestamp when cooldown ends
        self._cooldown_duration = 0.3   # 300ms post-speech cooldown

        # STT serializzato (un thread alla volta)
        self._transcribe_sem = threading.Semaphore(1)  # un trascrittore alla volta

        # Wake word (optional, set via set_wakeword_detector)
        self._wakeword = None
        self._on_wakeword_cb = None

        # VAD
        self._vad = SmartVAD(
            on_speech_start=self._on_speech_start,
            on_speech_end=self._on_speech_end,
        )

    # ── STT preload ───────────────────────────────────────

    def preload_stt_model(self):
        """Preload faster-whisper model (call at startup)."""
        preload_stt()

    def set_wakeword_detector(self, detector, on_wakeword: Callable[[], None]):
        """Attach a wake word detector. Audio chunks are fed to it in the callback."""
        self._wakeword = detector
        self._on_wakeword_cb = on_wakeword

    # ── VAD callbacks ─────────────────────────────────────

    def _on_speech_start(self):
        print(f"\n[LISTENING] Voce rilevata (livello={self._last_rms:.4f})")
        if self.is_speaking_fn():
            print("[BARGE_IN] Utente interrompe JARVIS!")
            self.on_barge_in()

    def _on_speech_end(self, audio: np.ndarray):
        duration = len(audio) / SAMPLE_RATE
        print(f"[LISTENING->PROCESSING] Utterance {duration:.2f}s -> STT in coda")
        t = threading.Thread(
            target=self._transcribe,
            args=(audio,),
            daemon=True,
            name="jarvis-transcribe",
        )
        t.start()

    # ── Trascrizione STT (serializzata) ─────────────────

    def _transcribe(self, audio: np.ndarray):
        duration = len(audio) / SAMPLE_RATE

        # Un trascrittore alla volta — evita competizione su CPU
        acquired = self._transcribe_sem.acquire(timeout=30)
        if not acquired:
            print("[STT] Timeout attesa semaforo — utterance scartata.")
            return

        try:
            print(f"[STT] Trascrivo {duration:.2f}s di audio...")
            t0 = time.time()

            text = transcribe_audio(audio)

            elapsed = time.time() - t0
            if text:
                print(f"[USER_SPEECH] \"{text}\"  ({elapsed:.1f}s)")
                self.on_transcript(text)
            else:
                print(f"[STT] Nessun parlato ({elapsed:.1f}s) — ignoro.")

        except Exception as e:
            print(f"[STT ERROR] {e}")
        finally:
            self._transcribe_sem.release()

    # ── Audio stream ──────────────────────────────────────

    def _audio_loop(self):
        try:
            import sounddevice as sd
        except ImportError:
            print("[LISTENER ERROR] sounddevice non installato: pip install sounddevice")
            return

        print(f"[LISTENER] Stream aperto @ {SAMPLE_RATE}Hz  chunk={CHUNK_SAMPLES} ({CHUNK_SAMPLES/SAMPLE_RATE*1000:.0f}ms)")

        def callback(indata, frames, time_info, status):
            if status:
                print(f"[LISTENER] Stream status: {status}")

            # float32 → int16
            chunk_f32 = indata[:, 0].copy()
            chunk_i16 = np.clip(chunk_f32 * 32767, -32768, 32767).astype(np.int16)

            # Calcola RMS per display livello
            rms = float(np.sqrt(np.mean(chunk_f32 ** 2)))
            self._last_rms = rms

            # Calibrazione ambientale (~1s)
            if self._calibrating:
                self._noise_buf.append(chunk_i16)
                if len(self._noise_buf) >= CALIBRATION_CHUNKS:
                    noise = np.concatenate(self._noise_buf)
                    self._vad.calibrate_noise(noise)
                    self._noise_buf   = []
                    self._calibrating = False
                    print(f"[CALIBRATION] OK. Threshold VAD impostato. Ascolto attivo.")
                    print(f"[IDLE] In ascolto — parla liberamente Sir.\n")
                return

            # Display audio level periodico
            self._level_counter += 1
            if self._level_counter >= LEVEL_PRINT_CHUNKS:
                bar_len = int(rms * 200)
                bar = "#" * min(bar_len, 40)
                print(f"[AUDIO_LEVEL] {rms:.4f}  |{bar:<40}|", end="\r")
                self._level_counter = 0

            # Suppress VAD when JARVIS is speaking (avoid self-trigger)
            jarvis_speaking = self.is_speaking_fn()
            now = time.time()

            if jarvis_speaking:
                # JARVIS is actively playing audio — suppress VAD
                if not self._was_speaking:
                    print("[VAD_SUPPRESSED] JARVIS speaking — threshold raised 3.5x")
                self._was_speaking = True
                self._vad.set_suppressed(True)
            elif self._was_speaking:
                # JARVIS just stopped speaking — start cooldown
                self._was_speaking = False
                self._cooldown_until = now + self._cooldown_duration
                self._vad.set_suppressed(True)
                print(f"[VAD_SUPPRESSED] Cooldown {self._cooldown_duration*1000:.0f}ms post-speech")
                # Reset VAD state to discard any "speech" buffered from speaker bleed
                self._vad.reset()
            elif now < self._cooldown_until:
                # Still in post-speech cooldown
                self._vad.set_suppressed(True)
            else:
                # Normal listening
                self._vad.set_suppressed(False)

            # Feed wake word detector (if active and not suppressed)
            if self._wakeword is not None and not jarvis_speaking and now >= self._cooldown_until:
                if self._wakeword.process_chunk(chunk_i16):
                    if self._on_wakeword_cb:
                        self._on_wakeword_cb()

            # Feed VAD
            self._vad.process_chunk(chunk_i16)

        while self._running:
            try:
                with sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    channels=1,
                    dtype=np.float32,
                    blocksize=CHUNK_SAMPLES,
                    callback=callback,
                    latency="low",
                ):
                    print("[LISTENER] Stream attivo.")
                    while self._running:
                        time.sleep(0.05)

            except Exception as e:
                if self._running:
                    print(f"[LISTENER ERROR] Stream crash: {e}")
                    print(f"[LISTENER] Riavvio stream in {STREAM_RETRY_DELAY}s...")
                    # Reset calibrazione per riavvio
                    self._calibrating = True
                    self._noise_buf   = []
                    self._vad.reset()
                    time.sleep(STREAM_RETRY_DELAY)

    # ── Public API ────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(
            target=self._audio_loop,
            daemon=True,
            name="jarvis-listener",
        )
        self._thread.start()
        print("[LISTENER] Thread avviato.")

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        print("[LISTENER] Fermato.")

    def reset_vad(self):
        """
        Resetta stato VAD. Chiamare SOLO su barge-in, NON dopo ogni utterance.
        Il VAD torna automaticamente in SILENCE dopo voice_end.
        """
        print("[LISTENER] VAD reset (post barge-in).")
        self._vad.reset()

    @property
    def backend_name(self) -> str:
        return self._vad.backend_name

    @staticmethod
    def is_mic_available() -> bool:
        try:
            import sounddevice as sd
            devices = sd.query_devices(kind="input")
            return devices is not None
        except Exception:
            return False
