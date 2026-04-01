"""
JARVIS VAD System — Test Suite v2
Testa ogni fix:  VAD loop, logging, ducking, barge-in, state machine.

Esegui:
    python test_vad_system.py           # test statici
    python test_vad_system.py --mic     # + test live microfono (3s)
"""
import sys
import time
import threading
import numpy as np


# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────

def header(n, title):
    print(f"\n{'='*55}")
    print(f"  TEST {n}: {title}")
    print(f"{'='*55}")


def ok(msg):
    print(f"  PASS  {msg}")

def fail(msg):
    print(f"  FAIL  {msg}")


# ──────────────────────────────────────────────────────────
# TEST 1 — SmartVAD backend + eventi
# ──────────────────────────────────────────────────────────

def test_vad_events():
    header(1, "SmartVAD — voice_start / voice_end")
    from jarvis_vad_smart import SmartVAD, SAMPLE_RATE, CHUNK_SAMPLES

    events = []
    done   = threading.Event()

    def on_start():
        events.append("start")

    def on_end(audio):
        events.append(f"end:{len(audio)/SAMPLE_RATE:.2f}s")
        done.set()

    vad = SmartVAD(on_speech_start=on_start, on_speech_end=on_end,
                   silence_duration=0.4)  # short silence for fast test
    print(f"  Backend: {vad.backend_name}")

    # Calibra con silenzio puro
    silence = np.zeros(CHUNK_SAMPLES, dtype=np.int16)
    vad.calibrate_noise(np.tile(silence, 32))

    # Feed: 5 chunk silenzio -> 25 chunk voce -> 25 chunk silenzio
    amp   = int(32767 * 0.4)
    voice = np.random.randint(-amp, amp, CHUNK_SAMPLES, dtype=np.int16)
    for _ in range(5):   vad.process_chunk(silence)
    for _ in range(25):  vad.process_chunk(voice)
    for _ in range(30):  vad.process_chunk(silence)

    done.wait(timeout=2)

    if "start" in events:
        ok(f"voice_start rilevato")
    else:
        fail("voice_start NON rilevato (threshold troppo alto?)")

    end_events = [e for e in events if e.startswith("end:")]
    if end_events:
        ok(f"voice_end rilevato: {end_events[0]}")
    else:
        fail("voice_end NON rilevato")

    return bool(events)


# ──────────────────────────────────────────────────────────
# TEST 2 — Audio ducking con mock pygame
# ──────────────────────────────────────────────────────────

def test_audio_ducking():
    header(2, "Audio ducking — duck_music() con musica simulata")
    import jarvis_voice as jv

    volume_log = []

    # Mock MUSIC_CH
    class MockChannel:
        def __init__(self):
            self._vol = jv.MUSIC_VOL_NORMAL
        def get_busy(self):
            return True
        def get_volume(self):
            return self._vol
        def set_volume(self, v):
            self._vol = v
            volume_log.append(round(v, 3))
        def play(self, *a, **k): pass
        def stop(self): pass

    mock_ch = MockChannel()
    original_ch = jv.MUSIC_CH
    original_loaded = jv._music_loaded

    jv.MUSIC_CH      = mock_ch
    jv._music_loaded = True

    # Duck
    jv.duck_music(ducked=True)
    final_duck = mock_ch._vol

    # Restore
    jv.duck_music(ducked=False)
    final_restore = mock_ch._vol

    jv.MUSIC_CH      = original_ch
    jv._music_loaded = original_loaded

    print(f"  Volume log: {volume_log}")

    if final_duck < 0.3:
        ok(f"Duck OK -> volume finale: {final_duck:.2f}")
    else:
        fail(f"Duck NON ha abbassato abbastanza: {final_duck:.2f}")

    if final_restore > 0.5:
        ok(f"Restore OK -> volume finale: {final_restore:.2f}")
    else:
        fail(f"Restore NON ha alzato abbastanza: {final_restore:.2f}")

    return final_duck < 0.3 and final_restore > 0.5


# ──────────────────────────────────────────────────────────
# TEST 3 — say() con stop_event (barge-in durante TTS gen)
# ──────────────────────────────────────────────────────────

def test_say_stop_event():
    header(3, "say() — stop_event interrompe prima del playback")
    import jarvis_voice as jv

    # Patch create_audio_file per evitare subprocess reale
    original_create = jv.create_audio_file
    original_say_fn  = jv.say

    def mock_create(text, stop_event=None):
        # Simula 0.3s di generazione TTS, controllando stop_event
        for _ in range(6):
            if stop_event and stop_event.is_set():
                print("  [mock TTS] Interrotto durante generazione")
                return None
            time.sleep(0.05)
        return "fake_audio.wav"

    jv.create_audio_file = mock_create

    stop = threading.Event()
    interrupted = threading.Event()

    def run_say():
        result = jv.say("test barge in", duck=False, stop_event=stop)
        if not result:
            interrupted.set()

    t = threading.Thread(target=run_say)
    t.start()

    # Attendi 0.1s poi setta barge-in
    time.sleep(0.1)
    stop.set()

    t.join(timeout=2)
    jv.create_audio_file = original_create

    if interrupted.is_set():
        ok("say() interrotto correttamente da stop_event")
        return True
    else:
        fail("say() NON interrotto da stop_event")
        return False


# ──────────────────────────────────────────────────────────
# TEST 4 — State machine agent
# ──────────────────────────────────────────────────────────

def test_state_machine():
    header(4, "State machine — transizioni IDLE/PROCESSING/SPEAKING")
    import jarvis_voice as jv
    jv.say                 = lambda t, duck=True, stop_event=None: (
        print(f"  [TTS mock] {t}") or True
    )
    jv.play_background_music = lambda: None

    import jarvis_agent_refactored as am
    am.say                 = jv.say
    am.play_background_music = jv.play_background_music

    from jarvis_agent_refactored import JarvisAgent, S_IDLE, S_PROCESSING, S_SPEAKING
    agent = JarvisAgent()

    states_seen = []
    original_set = agent._set_state
    def tracking_set(s):
        states_seen.append(s)
        original_set(s)
    agent._set_state = tracking_set

    # Process normale
    ok_result = agent._process_utterance("come stai?")
    assert ok_result is True, "_process_utterance deve ritornare True"
    ok(f"_process_utterance('come stai?') = True")
    print(f"  Stati visitati: {states_seen}")

    if S_PROCESSING in states_seen:
        ok("Stato PROCESSING visitato")
    else:
        fail("Stato PROCESSING NON visitato")

    if S_SPEAKING in states_seen:
        ok("Stato SPEAKING visitato")
    else:
        fail("Stato SPEAKING NON visitato")

    # Exit
    states_seen.clear()
    exit_result = agent._process_utterance("exit")
    assert exit_result is False
    ok("_process_utterance('exit') = False")

    return True


# ──────────────────────────────────────────────────────────
# TEST 5 — Barge-in durante PROCESSING (Ollama abort)
# ──────────────────────────────────────────────────────────

def test_barge_in_processing():
    header(5, "Barge-in durante PROCESSING — Ollama abortito")
    import jarvis_voice as jv
    jv.say                 = lambda t, duck=True, stop_event=None: True
    jv.play_background_music = lambda: None

    import jarvis_agent_refactored as am
    am.say                 = jv.say
    am.play_background_music = jv.play_background_music

    from jarvis_agent_refactored import JarvisAgent
    import jarvis_brain as brain

    # Simula Ollama lento (3s)
    original_process = brain.process_input
    def slow_process(text):
        time.sleep(3)
        return "risposta lenta"
    brain.process_input = slow_process
    am.process_input    = slow_process

    agent = JarvisAgent()
    result = [None]
    done   = threading.Event()

    def run_process():
        result[0] = agent._process_utterance("domanda lenta")
        done.set()

    t = threading.Thread(target=run_process)
    t.start()

    # Aspetta che entri in PROCESSING, poi barge-in
    time.sleep(0.3)
    print(f"  Stato attuale: {agent._get_state()}")
    agent._on_barge_in()

    done.wait(timeout=1.5)
    brain.process_input = original_process
    am.process_input    = original_process

    if done.is_set():
        ok(f"_process_utterance terminato in <1.5s (non ha aspettato 3s Ollama)")
        return True
    else:
        fail("_process_utterance ancora in corso dopo 1.5s — barge-in NON ha abortito Ollama")
        return False


# ──────────────────────────────────────────────────────────
# TEST 6 — Loop continuo non si blocca
# ──────────────────────────────────────────────────────────

def test_continuous_loop():
    header(6, "Loop continuo — 3 utterance consecutive senza blocco")
    import jarvis_voice as jv
    jv.say                 = lambda t, duck=True, stop_event=None: True
    jv.play_background_music = lambda: None

    import jarvis_agent_refactored as am
    am.say                 = jv.say
    am.play_background_music = jv.play_background_music
    am.process_input       = lambda t: f"risposta a: {t}"
    am.add_to_memory       = lambda u, r: None

    from jarvis_agent_refactored import JarvisAgent
    agent = JarvisAgent()

    processed = []
    original_process = agent._process_utterance
    def tracked_process(text):
        r = original_process(text)
        processed.append(text)
        return r
    agent._process_utterance = tracked_process

    # Metti 3 utterance in queue
    for phrase in ["prima domanda", "seconda domanda", "terza domanda"]:
        agent._transcript_queue.put(phrase)
    # Metti exit per terminare il loop
    agent._transcript_queue.put("exit")

    # Avvia run_continuous senza listener reale
    agent._listener = type("FakeListener", (), {
        "backend_name": "mock",
        "start": lambda self: None,
        "stop":  lambda self: None,
        "reset_vad": lambda self: None,
    })()

    # Patch intro_sequence per non fare TTS
    agent.intro_sequence = lambda: None

    t = threading.Thread(target=agent.run_continuous, daemon=True)
    t.start()
    t.join(timeout=10)

    print(f"  Utterance processate: {processed}")

    if len(processed) >= 3:
        ok(f"Tutte e 3 le utterance processate in sequenza")
        return True
    else:
        fail(f"Solo {len(processed)}/3 utterance processate — loop bloccato?")
        return False


# ──────────────────────────────────────────────────────────
# TEST 7 — Mic live (opzionale)
# ──────────────────────────────────────────────────────────

def test_mic_live():
    header(7, "Mic live — 4 secondi di ascolto reale")
    from jarvis_listener import JarvisListener

    if not JarvisListener.is_mic_available():
        print("  SKIP: microfono non disponibile.")
        return True

    received = []

    listener = JarvisListener(on_transcript=lambda t: received.append(t))
    listener.start()

    print("  Parla al microfono per 4 secondi...")
    time.sleep(4)
    listener.stop()

    print(f"  Transcript ricevuti: {len(received)}")
    ok("Listener avviato e fermato senza crash.")
    return True


# ──────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        ("SmartVAD eventi",           test_vad_events),
        ("Audio ducking",             test_audio_ducking),
        ("say() stop_event",          test_say_stop_event),
        ("State machine",             test_state_machine),
        ("Barge-in processing abort", test_barge_in_processing),
        ("Loop continuo",             test_continuous_loop),
    ]

    if "--mic" in sys.argv:
        tests.append(("Mic live", test_mic_live))

    passed = 0
    for name, fn in tests:
        try:
            ok_flag = fn()
        except Exception as e:
            print(f"  EXCEPTION: {e}")
            import traceback; traceback.print_exc()
            ok_flag = False
        passed += int(bool(ok_flag))

    print(f"\n{'='*55}")
    print(f"  Risultati: {passed}/{len(tests)} PASS")
    if passed == len(tests):
        print("  TUTTI I TEST PASSATI.")
    else:
        print(f"  {len(tests)-passed} TEST FALLITI — vedi output sopra.")
    print("="*55)
    sys.exit(0 if passed == len(tests) else 1)
