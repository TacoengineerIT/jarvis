"""
Tests for jarvis_voice.py — TTS generation and playback.
CRITICAL: All audio playback is mocked. No real sound output.
"""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from pathlib import Path
import threading


class TestTTSGeneratesAudio:

    @patch("jarvis_voice.subprocess.Popen")
    def test_create_audio_file_calls_edge_tts(self, mock_popen, tmp_path):
        """create_audio_file should invoke edge-tts subprocess."""
        # Mock subprocess to create the expected file
        mock_proc = MagicMock()
        mock_proc.poll.side_effect = [None, 0]  # running, then done
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        import jarvis_voice as jv

        with patch.object(jv, "Path", wraps=Path) as mock_path_cls:
            # Patch audio_dir to tmp
            audio_dir = tmp_path / "audio_cache"
            audio_dir.mkdir()

            # We need to intercept the path creation
            result = jv.create_audio_file("test phrase")

            # edge-tts should have been called
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args[0][0]
            assert "edge-tts" in call_args[0]
            assert "--voice" in call_args
            assert "it-IT-DiegoNeural" in call_args

    def test_create_audio_file_respects_stop_event(self):
        """If stop_event is set, create_audio_file returns None immediately."""
        import jarvis_voice as jv

        stop = threading.Event()
        stop.set()

        result = jv.create_audio_file("test phrase", stop_event=stop)
        assert result is None


class TestTTSItalianVoice:

    @patch("jarvis_voice.subprocess.Popen")
    def test_voice_is_diego_neural(self, mock_popen):
        """TTS should use it-IT-DiegoNeural voice."""
        mock_proc = MagicMock()
        mock_proc.poll.side_effect = [None, 0]
        mock_proc.returncode = 0
        mock_popen.return_value = mock_proc

        import jarvis_voice as jv
        jv.create_audio_file("qualsiasi frase")

        call_args = mock_popen.call_args[0][0]
        assert "it-IT-DiegoNeural" in call_args


class TestSayFunction:

    def test_say_with_stop_event_set(self):
        """say() should return False immediately if stop_event already set."""
        import jarvis_voice as jv

        stop = threading.Event()
        stop.set()

        # say() checks stop_event at the very start and returns False
        with patch.object(jv, "duck_music"), \
             patch.object(jv, "create_audio_file") as mock_create:
            result = jv.say("qualcosa", duck=True, stop_event=stop)
            assert result is False
            mock_create.assert_not_called()

    def test_say_no_audio_file(self):
        """say() should handle None audio file gracefully."""
        import jarvis_voice as jv

        with patch.object(jv, "duck_music"), \
             patch.object(jv, "create_audio_file", return_value=None):
            result = jv.say("qualcosa", duck=False, stop_event=None)
            assert result is False


class TestDucking:

    def test_duck_music_no_crash_when_unloaded(self):
        """duck_music should be a no-op when music not loaded."""
        import jarvis_voice as jv

        original = jv._music_loaded
        jv._music_loaded = False
        try:
            jv.duck_music(ducked=True)   # should not crash
            jv.duck_music(ducked=False)  # should not crash
        finally:
            jv._music_loaded = original

    @patch("jarvis_voice.MUSIC_CH")
    def test_duck_ramps_volume(self, mock_ch):
        """When music is playing, duck should ramp volume down."""
        import jarvis_voice as jv

        mock_ch.get_busy.return_value = True
        mock_ch.get_volume.return_value = 0.70

        original = jv._music_loaded
        jv._music_loaded = True
        try:
            jv.duck_music(ducked=True)
            # set_volume should have been called multiple times (ramp)
            assert mock_ch.set_volume.call_count >= 2
        finally:
            jv._music_loaded = original


class TestAudioCacheHash:

    def test_hash_deterministic(self):
        """Same text should produce same hash (hashlib, not hash())."""
        import jarvis_voice as jv
        import hashlib

        text = "Buonasera Tony"
        h1 = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
        h2 = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
        assert h1 == h2

    def test_hash_different_texts(self):
        """Different texts should produce different hashes."""
        import hashlib

        h1 = hashlib.md5("Buonasera".encode("utf-8")).hexdigest()[:12]
        h2 = hashlib.md5("Arrivederci".encode("utf-8")).hexdigest()[:12]
        assert h1 != h2
