"""
JARVIS Voice Input - Whisper transcription WITHOUT FFmpeg dependency.
Passes numpy array directly to Whisper model (bypasses FFmpeg audio loading).
Falls back gracefully if mic/whisper unavailable.
"""

import numpy as np
from pathlib import Path

# Lazy-load Whisper to avoid crash at import if not installed
_MODEL = None

def _get_model():
    global _MODEL
    if _MODEL is None:
        try:
            import whisper
            _MODEL = whisper.load_model("base", device="cpu")
        except Exception as e:
            print(f"[Whisper] Impossibile caricare modello: {e}")
            _MODEL = None
    return _MODEL


def listen_and_transcribe(duration_seconds: int = 5) -> str:
    """
    Registra audio dal microfono e restituisce il testo trascritto.
    Non richiede FFmpeg: passa numpy array direttamente a Whisper.

    Returns:
        Stringa con testo trascritto, o stringa vuota se fallisce.
    """
    SAMPLE_RATE = 16000

    # 1. Registra audio
    try:
        import sounddevice as sd
        print("JARVIS: Ascolto Sir...")
        audio_int16 = sd.rec(
            int(SAMPLE_RATE * duration_seconds),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype=np.int16
        )
        sd.wait()
    except Exception as e:
        print(f"[Mic] Errore registrazione: {e}")
        print("[Mic] Dispositivo audio non disponibile. Usa input testo.")
        return ""

    # 2. Carica modello Whisper
    model = _get_model()
    if model is None:
        print("[Whisper] Modello non disponibile. Installare: pip install openai-whisper")
        return ""

    # 3. Converti int16 → float32 normalizzato [-1.0, 1.0]
    # Questo bypassa completamente FFmpeg: nessun file intermedio!
    try:
        audio_float32 = audio_int16.flatten().astype(np.float32) / 32768.0
        result = model.transcribe(audio_float32, language="it", fp16=False)
        text = result["text"].strip()
        if text:
            print(f"[Whisper] Riconosciuto: {text}")
        else:
            print("[Whisper] Nessun parlato rilevato.")
        return text
    except Exception as e:
        print(f"[Whisper] Errore trascrizione: {e}")
        return ""


def check_ffmpeg() -> bool:
    """Verifica se FFmpeg è disponibile (informativo, non bloccante)."""
    import subprocess
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=3)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


if __name__ == "__main__":
    ffmpeg_ok = check_ffmpeg()
    if not ffmpeg_ok:
        print("[INFO] FFmpeg non trovato nel PATH. Funziona lo stesso via numpy array.")
        print("[INFO] Per installarlo: scoop install ffmpeg  oppure  choco install ffmpeg")

    text = listen_and_transcribe()
    if text:
        print(f"Testo riconosciuto: {text}")
    else:
        print("Nessun testo riconosciuto.")
