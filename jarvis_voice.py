"""
JARVIS Voice — Edge-TTS + pygame audio con ducking corretto.
Fixes v2:
  - duck_music() controlla get_busy() prima di set_volume
  - say() controlla stop_event sia DURANTE generazione TTS sia durante playback
  - Volume ramp smooth (10 step × 5ms = 50ms)
  - Logging visibile in console
"""
import hashlib
import subprocess
import threading
import pygame
import time
from pathlib import Path

# ── Init pygame mixer ──────────────────────────────────────
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
pygame.mixer.init()

MUSIC_CH = pygame.mixer.Channel(0)   # musica di sottofondo
VOICE_CH = pygame.mixer.Channel(1)   # voce JARVIS

MUSIC_VOL_NORMAL = 0.70
MUSIC_VOL_DUCKED = 0.15

MUSIC_FILE = Path("backInBlack.mp3")
_music_loaded = False   # track se la musica è stata caricata

# ──────────────────────────────────────────────────────────

def _ramp_volume(channel: pygame.mixer.Channel, start: float, end: float,
                 steps: int = 8, total_ms: int = 40):
    """Volume ramp smooth senza bloccare per più di total_ms."""
    if start == end:
        return
    step_vol  = (end - start) / steps
    step_time = total_ms / 1000.0 / steps
    for i in range(1, steps + 1):
        channel.set_volume(start + step_vol * i)
        time.sleep(step_time)


def play_background_music() -> bool:
    global _music_loaded
    if not MUSIC_FILE.exists():
        print(f"[MUSIC] File non trovato: {MUSIC_FILE.resolve()}")
        return False
    try:
        sound = pygame.mixer.Sound(str(MUSIC_FILE))
        MUSIC_CH.play(sound, loops=-1)
        MUSIC_CH.set_volume(MUSIC_VOL_NORMAL)
        _music_loaded = True
        print(f"[MUSIC] Back in Black avviato (vol={MUSIC_VOL_NORMAL})")
        return True
    except Exception as e:
        print(f"[MUSIC ERROR] {e}")
        return False


def duck_music(ducked: bool = True):
    """Abbassa/alza volume musica. No-op se la musica non sta suonando."""
    if not _music_loaded or not MUSIC_CH.get_busy():
        return

    current = MUSIC_CH.get_volume()
    target  = MUSIC_VOL_DUCKED if ducked else MUSIC_VOL_NORMAL
    direction = "v DUCK" if ducked else "^ RESTORE"
    print(f"[AUDIO_DUCK] {direction}  {current:.2f} -> {target:.2f}")
    _ramp_volume(MUSIC_CH, current, target)


def create_audio_file(text: str, stop_event=None) -> str | None:
    """
    Genera TTS con edge-tts. Salva in audio_cache/ (cache permanente).
    stop_event: se settato prima/durante la generazione, ritorna None immediatamente.
    """
    audio_dir = Path("audio_cache")
    audio_dir.mkdir(exist_ok=True)

    file_hash  = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
    audio_file = audio_dir / f"tts_{file_hash}.wav"

    if audio_file.exists():
        return str(audio_file)

    # Controlla barge-in prima ancora di avviare subprocess
    if stop_event and stop_event.is_set():
        print("[TTS] Generazione saltata (barge-in pre-TTS).")
        return None

    try:
        cmd = [
            "edge-tts",
            "--voice", "it-IT-DiegoNeural",
            "--rate", "+10%",
            "--text", text,
            "--write-media", str(audio_file),
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Attendi completamento controllando stop_event ogni 100ms
        while proc.poll() is None:
            if stop_event and stop_event.is_set():
                proc.kill()
                print("[TTS] Generazione interrotta (barge-in durante TTS gen).")
                return None
            time.sleep(0.1)

        if proc.returncode != 0:
            print(f"[TTS ERROR] edge-tts returncode={proc.returncode}")
            return None

        return str(audio_file)

    except FileNotFoundError:
        print("[TTS ERROR] edge-tts non trovato. Installa: pip install edge-tts")
        return None
    except Exception as e:
        print(f"[TTS ERROR] {e}")
        return None


def say(text: str, duck: bool = True, stop_event=None) -> bool:
    """
    Parla il testo con Edge-TTS DiegoNeural italiano.

    stop_event (threading.Event): se settato, interrompe immediatamente
    (durante generazione TTS E durante playback).
    """
    print(f"\n[JARVIS_SPEAKING] \"{text}\"")

    # Controlla barge-in prima di fare qualsiasi cosa
    if stop_event and stop_event.is_set():
        print("[JARVIS_SPEAKING] Saltato (stop_event già attivo).")
        return False

    # 1. Duck musica (immediato)
    if duck:
        duck_music(ducked=True)

    # 2. Genera audio TTS (passa stop_event per abort immediato)
    audio_file = create_audio_file(text, stop_event=stop_event)

    # Controlla di nuovo dopo generazione TTS
    if stop_event and stop_event.is_set():
        if duck:
            duck_music(ducked=False)
        return False

    # 3. Playback
    played = False
    if audio_file and Path(audio_file).exists():
        try:
            sound = pygame.mixer.Sound(audio_file)
            VOICE_CH.play(sound)
            played = True
            print(f"[JARVIS_SPEAKING] Playback avviato.")

            # Loop con check barge-in ogni 30ms
            while VOICE_CH.get_busy():
                if stop_event and stop_event.is_set():
                    VOICE_CH.stop()
                    print("[JARVIS_SPEAKING] Playback interrotto (barge-in).")
                    played = False
                    break
                time.sleep(0.03)

        except Exception as e:
            print(f"[PLAY ERROR] {e}")
    else:
        print(f"[JARVIS_SPEAKING] File audio non disponibile: {audio_file}")

    # 4. Restore musica
    if duck:
        duck_music(ducked=False)

    return played
