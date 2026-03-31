import asyncio
import tempfile
import time
import os
import subprocess
from pathlib import Path

try:
    import edge_tts
except:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts"])
    import edge_tts

async def text_to_speech(text: str):
    """Crea file MP3 da testo"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        temp_path = f.name
    
    communicate = edge_tts.Communicate(text, "it-IT-DiegoNeural")
    await communicate.save(temp_path)
    return temp_path

def say(text: str):
    """Parla il testo — FORZA OUTPUT AUDIO"""
    print(f"\n🎙️ JARVIS: {text}\n")
    
    try:
        # Crea file audio
        audio_file = asyncio.run(text_to_speech(text))
        
        # METODO 1: Usa PowerShell per forzare l'output (Windows)
        try:
            subprocess.run([
                "powershell", "-Command",
                f"(New-Object Media.SoundPlayer '{audio_file}').PlaySync()"
            ], timeout=10)
            Path(audio_file).unlink()
            return True
        except:
            pass
        
        # METODO 2: Usa Windows explorer per aprire il file (forzato)
        try:
            os.startfile(audio_file, 'play')
            time.sleep(5)  # Aspetta riproduzione
            Path(audio_file).unlink()
            return True
        except:
            pass
        
        # METODO 3: Fallback - stampa solo testo
        print(f"[Audio non disponibile - usando testo]")
        return True
        
    except Exception as e:
        print(f"[TTS Error] {e}")
        return False

if __name__ == "__main__":
    say("Ciao Tony, sono JARVIS, sto testando l'audio")
