"""
Tests for jarvis_stt.py — faster-whisper STT module.
CRITICAL: All model loading is mocked. No real Whisper model is loaded.
"""
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

import jarvis_stt as stt


@pytest.fixture(autouse=True)
def _reset_stt_singleton():
    """Reset STT singleton state before each test."""
    stt._model = None
    stt._model_loaded = False
    yield
    stt._model = None
    stt._model_loaded = False


class TestModelLoading:

    @patch("jarvis_stt.WhisperModel", create=True)
    def test_load_model_once(self, mock_cls):
        """Model should be loaded exactly once via singleton."""
        mock_model = MagicMock()
        mock_cls.return_value = mock_model

        with patch.dict("sys.modules", {"faster_whisper": MagicMock(WhisperModel=mock_cls)}):
            result1 = stt._load_model()
            result2 = stt._load_model()

        # Called only once (singleton)
        assert mock_cls.call_count == 1
        assert result1 is mock_model
        assert result2 is mock_model

    def test_load_model_handles_import_error(self):
        """If faster-whisper not installed, model is None."""
        with patch.dict("sys.modules", {"faster_whisper": None}):
            # Force reimport attempt
            stt._model = None
            stt._model_loaded = False
            result = stt._load_model()

        assert result is None
        assert stt._model_loaded is True  # Don't retry

    def test_is_model_loaded_false_initially(self):
        """Model should not be loaded until preload() or first transcribe."""
        assert stt.is_model_loaded() is False

    def test_preload_calls_load(self):
        """preload() should trigger model loading."""
        with patch.object(stt, "_load_model", return_value=None) as mock_load:
            stt.preload()
            mock_load.assert_called_once()


class TestTranscription:

    def test_transcribe_returns_text(self):
        """transcribe_audio should return lowercased stripped text."""
        mock_model = MagicMock()
        # faster-whisper returns (segments_generator, info)
        mock_seg = MagicMock()
        mock_seg.text = "  Ciao Tony  "
        mock_model.transcribe.return_value = (iter([mock_seg]), MagicMock())

        stt._model = mock_model
        stt._model_loaded = True

        audio = np.zeros(16000, dtype=np.int16)
        result = stt.transcribe_audio(audio)

        assert result == "ciao tony"

    def test_transcribe_joins_multiple_segments(self):
        """Multiple segments should be joined with spaces."""
        mock_model = MagicMock()
        seg1 = MagicMock()
        seg1.text = "Buonasera"
        seg2 = MagicMock()
        seg2.text = "Sir"
        mock_model.transcribe.return_value = (iter([seg1, seg2]), MagicMock())

        stt._model = mock_model
        stt._model_loaded = True

        audio = np.zeros(16000, dtype=np.int16)
        result = stt.transcribe_audio(audio)

        assert result == "buonasera sir"

    def test_transcribe_empty_on_no_model(self):
        """If model failed to load, return empty string."""
        stt._model = None
        stt._model_loaded = True

        audio = np.zeros(16000, dtype=np.int16)
        result = stt.transcribe_audio(audio)

        assert result == ""

    def test_transcribe_uses_italian(self):
        """transcribe should pass language='it' and vad_filter=True."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (iter([]), MagicMock())

        stt._model = mock_model
        stt._model_loaded = True

        audio = np.zeros(16000, dtype=np.int16)
        stt.transcribe_audio(audio)

        call_kwargs = mock_model.transcribe.call_args
        assert call_kwargs[1]["language"] == "it"
        assert call_kwargs[1]["vad_filter"] is True
        assert call_kwargs[1]["vad_parameters"]["min_silence_duration_ms"] == 500

    def test_transcribe_converts_int16_to_float32(self):
        """Audio should be converted from int16 to float32 normalized."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = (iter([]), MagicMock())

        stt._model = mock_model
        stt._model_loaded = True

        audio = np.array([16384, -16384, 0], dtype=np.int16)
        stt.transcribe_audio(audio)

        passed_audio = mock_model.transcribe.call_args[0][0]
        assert passed_audio.dtype == np.float32
        assert abs(passed_audio[0] - 0.5) < 0.01

    def test_transcribe_handles_exception(self):
        """Exception during transcribe should return empty string."""
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = RuntimeError("boom")

        stt._model = mock_model
        stt._model_loaded = True

        audio = np.zeros(16000, dtype=np.int16)
        result = stt.transcribe_audio(audio)

        assert result == ""
