"""
Integration tests for JARVIS.
CRITICAL: All audio I/O is mocked — no real mic, no real speaker, no real pygame playback.
"""
import threading
import time
import queue
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


@pytest.fixture(autouse=True)
def _mock_agent_audio():
    """
    Mock say/play_background_music for agent tests.
    Uses patch to ensure originals are restored after each test.
    """
    import jarvis_voice as jv
    import jarvis_agent_refactored as agent_mod

    mock_say = lambda t, duck=True, stop_event=None: True
    mock_music = lambda: None

    with patch.object(jv, "say", mock_say), \
         patch.object(jv, "play_background_music", mock_music), \
         patch.object(agent_mod, "say", mock_say), \
         patch.object(agent_mod, "play_background_music", mock_music), \
         patch.object(agent_mod, "add_to_memory", lambda u, r: None):
        yield


class TestFullCommandPipeline:

    @patch("jarvis_brain.is_ollama_available", return_value=False)
    @patch("subprocess.Popen")
    @patch("webbrowser.open")
    def test_apri_chrome_pipeline(self, mock_web, mock_popen, mock_ollama):
        """Simulate transcription 'apri chrome' → verify action fires."""
        import jarvis_brain as brain

        result = brain.process_input("apri chrome")
        assert result is not None
        assert "chrome" in result.lower()

    @patch("jarvis_brain.is_ollama_available", return_value=False)
    @patch("subprocess.Popen")
    @patch("webbrowser.open")
    def test_apri_youtube_pipeline(self, mock_web, mock_popen, mock_ollama):
        """Simulate 'apri youtube' → verify webbrowser action."""
        import jarvis_brain as brain

        result = brain.process_input("apri youtube")
        assert result is not None
        assert "youtube" in result.lower()


class TestFinancePipeline:

    def test_situazione_affitto_returns_amount(self, tmp_path):
        """'situazione affitto' → TTS string contains euro amount."""
        import finance_engine as fe
        with patch.object(fe, "FINANCE_FILE", tmp_path / "config" / "finances.json"):
            fe.update_finances(50.0)

            import jarvis_brain as brain
            with patch("jarvis_brain.is_ollama_available", return_value=False):
                result = brain.process_input("situazione affitto")

            assert result is not None
            assert "euro" in result.lower()

    def test_report_finanziario(self, tmp_path):
        """'report finanziario' → detailed report."""
        import finance_engine as fe
        with patch.object(fe, "FINANCE_FILE", tmp_path / "config" / "finances.json"):
            fe.update_finances(75.0)

            import jarvis_brain as brain
            with patch("jarvis_brain.is_ollama_available", return_value=False):
                result = brain.process_input("report finanziario")

            assert result is not None
            assert "sir" in result.lower() or "euro" in result.lower()


class TestStateMachine:

    def test_state_transitions(self):
        """Verify IDLE → PROCESSING → SPEAKING → IDLE cycle."""
        import jarvis_agent_refactored as agent_mod
        from jarvis_agent_refactored import JarvisAgent, S_IDLE, S_PROCESSING, S_SPEAKING

        agent = JarvisAgent()
        states_seen = []
        original_set = agent._set_state

        def tracking_set(s):
            states_seen.append(s)
            original_set(s)
        agent._set_state = tracking_set

        with patch.object(agent_mod, "process_input", return_value="Risposta mock"):
            result = agent._process_utterance("test input")

        assert result is True
        assert S_PROCESSING in states_seen
        assert S_SPEAKING in states_seen
        assert states_seen[-1] == S_IDLE  # Should end in IDLE

    def test_exit_command(self):
        """Exit keywords should return False."""
        from jarvis_agent_refactored import JarvisAgent
        agent = JarvisAgent()

        for keyword in ["exit", "quit", "ciao jarvis", "spegniti"]:
            result = agent._process_utterance(keyword)
            assert result is False, f"'{keyword}' should trigger exit"


class TestStartupSequence:

    def test_intro_variants_not_empty(self):
        """Startup phrases list should have multiple variants."""
        from jarvis_agent_refactored import INTRO_VARIANTS, FAREWELLS
        assert len(INTRO_VARIANTS) >= 3
        assert len(FAREWELLS) >= 2

    def test_intro_variants_all_strings(self):
        """All intro variants should be non-empty strings."""
        from jarvis_agent_refactored import INTRO_VARIANTS
        for v in INTRO_VARIANTS:
            assert isinstance(v, str)
            assert len(v) > 10

    def test_intro_sequence_calls_say(self):
        """intro_sequence should call say() multiple times."""
        import jarvis_agent_refactored as agent_mod

        call_count = [0]
        original_say = agent_mod.say

        def counting_say(t, duck=True, stop_event=None):
            call_count[0] += 1
            return True

        from jarvis_agent_refactored import JarvisAgent
        agent = JarvisAgent()

        with patch.object(agent_mod, "say", counting_say):
            agent.intro_sequence()

        assert call_count[0] >= 4, f"Intro should call say() at least 4 times, got {call_count[0]}"


class TestBargeInDuringProcessing:

    def test_ollama_abort(self):
        """Barge-in during processing should abort Ollama and return to IDLE."""
        import jarvis_agent_refactored as agent_mod
        from jarvis_agent_refactored import JarvisAgent, S_IDLE

        # Simulate slow Ollama (2s)
        def slow_process(text):
            time.sleep(2)
            return "slow response"

        agent = JarvisAgent()
        result_holder = [None]
        done = threading.Event()

        def run():
            result_holder[0] = agent._process_utterance("slow query")
            done.set()

        with patch.object(agent_mod, "process_input", slow_process):
            t = threading.Thread(target=run, daemon=True)
            t.start()

            # Wait for PROCESSING state, then barge in
            time.sleep(0.2)
            agent._on_barge_in()

            done.wait(timeout=1.5)

        assert done.is_set(), "Processing should have been aborted within 1.5s"
        assert result_holder[0] is True  # _process_utterance returns True (not exit)
        assert agent._get_state() == S_IDLE


class TestWakeWordToCommand:

    def test_wakeword_activates_listening(self):
        """Wake word detection should set active listening state."""
        from jarvis_agent_refactored import JarvisAgent, S_ACTIVE_LISTENING

        agent = JarvisAgent()

        # Simulate wake word unavailable → always active
        agent._wakeword._available = False
        assert agent._is_active_listening() is True

    def test_wakeword_timeout(self):
        """Active listening should timeout and return to passive."""
        from jarvis_agent_refactored import JarvisAgent, S_PASSIVE_LISTENING, S_ACTIVE_LISTENING

        agent = JarvisAgent()
        # Simulate wake word available
        agent._wakeword._available = True
        agent._active_timeout = 0.1  # Very short timeout
        agent._on_wake_word()
        assert agent._get_state() == S_ACTIVE_LISTENING

        time.sleep(0.2)
        agent._check_active_timeout()
        assert agent._get_state() == S_PASSIVE_LISTENING

    def test_transcript_ignored_in_passive(self):
        """Transcripts during passive listening should be ignored."""
        from jarvis_agent_refactored import JarvisAgent, S_PASSIVE_LISTENING

        agent = JarvisAgent()
        # In passive mode with wakeword available, is_active_listening returns False
        agent._wakeword._available = True
        agent._active_until = 0  # Expired
        assert agent._is_active_listening() is False


class TestHomeCommandPipeline:

    @patch("jarvis_brain.requests.post")
    @patch("jarvis_brain.is_ollama_available", return_value=False)
    def test_accendi_luce_pipeline(self, mock_ollama, mock_post):
        """'accendi luce camera' should trigger HA turn_on (when configured)."""
        import jarvis_brain as brain
        import jarvis_home as home

        mock_post.return_value = MagicMock(status_code=200)

        # Create a configured bridge
        mock_bridge = MagicMock()
        mock_bridge.available = True
        mock_bridge.turn_on.return_value = "Ho acceso luce camera, Sir."

        with patch.object(home, "_bridge", mock_bridge), \
             patch("jarvis_brain.get_ha_bridge", return_value=mock_bridge):
            result = brain.process_input("accendi luce camera")

        assert result is not None
        assert "acceso" in result.lower() or "luce" in result.lower()

    @patch("jarvis_brain.is_ollama_available", return_value=False)
    def test_home_command_when_unconfigured(self, mock_ollama):
        """Home commands should gracefully handle unconfigured HA."""
        import jarvis_brain as brain
        import jarvis_home as home

        mock_bridge = MagicMock()
        mock_bridge.available = False

        with patch("jarvis_brain.get_ha_bridge", return_value=mock_bridge):
            # Should fall through to other handlers since HA is unavailable
            result = brain.process_input("accendi luce camera")
            assert result is not None


class TestSTTPipeline:

    def test_transcribe_audio_mock(self):
        """STT module should transcribe audio (mocked model)."""
        import jarvis_stt as stt

        mock_model = MagicMock()
        seg = MagicMock()
        seg.text = "apri chrome"
        mock_model.transcribe.return_value = (iter([seg]), MagicMock())

        stt._model = mock_model
        stt._model_loaded = True

        try:
            audio = np.random.randint(-1000, 1000, 16000, dtype=np.int16)
            text = stt.transcribe_audio(audio)
            assert text == "apri chrome"
        finally:
            stt._model = None
            stt._model_loaded = False
