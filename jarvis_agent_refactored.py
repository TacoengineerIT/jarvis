"""
JARVIS Agent v2 — Loop continuo con state machine esplicita.

State machine:
  [IDLE] → rileva voce → [LISTENING]
  [LISTENING] → utterance completa → [PROCESSING]  (Whisper + Ollama)
  [PROCESSING] → risposta pronta → [SPEAKING]       (TTS + ducking)
  [SPEAKING] → fine TTS → [IDLE]
  Qualsiasi stato → barge-in → [IDLE]

Fixes v2:
  - reset_vad() SOLO su barge-in (non dopo ogni utterance)
  - Ollama gira in thread separato → abort in <100ms su barge-in
  - stop_event passato a say() per barge-in immediato
  - Logging di ogni transizione di stato
  - Loop non si ferma mai tranne su exit/KeyboardInterrupt
"""
import queue
import random
import signal
import threading
import time
from typing import Optional

from jarvis_config import config
from jarvis_brain import process_input, is_ollama_available
from jarvis_voice import say, play_background_music
from memory_manager import add_to_memory
from jarvis_wakeword import WakeWordDetector

# ──────────────────────────────────────────────────────────
# FRASI
# ──────────────────────────────────────────────────────────

INTRO_VARIANTS = [
    "Oggi sono particolarmente utile con i suoi appunti universitari.",
    "Posso cercare qualsiasi cosa su internet in tempo reale.",
    "Controllo completo del suo PC. La prego, niente 47 tab aperti su Chrome.",
    "Sistema operativo ottimizzato per la procrastinazione... scherzo Sir.",
]

FAREWELLS = [
    "Arrivederci Tony. Cercherò di non annoiarmi troppo.",
    "Sistemi in standby. Si faccia vedere ogni tanto, Sir.",
    "Buona fortuna con quel codice, Sir. Torni quando ha problemi.",
]

EXIT_KEYWORDS = ["exit", "quit", "ciao jarvis", "arrivederci jarvis", "spegniti"]

# ──────────────────────────────────────────────────────────
# STATE MACHINE
# ──────────────────────────────────────────────────────────

S_IDLE             = "IDLE"
S_PASSIVE_LISTENING = "PASSIVE_LISTENING"
S_ACTIVE_LISTENING  = "ACTIVE_LISTENING"
S_LISTENING        = "LISTENING"
S_PROCESSING       = "PROCESSING"
S_SPEAKING         = "SPEAKING"


class JarvisAgent:

    def __init__(self):
        self.history: list = []

        # State machine
        self._state = S_IDLE
        self._state_lock = threading.Lock()

        # Barge-in / abort
        self._stop_event  = threading.Event()   # interrompe TTS playback
        self._abort_event = threading.Event()   # interrompe Ollama processing

        # Transcript queue (dal listener)
        self._transcript_queue: queue.Queue[str] = queue.Queue()

        self._listener = None
        self._should_exit = False

        # Wake word
        self._wakeword = WakeWordDetector()
        self._active_until = 0.0  # timestamp: active listening expires
        self._active_timeout = 10.0  # seconds of active listening after wake word

    # ── State machine ─────────────────────────────────────

    def _set_state(self, new_state: str):
        with self._state_lock:
            old = self._state
            self._state = new_state
        if old != new_state:
            print(f"\n[STATE] {old} -> {new_state}")

    def _get_state(self) -> str:
        with self._state_lock:
            return self._state

    # ── Predicati per listener ────────────────────────────

    def _is_speaking(self) -> bool:
        return self._get_state() == S_SPEAKING

    def _is_busy(self) -> bool:
        """True se JARVIS sta elaborando o parlando (non IDLE/LISTENING)."""
        return self._get_state() in (S_PROCESSING, S_SPEAKING)

    # ── Barge-in ──────────────────────────────────────────

    def _on_barge_in(self):
        state = self._get_state()
        print(f"[BARGE_IN] Interrompo stato: {state}")

        # Ferma TTS se sta parlando
        self._stop_event.set()
        # Cancella elaborazione Ollama se sta processando
        self._abort_event.set()

    def _on_transcript(self, text: str):
        """Callback dal listener — mette in queue."""
        self._transcript_queue.put(text)

    # ── TTS wrapper ───────────────────────────────────────

    def _say(self, text: str, duck: bool = True):
        self._set_state(S_SPEAKING)
        self._stop_event.clear()
        try:
            say(text, duck=duck, stop_event=self._stop_event)
        finally:
            self._set_state(S_IDLE)
            print(f"[IDLE] In ascolto — parla liberamente Sir.")

    # ── Ollama in thread abortable ────────────────────────

    def _run_ollama(self, text: str) -> Optional[str]:
        """
        Esegue process_input() in un thread daemon.
        Controlla _abort_event ogni 100ms.
        Ritorna None se abortito.
        """
        result: list = [None]
        done = threading.Event()

        def worker():
            try:
                result[0] = process_input(text)
            except Exception as e:
                print(f"[OLLAMA ERROR] {e}")
            finally:
                done.set()

        t = threading.Thread(target=worker, daemon=True, name="jarvis-ollama")
        t.start()
        print(f"[OLLAMA_THINKING] Elaboro: \"{text}\"")

        while not done.wait(timeout=0.1):
            if self._abort_event.is_set():
                print("[OLLAMA_THINKING] Abortito (barge-in durante processing).")
                return None

        return result[0]

    # ── Intro ─────────────────────────────────────────────

    def intro_sequence(self):
        play_background_music()
        time.sleep(2.5)
        print("\n" + "="*55)
        print("  JARVIS v2 — Continuous Listening Mode")
        print("="*55)
        self._say("Buonasera, Tony.", duck=False)
        time.sleep(0.1)
        self._say("Sono JARVIS, il suo sistema di intelligenza artificiale personale.")
        time.sleep(0.1)
        self._say(random.choice(INTRO_VARIANTS))
        time.sleep(0.1)
        self._say("Tutti i sistemi operativi, Sir. Come posso assisterla?")

    # ── Processa un utterance ─────────────────────────────

    def _process_utterance(self, text: str) -> bool:
        """
        Gestisce una singola utterance.
        Ritorna False se si deve uscire.
        """
        # Ignora utterance vuote o rumore
        text = text.strip()
        if not text or len(text) < 2:
            print(f"[PROCESSING] Utterance troppo corta, ignoro: {text!r}")
            return True

        # Exit
        if any(kw in text.lower() for kw in EXIT_KEYWORDS):
            print("[STATE] EXIT richiesto.")
            farewell = random.choice(FAREWELLS)
            self._say(farewell)
            return False

        # Processing
        self._set_state(S_PROCESSING)
        self._abort_event.clear()

        response = self._run_ollama(text)

        # Abortito durante processing → torna IDLE e riascolta
        if response is None or self._abort_event.is_set():
            self._abort_event.clear()
            self._set_state(S_IDLE)
            print(f"[IDLE] Processing annullato. In ascolto.")
            return True

        # Salva memoria
        add_to_memory(text, response)
        self.history.append({"user": text, "response": response, "ts": time.time()})
        if len(self.history) > 20:
            self.history.pop(0)

        # Parla risposta
        self._say(response, duck=True)
        return True

    # ── Wake word support ───────────────────────────────

    def _on_wake_word(self):
        """Called when wake word detected. Activates listening for _active_timeout seconds."""
        self._active_until = time.time() + self._active_timeout
        self._set_state(S_ACTIVE_LISTENING)
        print(f"[WAKEWORD] Ascolto attivo per {self._active_timeout}s")

    def _is_active_listening(self) -> bool:
        """True if in active listening window (wake word was recently detected)."""
        if not self._wakeword.available:
            return True  # No wake word → always active
        return time.time() < self._active_until

    def _check_active_timeout(self):
        """Check if active listening has timed out, return to passive."""
        if not self._wakeword.available:
            return
        if self._get_state() == S_ACTIVE_LISTENING and time.time() >= self._active_until:
            self._set_state(S_PASSIVE_LISTENING)
            print("[WAKEWORD] Timeout ascolto attivo — torno in ascolto passivo.")

    # ── MODALITÀ 1: Continuous VAD ────────────────────────

    def run_continuous(self):
        """
        Main loop con ascolto VAD continuo.
        Non si blocca mai — elabora una utterance alla volta dalla queue.
        Il listener gira in background H24.
        With wake word: PASSIVE_LISTENING → wake word → ACTIVE_LISTENING → timeout → PASSIVE_LISTENING
        Without wake word: always active (backward compatible).
        """
        from jarvis_listener import JarvisListener

        self._listener = JarvisListener(
            on_transcript=self._on_transcript,
            on_barge_in=self._on_barge_in,
            is_speaking_fn=self._is_speaking,
        )

        # Wire wake word into listener if available
        if self._wakeword.available:
            self._listener.set_wakeword_detector(self._wakeword, self._on_wake_word)

        print(f"[INIT] Avvio listener VAD (backend: {self._listener.backend_name})")
        if self._wakeword.available:
            print("[INIT] Wake word 'Hey JARVIS' attivo.")
        else:
            print("[INIT] Wake word non disponibile — ascolto continuo.")
        self._listener.start()

        # Aspetta calibrazione completata (~1s) poi intro
        time.sleep(1.2)
        self.intro_sequence()

        initial_state = S_PASSIVE_LISTENING if self._wakeword.available else S_IDLE
        self._set_state(initial_state)
        # If wake word is active, set always-active so first speech works after intro
        if self._wakeword.available:
            self._active_until = time.time() + self._active_timeout
            self._set_state(S_ACTIVE_LISTENING)
        print(f"\n[IDLE] Ascolto continuo attivo. CTRL+C per uscire.")

        while not self._should_exit:
            try:
                # Check active listening timeout (wake word mode)
                self._check_active_timeout()

                # Recupera prossima utterance (timeout 0.3s per poter controllare should_exit)
                try:
                    text = self._transcript_queue.get(timeout=0.3)
                except queue.Empty:
                    continue

                # In wake word mode, ignore transcripts when in passive listening
                if self._wakeword.available and not self._is_active_listening():
                    if self._get_state() == S_PASSIVE_LISTENING:
                        print(f"[WAKEWORD] Ignorata utterance in ascolto passivo: {text!r}")
                        continue

                # Se è arrivata una barge-in mentre eravamo in queue.get(),
                # il barge-in ha già abortito il processing precedente.
                # Svuota utterance residue accumulate durante SPEAKING/PROCESSING.
                cur_state = self._get_state()
                if cur_state not in (S_IDLE, S_ACTIVE_LISTENING):
                    print(f"[QUEUE] Utterance ricevuta in stato {cur_state}, accodo.")

                # Processa
                should_continue = self._process_utterance(text)
                if not should_continue:
                    self._should_exit = True
                    break

                # Dopo ogni utterance: reset barge-in events (non il VAD — si resetta da solo)
                self._stop_event.clear()
                self._abort_event.clear()

            except KeyboardInterrupt:
                print("\n[EXIT] CTRL+C ricevuto.")
                self._say("Sistemi in standby. Goodbye Sir.")
                self._should_exit = True
                break
            except Exception as e:
                print(f"\n[ERROR] Eccezione nel loop principale: {e}")
                import traceback; traceback.print_exc()
                self._set_state(S_IDLE)
                # Non uscire — riprova
                time.sleep(0.5)

        if self._listener:
            self._listener.stop()
        print("[EXIT] JARVIS fermato.")

    # ── MODALITÀ 2: CLI testuale (fallback) ───────────────

    def run(self):
        """Fallback testo quando microfono non disponibile."""
        self.intro_sequence()
        print("\n[CLI] Modalità testo. Scrivi comandi o 'voce' per input vocale.")

        while True:
            try:
                raw = input("\nTony> ").strip()
                if not raw:
                    continue

                if any(kw in raw.lower() for kw in EXIT_KEYWORDS):
                    self._say(random.choice(FAREWELLS))
                    break

                if raw.lower() == "voce":
                    try:
                        from jarvis_voice_input import listen_and_transcribe
                        print("[CLI] Ascolto Sir (5s)...")
                        raw = listen_and_transcribe()
                        if not raw:
                            continue
                        print(f"[USER_SPEECH] \"{raw}\"")
                    except Exception as e:
                        print(f"[CLI ERROR] {e}")
                        continue

                if not self._process_utterance(raw):
                    break

            except KeyboardInterrupt:
                self._say("Sistemi in standby. Goodbye Sir.")
                break
            except Exception as e:
                print(f"\n[ERROR] {e}")

    # ── Auto-select ───────────────────────────────────────

    def run_auto(self):
        """Prova VAD continuo, fallback a CLI se mic non disponibile."""
        try:
            from jarvis_listener import JarvisListener
            if JarvisListener.is_mic_available():
                self.run_continuous()
                return
            print("[INIT] Microfono non rilevato.")
        except Exception as e:
            print(f"[INIT] Errore microfono: {e}")

        print("[INIT] Avvio modalità testo.")
        self.run()


# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    agent = JarvisAgent()

    # Graceful shutdown on SIGINT/SIGTERM
    def _shutdown_handler(signum, frame):
        print(f"\n[SIGNAL] Ricevuto segnale {signum}. Shutdown...")
        agent._should_exit = True
        if agent._listener:
            agent._listener.stop()

    signal.signal(signal.SIGINT, _shutdown_handler)
    signal.signal(signal.SIGTERM, _shutdown_handler)

    agent.run_auto()
