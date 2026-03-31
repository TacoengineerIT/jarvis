"""
JARVIS Voice Output - TTS via edge-tts (Microsoft Neural voices, offline-capable).
Voce italiana: it-IT-DiegoNeural.
Falls back to print() se edge-tts non disponibile.
"""

import asyncio
import tempfile
import os

TTS_VOICE = "it-IT-DiegoNeural"
_TTS_AVAILABLE = None  # None = non testato, True/False = esito


def _check_tts() -> bool:
    global _TTS_AVAILABLE
    if _TTS_AVAILABLE is None:
        try:
            import edge_tts  # noqa: F401
            _TTS_AVAILABLE = True
        except ImportError:
            _TTS_AVAILABLE = False
            print("[TTS] edge-tts non installato. Installa: pip install edge-tts")
    return _TTS_AVAILABLE


async def _speak_async(text: str):
    """Genera e riproduce audio TTS in modo asincrono."""
    import edge_tts

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name

    try:
        communicate = edge_tts.Communicate(text, TTS_VOICE)
        await communicate.save(tmp_path)
        _play_audio(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _play_audio(path: str):
    """Riproduce file audio mp3 su Windows."""
    # Prova pygame (già in requirements)
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(50)
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        return
    except Exception:
        pass

    # Fallback: Windows PowerShell media player
    try:
        import subprocess
        subprocess.run(
            ["powershell", "-c",
             f"Add-Type -AssemblyName presentationCore; "
             f"$mp = New-Object system.windows.media.mediaplayer; "
             f"$mp.open('{path}'); $mp.Play(); Start-Sleep 5"],
            timeout=30,
            capture_output=True
        )
        return
    except Exception:
        pass

    # Fallback finale: apri il file con il player predefinito
    try:
        os.startfile(path)
    except Exception as e:
        print(f"[TTS] Impossibile riprodurre audio: {e}")


def say(text: str, print_also: bool = True):
    """
    Legge text ad alta voce via edge-tts.
    Stampa sempre su console (utile per debug/log).

    Args:
        text: Testo da leggere
        print_also: Se True, stampa anche su console (default: True)
    """
    if print_also:
        print(f"JARVIS: {text}")

    if not _check_tts():
        return  # Solo print, già fatto sopra

    try:
        asyncio.run(_speak_async(text))
    except RuntimeError:
        # In ambienti con event loop già attivo (es. Jupyter)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_speak_async(text))
        finally:
            loop.close()
    except Exception as e:
        print(f"[TTS] Errore sintesi vocale: {e}")


if __name__ == "__main__":
    say("Buonasera Tony. Tutti i sistemi operativi, Sir.")
