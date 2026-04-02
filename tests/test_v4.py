"""
tests/test_v4.py — JARVIS v4.0 Unit Tests

All external APIs (Anthropic, Google STT, Tuya) are mocked.
Run: python -m pytest tests/test_v4.py -v
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ------------------------------------------------------------------ #
# Memory tests                                                         #
# ------------------------------------------------------------------ #

class TestJarvisMemory:
    def setup_method(self):
        from jarvis_memory import JarvisMemory
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.mem = JarvisMemory(db_path=Path(self.tmp.name))

    def test_save_and_retrieve_conversation(self):
        self.mem.save_conversation(
            user_input="Ciao JARVIS",
            jarvis_response="Buongiorno, Sir.",
            mood_detected="neutral",
            intent="greeting",
        )
        convs = self.mem.get_recent_conversations(limit=5)
        assert len(convs) == 1
        assert convs[0]["user_input"] == "Ciao JARVIS"
        assert convs[0]["jarvis_response"] == "Buongiorno, Sir."

    def test_context_summary(self):
        self.mem.save_conversation("test input", "test response")
        summary = self.mem.build_context_summary()
        assert "test input" in summary
        assert "test response" in summary

    def test_preferences(self):
        self.mem.set_preference("volume", 80)
        assert self.mem.get_preference("volume") == 80
        assert self.mem.get_preference("missing_key", "default") == "default"

    def test_mood_update(self):
        self.mem.update_mood(stress_level=5, mood="neutral", period="morning")
        today = self.mem.get_today_mood()
        assert today is not None
        assert today["morning_mood"] == "neutral"
        assert today["stress_level"] == 5

    def test_stats(self):
        self.mem.save_conversation("a", "b")
        stats = self.mem.stats()
        assert stats["conversations"] >= 1

    def test_scheduled_actions(self):
        self.mem.add_scheduled_action("7:00 AM", "suggest_walk")
        actions = self.mem.get_active_scheduled_actions()
        assert len(actions) >= 1
        assert actions[0]["trigger"] == "7:00 AM"


# ------------------------------------------------------------------ #
# Mood detector tests                                                  #
# ------------------------------------------------------------------ #

class TestMoodDetector:
    def setup_method(self):
        from jarvis_mood import MoodDetector
        self.detector = MoodDetector()

    def test_happy_keywords(self):
        result = self.detector.detect("Mi sento felice e contento oggi!")
        assert result["label"] == "happy"
        assert result["score"] > 0.5
        assert result["emoji"] == "😊"

    def test_sad_keywords(self):
        result = self.detector.detect("Sono molto stressato e depresso")
        assert result["label"] in ("sad", "stressed")
        assert result["score"] < 0.55

    @patch("jarvis_mood._temporal_score", return_value=0.55)
    def test_neutral_keywords(self, _mock_ts):
        result = self.detector.detect("Apri chrome")
        assert result["label"] == "neutral"

    def test_signals_present(self):
        result = self.detector.detect("test")
        assert "voice" in result["signals"]
        assert "temporal" in result["signals"]
        assert "keyword" in result["signals"]

    def test_stress_level_mapping(self):
        result = self.detector.detect("Sono molto stressato confuso aiuto")
        stress = self.detector.stress_level(result)
        assert 1 <= stress <= 10


# ------------------------------------------------------------------ #
# Intent classification tests                                          #
# ------------------------------------------------------------------ #

class TestIntentClassification:
    def setup_method(self):
        from jarvis_core import JarvisCore
        self.core = JarvisCore.__new__(JarvisCore)

    def _classify(self, text):
        from jarvis_core import JarvisCore
        # Use standalone function
        import jarvis_core
        obj = object.__new__(jarvis_core.JarvisCore)
        return jarvis_core.JarvisCore._classify_intent(obj, text)

    def test_git_push(self):
        assert self._classify("pusha il codice") == "git_push"

    def test_turn_on_light(self):
        assert self._classify("accendi le luci del salotto") == "turn_on_light"

    def test_turn_off(self):
        assert self._classify("spegni la lampada") == "turn_off_light"

    def test_what_time(self):
        assert self._classify("che ore sono?") == "what_time"

    def test_mood_check(self):
        assert self._classify("mi sento giù oggi") == "mood_check"

    def test_open_app(self):
        assert self._classify("apri chrome") == "open_app"

    def test_unknown(self):
        assert self._classify("xyzzy nonsense gibberish") == "unknown"


# ------------------------------------------------------------------ #
# Actions tests                                                        #
# ------------------------------------------------------------------ #

class TestJarvisActions:
    def setup_method(self):
        from jarvis_actions import JarvisActions
        config = {
            "quick_commands": {
                "test_cmd": "echo hello"
            }
        }
        self.actions = JarvisActions(config)

    def test_what_time(self):
        result = asyncio.run(self.actions.execute("what_time", "che ore sono"))
        assert result is not None
        assert "Sir" in result

    def test_what_date(self):
        result = asyncio.run(self.actions.execute("what_date", "che giorno è"))
        assert result is not None
        assert "Sir" in result

    def test_add_reminder(self):
        result = asyncio.run(self.actions.execute("add_reminder", "ricorda di comprare il latte"))
        assert result is not None
        assert "latte" in result.lower()

    def test_reminder_list(self):
        asyncio.run(self.actions.execute("add_reminder", "ricorda di studiare Python"))
        reminders = self.actions.get_reminders()
        assert len(reminders) >= 1

    def test_unknown_intent_returns_none(self):
        result = asyncio.run(self.actions.execute("unknown", "qualcosa di strano"))
        assert result is None


# ------------------------------------------------------------------ #
# Home automation tests (mocked Tuya)                                  #
# ------------------------------------------------------------------ #

class TestJarvisHome:
    def setup_method(self):
        from jarvis_home import JarvisHome
        config = {
            "smart_home": {
                "devices": [
                    {
                        "alias": "luce_test",
                        "id": "fake_id_123",
                        "ip": "192.168.1.100",
                        "local_key": "fake_key",
                        "version": 3.3
                    }
                ]
            }
        }
        self.home = JarvisHome(config)

    def test_not_configured_without_tinytuya(self):
        # If tinytuya not installed, should return graceful message
        result = self.home.handle_command("accendi le luci")
        if not self.home.is_configured():
            assert result is None or "non configurata" in (result or "")

    def test_list_devices(self):
        result = self.home.list_devices()
        assert "luce_test" in result or "Nessun" in result

    def test_turn_on_without_tuya(self):
        # tinytuya not installed in test env → expect graceful message
        result = self.home.turn_on("luce_test")
        assert result is not None
        assert isinstance(result, str)


# ------------------------------------------------------------------ #
# Core routing tests (mocked API)                                      #
# ------------------------------------------------------------------ #

class TestJarvisCore:
    def setup_method(self):
        from jarvis_memory import JarvisMemory
        from jarvis_mood import MoodDetector
        from jarvis_core import JarvisCore
        import tempfile, pathlib
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.mem = JarvisMemory(db_path=pathlib.Path(tmp.name))
        self.core = JarvisCore(
            api_key="sk-ant-fake",
            memory=self.mem,
            mood_detector=MoodDetector(),
        )

    @patch("jarvis_core.anthropic.Anthropic")
    def test_haiku_called_for_quick_intent(self, mock_anthropic):
        mock_client = MagicMock()
        mock_client.messages.create.return_value.content = [MagicMock(text="Sono le 10:00, Sir.")]
        mock_anthropic.return_value = mock_client
        self.core.client = mock_client

        result = asyncio.run(self.core.process("che ore sono"))
        assert result["intent"] == "what_time"
        assert result["model"] in ("haiku", "cache")

    @patch("jarvis_core.anthropic.Anthropic")
    def test_sonnet_called_for_mood_check(self, mock_anthropic):
        mock_client = MagicMock()
        mock_client.messages.create.return_value.content = [MagicMock(text="Capisco, Sir. Come posso aiutarla?")]
        mock_anthropic.return_value = mock_client
        self.core.client = mock_client

        result = asyncio.run(self.core.process("mi sento triste"))
        assert result["intent"] == "mood_check"
        assert result["model"] == "sonnet"

    @patch("jarvis_core.anthropic.Anthropic")
    def test_response_saved_to_memory(self, mock_anthropic):
        mock_client = MagicMock()
        mock_client.messages.create.return_value.content = [MagicMock(text="Risposta test.")]
        mock_anthropic.return_value = mock_client
        self.core.client = mock_client

        asyncio.run(self.core.process("ciao JARVIS"))
        convs = self.mem.get_recent_conversations(1)
        assert len(convs) == 1
        assert convs[0]["user_input"] == "ciao JARVIS"
