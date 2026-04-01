"""
JARVIS VAD Smart - Voice Activity Detection
Prova silero-vad (PyPI, no C++ richiesto).
Fallback automatico a energy-based VAD se torch/silero non disponibili.
"""
import threading
import numpy as np
import logging

logger = logging.getLogger("jarvis.vad")

SAMPLE_RATE = 16000
CHUNK_SAMPLES = 512  # 32ms @ 16kHz (silero requirement)

STATE_SILENCE = "silence"
STATE_VOICE   = "voice"


# ──────────────────────────────────────────────────────────
# BACKEND: Silero
# ──────────────────────────────────────────────────────────

def _try_load_silero():
    """Prova a caricare silero-vad dal pacchetto PyPI silero-vad>=5.0"""
    try:
        from silero_vad import load_silero_vad   # pip install silero-vad
        model = load_silero_vad()
        model.eval()
        logger.info("[VAD] Silero VAD caricato.")
        return model
    except Exception:
        pass

    # Secondo tentativo: torch hub (richiede internet prima volta)
    try:
        import torch
        model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True
        )
        model.eval()
        logger.info("[VAD] Silero VAD caricato via torch.hub.")
        return model
    except Exception as e:
        logger.warning(f"[VAD] Silero non disponibile ({e}). Uso energy-based VAD.")
        return None


class _SileroBackend:
    def __init__(self, model, threshold: float = 0.5):
        import torch as _torch
        self._model = model
        self._torch = _torch
        self._threshold = threshold

    def is_speech(self, chunk_int16: np.ndarray) -> float:
        tensor = self._torch.from_numpy(
            chunk_int16.astype(np.float32) / 32768.0
        )
        with self._torch.no_grad():
            return float(self._model(tensor, SAMPLE_RATE).item())

    def calibrate(self, _noise: np.ndarray):
        pass  # silero non ha bisogno di calibrazione

    def reset(self):
        try:
            self._model.reset_states()
        except Exception:
            pass


# ──────────────────────────────────────────────────────────
# BACKEND: Energy (no dipendenze extra)
# ──────────────────────────────────────────────────────────

class _EnergyBackend:
    """RMS energy VAD – nessuna dipendenza esterna."""

    def __init__(self, threshold: float = 0.020):
        self.threshold = threshold
        self._noise_floor = 0.005

    def calibrate(self, noise_samples: np.ndarray):
        rms = float(np.sqrt(np.mean(noise_samples.astype(np.float32) ** 2))) / 32768.0
        self._noise_floor = rms
        self.threshold = max(0.010, rms * 4.0)
        logger.info(
            f"[VAD/energy] Calibrato. Noise floor: {rms:.5f}, "
            f"Threshold: {self.threshold:.5f}"
        )

    def is_speech(self, chunk_int16: np.ndarray) -> float:
        rms = float(np.sqrt(np.mean(chunk_int16.astype(np.float32) ** 2))) / 32768.0
        # Raw ratio without cap — SmartVAD uses threshold multiplier for suppression
        return rms / max(self.threshold, 1e-9)

    def reset(self):
        pass


# ──────────────────────────────────────────────────────────
# SmartVAD – state machine sopra i backend
# ──────────────────────────────────────────────────────────

class SmartVAD:
    """
    State machine VAD con onset/offset detection.

    Callbacks:
        on_speech_start()               – voce iniziata
        on_speech_end(audio_int16)      – voce finita, audio completo
    """

    # When JARVIS is speaking through speakers, multiply threshold by this factor.
    # Only a loud human voice close to the mic can overcome it.
    SUPPRESSION_MULTIPLIER = 3.5

    def __init__(
        self,
        on_speech_start=None,
        on_speech_end=None,
        speech_threshold: float = 0.5,
        silence_duration: float = 1.2,   # secondi di silenzio per chiudere utterance
        min_speech_duration: float = 0.3, # scarta utterance troppo corte
    ):
        self.on_speech_start = on_speech_start or (lambda: None)
        self.on_speech_end   = on_speech_end   or (lambda a: None)
        self.speech_threshold = speech_threshold

        self._silence_frames_needed = max(
            1, int(silence_duration * SAMPLE_RATE / CHUNK_SAMPLES)
        )
        self._min_speech_frames = max(
            1, int(min_speech_duration * SAMPLE_RATE / CHUNK_SAMPLES)
        )

        self._state         = STATE_SILENCE
        self._silence_count = 0
        self._speech_buf    = []
        self._speech_frames = 0
        self._lock          = threading.Lock()

        # Suppression flag — raised when JARVIS is speaking to avoid self-trigger
        self._suppressed = False

        # Backend selection
        silero = _try_load_silero()
        if silero:
            self._backend      = _SileroBackend(silero, threshold=speech_threshold)
            self._backend_name = "silero"
        else:
            self._backend      = _EnergyBackend(threshold=0.020)
            self._backend_name = "energy"

        logger.info(f"[VAD] Backend attivo: {self._backend_name}")

    # ── public ──

    @property
    def backend_name(self) -> str:
        return self._backend_name

    def set_suppressed(self, suppressed: bool):
        """Enable/disable suppression (raises threshold to avoid self-trigger from speakers)."""
        self._suppressed = suppressed

    def calibrate_noise(self, audio: np.ndarray):
        """Calibra con ~1s di silenzio ambientale."""
        self._backend.calibrate(audio)

    def process_chunk(self, chunk: np.ndarray) -> str:
        """
        Processa 512 campioni int16.
        Ritorna: 'silence' | 'voice_start' | 'voice' | 'voice_end'
        """
        prob = self._backend.is_speech(chunk)

        if self._suppressed:
            # During JARVIS speech/cooldown: require much stronger signal.
            # Energy backend returns raw ratio (can exceed 1.0), so multiplier works.
            # Silero returns 0-1 probability, clamp to 0.85 minimum.
            if self._backend_name == "silero":
                threshold = max(0.85, self.speech_threshold * self.SUPPRESSION_MULTIPLIER)
            else:
                threshold = self.speech_threshold * self.SUPPRESSION_MULTIPLIER
        else:
            threshold = self.speech_threshold

        is_voice = prob >= threshold

        with self._lock:
            if self._state == STATE_SILENCE:
                if is_voice:
                    self._state         = STATE_VOICE
                    self._silence_count = 0
                    self._speech_frames = 1
                    self._speech_buf    = [chunk.copy()]
                    self.on_speech_start()
                    return "voice_start"
                return "silence"

            else:  # STATE_VOICE
                self._speech_buf.append(chunk.copy())

                if is_voice:
                    self._silence_count  = 0
                    self._speech_frames += 1
                    return "voice"

                self._silence_count += 1
                if self._silence_count >= self._silence_frames_needed:
                    audio_data   = np.concatenate(self._speech_buf)
                    n_speech     = self._speech_frames

                    self._state         = STATE_SILENCE
                    self._speech_buf    = []
                    self._silence_count = 0
                    self._speech_frames = 0
                    self._backend.reset()

                    if n_speech >= self._min_speech_frames:
                        self.on_speech_end(audio_data)
                        return "voice_end"
                    return "silence"

                return "voice"

    def reset(self):
        """Forza ritorno a stato silenzio (usare dopo barge-in)."""
        with self._lock:
            self._state         = STATE_SILENCE
            self._speech_buf    = []
            self._silence_count = 0
            self._speech_frames = 0
            self._backend.reset()
