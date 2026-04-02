"""
Tests for jarvis_wakeword.py — Wake word detection.
CRITICAL: openwakeword is fully mocked. No real model is loaded.
"""
import time
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

import jarvis_wakeword as ww


@pytest.fixture(autouse=True)
def _reset_wakeword_singleton():
    """Reset module-level singleton state."""
    ww._oww_model = None
    ww._oww_available = False
    ww._oww_checked = False
    yield
    ww._oww_model = None
    ww._oww_available = False
    ww._oww_checked = False


class TestWakeWordDetectorUnavailable:

    def test_not_available_without_openwakeword(self):
        """Detector should report unavailable when openwakeword is missing."""
        with patch.dict("sys.modules", {"openwakeword": None}):
            ww._oww_checked = False
            detector = ww.WakeWordDetector()
        assert detector.available is False

    def test_process_chunk_returns_false_when_unavailable(self):
        """process_chunk should return False when model not loaded."""
        ww._oww_checked = True
        ww._oww_available = False
        detector = ww.WakeWordDetector()

        chunk = np.zeros(512, dtype=np.int16)
        assert detector.process_chunk(chunk) is False


class TestWakeWordDetectorAvailable:

    def _make_detector_with_mock_model(self):
        """Create detector with a mocked openwakeword model."""
        mock_model = MagicMock()
        mock_model.predict.return_value = {"hey_jarvis": 0.1}
        ww._oww_model = mock_model
        ww._oww_available = True
        ww._oww_checked = True
        detector = ww.WakeWordDetector(threshold=0.5)
        return detector, mock_model

    def test_available_with_model(self):
        """Detector should report available when model is loaded."""
        detector, _ = self._make_detector_with_mock_model()
        assert detector.available is True

    def test_no_detection_below_threshold(self):
        """Low score should not trigger detection."""
        detector, mock_model = self._make_detector_with_mock_model()
        mock_model.predict.return_value = {"hey_jarvis": 0.2}

        # Feed enough samples for one oww frame (1280 samples)
        chunk = np.zeros(1280, dtype=np.int16)
        result = detector.process_chunk(chunk)

        assert result is False

    def test_detection_above_threshold(self):
        """High score should trigger detection."""
        detector, mock_model = self._make_detector_with_mock_model()
        mock_model.predict.return_value = {"hey_jarvis": 0.85}

        chunk = np.zeros(1280, dtype=np.int16)
        result = detector.process_chunk(chunk)

        assert result is True

    def test_buffering_small_chunks(self):
        """Small chunks should be buffered until 1280 samples."""
        detector, mock_model = self._make_detector_with_mock_model()
        mock_model.predict.return_value = {"hey_jarvis": 0.9}

        # Feed 512-sample chunks — need 3 to reach 1280 (1536 > 1280)
        chunk = np.zeros(512, dtype=np.int16)
        r1 = detector.process_chunk(chunk)  # 512 total
        r2 = detector.process_chunk(chunk)  # 1024 total
        r3 = detector.process_chunk(chunk)  # 1536 → process 1280, buffer 256

        assert r1 is False  # Not enough samples
        assert r2 is False  # Still not enough
        assert r3 is True   # Processed one frame

    def test_reset_clears_buffer(self):
        """reset() should clear the internal buffer."""
        detector, mock_model = self._make_detector_with_mock_model()

        # Partially fill buffer
        chunk = np.zeros(500, dtype=np.int16)
        detector.process_chunk(chunk)
        assert len(detector._buffer) > 0

        detector.reset()
        assert len(detector._buffer) == 0

    def test_cooldown_prevents_duplicate_detection(self):
        """After detection, cooldown should block immediate re-detection."""
        detector, mock_model = self._make_detector_with_mock_model()
        mock_model.predict.return_value = {"hey_jarvis": 0.85}
        detector.cooldown_seconds = 2.0

        chunk = np.zeros(1280, dtype=np.int16)

        # First detection should succeed
        result1 = detector.process_chunk(chunk)
        assert result1 is True

        # Immediate second detection should be blocked by cooldown
        result2 = detector.process_chunk(chunk)
        assert result2 is False

    def test_cooldown_expires_after_time(self):
        """After cooldown expires, detection should succeed again."""
        detector, mock_model = self._make_detector_with_mock_model()
        mock_model.predict.return_value = {"hey_jarvis": 0.85}
        # Use a very short cooldown so test is fast
        detector.cooldown_seconds = 0.05

        chunk = np.zeros(1280, dtype=np.int16)

        result1 = detector.process_chunk(chunk)
        assert result1 is True

        # Wait for cooldown to expire
        time.sleep(0.1)

        result2 = detector.process_chunk(chunk)
        assert result2 is True

    def test_only_one_detection_per_chunk_even_with_multiple_frames(self):
        """A single process_chunk call should trigger at most one detection."""
        detector, mock_model = self._make_detector_with_mock_model()
        mock_model.predict.return_value = {"hey_jarvis": 0.85}

        # Feed 3 full oww frames in one call — should only detect once
        chunk = np.zeros(1280 * 3, dtype=np.int16)
        result = detector.process_chunk(chunk)
        assert result is True
        assert mock_model.predict.call_count == 1  # Stopped after first detection


class TestIsAvailable:

    def test_is_available_false_without_module(self):
        """is_available() should return False when openwakeword missing."""
        ww._oww_checked = False
        with patch.dict("sys.modules", {"openwakeword": None}):
            result = ww.is_available()
        assert result is False

    def test_is_available_cached(self):
        """Second call should use cached result."""
        ww._oww_checked = True
        ww._oww_available = True
        assert ww.is_available() is True
