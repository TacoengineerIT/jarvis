"""
JARVIS STT — Speech-to-Text via faster-whisper (CTranslate2 backend).
Single model load at startup. Italian language hardcoded.
"""
import logging
import numpy as np

logger = logging.getLogger("jarvis.stt")

# Singleton model — loaded once
_model = None
_model_loaded = False


def _load_model():
    """Load faster-whisper model once. Returns model or None."""
    global _model, _model_loaded
    if _model_loaded:
        return _model
    try:
        from faster_whisper import WhisperModel
        logger.info("[STT] Carico faster-whisper 'small' (int8, CPU)...")
        print("[STT] Carico faster-whisper 'small' (int8, CPU)...")
        _model = WhisperModel("small", device="cpu", compute_type="int8")
        _model_loaded = True
        logger.info("[STT] Modello pronto.")
        print("[STT] Modello pronto.")
    except Exception as e:
        logger.error(f"[STT] Errore caricamento modello: {e}")
        print(f"[STT ERROR] {e}")
        _model = None
        _model_loaded = True  # Don't retry on every call
    return _model


def transcribe_audio(audio: np.ndarray) -> str:
    """
    Transcribe raw PCM audio (int16, 16kHz mono) to Italian text.

    Args:
        audio: numpy int16 array of audio samples at 16kHz

    Returns:
        Transcribed text, stripped and lowercased. Empty string on failure.
    """
    model = _load_model()
    if model is None:
        return ""

    # Convert int16 → float32 normalized [-1, 1]
    audio_f32 = audio.astype(np.float32) / 32768.0

    try:
        segments, info = model.transcribe(
            audio_f32,
            language="it",
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        # Collect all segment texts
        text = " ".join(seg.text for seg in segments).strip().lower()
        return text
    except Exception as e:
        logger.error(f"[STT] Errore trascrizione: {e}")
        print(f"[STT ERROR] {e}")
        return ""


def is_model_loaded() -> bool:
    """Check if STT model is ready."""
    return _model is not None


def preload():
    """Preload model (call at startup to avoid first-call latency)."""
    _load_model()
