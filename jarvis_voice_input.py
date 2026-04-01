"""
JARVIS Voice Input — CLI-mode STT via faster-whisper.
Records from mic and transcribes using jarvis_stt module.
Falls back gracefully if mic/STT unavailable.
"""

import numpy as np
from jarvis_stt import transcribe_audio, preload as preload_stt


def listen_and_transcribe(duration_seconds: int = 5) -> str:
    """
    Registra audio dal microfono e restituisce il testo trascritto.

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

    # 2. Trascrivi con faster-whisper
    try:
        audio_flat = audio_int16.flatten()
        text = transcribe_audio(audio_flat)
        if text:
            print(f"[STT] Riconosciuto: {text}")
        else:
            print("[STT] Nessun parlato rilevato.")
        return text
    except Exception as e:
        print(f"[STT] Errore trascrizione: {e}")
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
