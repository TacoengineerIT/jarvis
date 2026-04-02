"""
JARVIS Wake Word Detection — openwakeword backend.
Listens for "hey jarvis" to transition from passive to active listening.
Optional module: if openwakeword is not installed, falls back to always-active.
"""
import logging
import time
import numpy as np
from typing import Optional

logger = logging.getLogger("jarvis.wakeword")

# openwakeword expects 16kHz, 16-bit mono, 1280-sample chunks (80ms)
WAKEWORD_CHUNK_SAMPLES = 1280
WAKEWORD_THRESHOLD = 0.5

_oww_model = None
_oww_available = False
_oww_checked = False


def _load_oww():
    """Try to load openwakeword model. Returns True if available."""
    global _oww_model, _oww_available, _oww_checked
    if _oww_checked:
        return _oww_available
    _oww_checked = True
    try:
        import openwakeword
        from openwakeword.model import Model
        openwakeword.utils.download_models()
        _oww_model = Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
        _oww_available = True
        logger.info("[WAKEWORD] openwakeword caricato — modello 'hey_jarvis'")
        print("[WAKEWORD] Modello 'hey_jarvis' pronto.")
    except Exception as e:
        _oww_available = False
        logger.warning(f"[WAKEWORD] openwakeword non disponibile ({e}). Ascolto continuo.")
        print(f"[WAKEWORD] Non disponibile ({e}). Fallback: ascolto continuo.")
    return _oww_available


class WakeWordDetector:
    """
    Detects "hey jarvis" wake word in audio stream.

    Usage:
        detector = WakeWordDetector()
        if detector.available:
            detected = detector.process_chunk(audio_int16)
    """

    def __init__(self, threshold: float = WAKEWORD_THRESHOLD, cooldown_seconds: float = 2.0):
        self.threshold = threshold
        self.cooldown_seconds = cooldown_seconds
        self._available = _load_oww()
        self._buffer = np.array([], dtype=np.int16)
        self._last_detected_time: float = 0.0

    @property
    def available(self) -> bool:
        """True if openwakeword is loaded and ready."""
        return self._available

    def process_chunk(self, chunk: np.ndarray) -> bool:
        """
        Feed audio chunk (int16, 16kHz) and check for wake word.

        Args:
            chunk: int16 numpy array of any size

        Returns:
            True if wake word detected in this chunk
        """
        if not self._available or _oww_model is None:
            return False

        # Cooldown guard: ignore chunks until cooldown expires
        now = time.time()
        if now - self._last_detected_time < self.cooldown_seconds:
            logger.debug("[COOLDOWN] Ignorando chunk (cooldown attivo)")
            return False

        # Buffer chunks until we have enough for oww (1280 samples)
        self._buffer = np.concatenate([self._buffer, chunk])

        detected = False
        while len(self._buffer) >= WAKEWORD_CHUNK_SAMPLES:
            frame = self._buffer[:WAKEWORD_CHUNK_SAMPLES]
            self._buffer = self._buffer[WAKEWORD_CHUNK_SAMPLES:]

            prediction = _oww_model.predict(frame)
            # Check all wake word scores
            for model_name, score in prediction.items():
                if score >= self.threshold:
                    logger.info(f"[WAKEWORD] Rilevato '{model_name}' (score={score:.3f})")
                    print(f"[WAKEWORD] Hey JARVIS rilevato! (score={score:.3f})")
                    self._last_detected_time = time.time()
                    logger.info(f"[COOLDOWN] Attivato (reset tra {self.cooldown_seconds}s)")
                    detected = True
                    break  # One detection per chunk — stop inner loop
            if detected:
                break  # Stop outer loop immediately after first detection

        return detected

    def reset(self):
        """Clear internal buffer."""
        self._buffer = np.array([], dtype=np.int16)
        if self._available and _oww_model is not None:
            try:
                _oww_model.reset()
            except Exception:
                pass


def is_available() -> bool:
    """Check if wake word detection is available."""
    return _load_oww()
