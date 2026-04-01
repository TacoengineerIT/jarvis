"""
Tests for VAD barge-in suppression.
All tests use numerical simulation — NO real microphone is ever opened.
"""
import numpy as np
import pytest

from jarvis_vad_smart import SmartVAD, SAMPLE_RATE, CHUNK_SAMPLES, _EnergyBackend


def _make_silence(n_chunks: int = 1) -> list[np.ndarray]:
    """Generate n chunks of silence (zeros)."""
    return [np.zeros(CHUNK_SAMPLES, dtype=np.int16) for _ in range(n_chunks)]


def _make_voice(amplitude: float = 0.4, n_chunks: int = 1) -> list[np.ndarray]:
    """Generate n chunks of voice-like noise at given amplitude (0-1 scale)."""
    amp = int(32767 * amplitude)
    return [np.random.randint(-amp, amp, CHUNK_SAMPLES, dtype=np.int16)
            for _ in range(n_chunks)]


def _make_loud_voice(n_chunks: int = 1) -> list[np.ndarray]:
    """Very loud voice — should pass even through suppression."""
    return _make_voice(amplitude=0.95, n_chunks=n_chunks)


class TestSpeakingFlagSuppressesVAD:

    def test_suppressed_ignores_normal_audio(self):
        """When suppressed, moderate-volume audio should NOT trigger voice_start.

        With zero-calibrated noise floor the energy threshold is at minimum 0.010.
        Amplitude 0.08 → RMS ~0.046 → ratio ~4.6 — below 3.5x suppressed threshold
        only if we calibrate with a realistic noise floor.
        """
        events = []
        vad = SmartVAD(
            on_speech_start=lambda: events.append("start"),
            on_speech_end=lambda a: events.append("end"),
        )
        # Calibrate with low-level noise (realistic ambient)
        ambient = np.random.randint(-200, 200, CHUNK_SAMPLES * 32, dtype=np.int16)
        vad.calibrate_noise(ambient)

        # Enable suppression (JARVIS is speaking)
        vad.set_suppressed(True)

        # Feed moderate voice — typical speaker bleed level (low amplitude)
        for chunk in _make_voice(amplitude=0.02, n_chunks=20):
            vad.process_chunk(chunk)

        # No voice_start should have fired
        assert "start" not in events, "VAD triggered during suppression — should be silent"

    def test_suppressed_flag_toggles(self):
        """set_suppressed(True) then set_suppressed(False) works correctly."""
        vad = SmartVAD()
        vad.set_suppressed(True)
        assert vad._suppressed is True
        vad.set_suppressed(False)
        assert vad._suppressed is False


class TestNormalVADDetectsSpeech:

    def test_voice_detected_when_not_suppressed(self):
        """Normal operation: voice audio triggers voice_start."""
        events = []
        vad = SmartVAD(
            on_speech_start=lambda: events.append("start"),
            on_speech_end=lambda a: events.append("end"),
            silence_duration=0.3,
        )
        vad.calibrate_noise(np.zeros(CHUNK_SAMPLES * 32, dtype=np.int16))

        # Not suppressed (normal)
        vad.set_suppressed(False)

        # Feed voice
        for chunk in _make_voice(amplitude=0.4, n_chunks=15):
            vad.process_chunk(chunk)

        assert "start" in events, "VAD should detect voice when not suppressed"


class TestCooldownAfterSpeech:

    def test_cooldown_keeps_suppression(self):
        """After JARVIS stops speaking, VAD stays suppressed during cooldown."""
        events = []
        vad = SmartVAD(
            on_speech_start=lambda: events.append("start"),
            on_speech_end=lambda a: events.append("end"),
        )
        # Calibrate with realistic ambient noise
        ambient = np.random.randint(-200, 200, CHUNK_SAMPLES * 32, dtype=np.int16)
        vad.calibrate_noise(ambient)

        # Simulate: JARVIS was speaking, now stopped but suppression still on (cooldown)
        vad.set_suppressed(True)
        vad.reset()  # Discard any buffered speech from speaker bleed

        # Feed moderate voice during cooldown (speaker bleed level)
        for chunk in _make_voice(amplitude=0.02, n_chunks=10):
            vad.process_chunk(chunk)

        assert "start" not in events, "Should stay suppressed during cooldown"


class TestLoudBargeInDuringSpeech:

    def test_very_loud_passes_suppression(self):
        """Very loud human voice (close to mic) should still trigger during suppression."""
        events = []
        vad = SmartVAD(
            on_speech_start=lambda: events.append("start"),
            on_speech_end=lambda a: events.append("end"),
        )
        vad.calibrate_noise(np.zeros(CHUNK_SAMPLES * 32, dtype=np.int16))

        # Suppressed but very loud voice
        vad.set_suppressed(True)

        for chunk in _make_loud_voice(n_chunks=15):
            vad.process_chunk(chunk)

        # With amplitude=0.95 and calibrated noise floor near 0,
        # the energy ratio should exceed 3.5x threshold
        assert "start" in events, "Very loud barge-in should pass even during suppression"


class TestEnergyBackend:

    def test_is_speech_no_cap(self):
        """Energy backend returns raw ratio > 1.0 (no cap)."""
        backend = _EnergyBackend(threshold=0.020)
        # Create chunk with high energy (amplitude=0.5 → RMS ~0.29)
        chunk = np.random.randint(-16000, 16000, CHUNK_SAMPLES, dtype=np.int16)
        prob = backend.is_speech(chunk)
        # RMS of uniform[-16000,16000] ≈ 9237/32768 ≈ 0.28, ratio = 0.28/0.02 = 14
        assert prob > 1.0, f"Energy backend should return raw ratio > 1.0, got {prob}"

    def test_silence_below_threshold(self):
        """Silence chunk returns low energy ratio."""
        backend = _EnergyBackend(threshold=0.020)
        chunk = np.zeros(CHUNK_SAMPLES, dtype=np.int16)
        prob = backend.is_speech(chunk)
        assert prob < 0.01, f"Silence should be near 0, got {prob}"

    def test_calibration(self):
        """Calibration adjusts threshold based on noise floor."""
        backend = _EnergyBackend()
        noise = np.random.randint(-100, 100, CHUNK_SAMPLES * 32, dtype=np.int16)
        backend.calibrate(noise)
        assert backend.threshold > 0
        assert backend._noise_floor > 0


class TestVADReset:

    def test_reset_clears_state(self):
        """Reset brings VAD back to silence state."""
        vad = SmartVAD()
        vad.calibrate_noise(np.zeros(CHUNK_SAMPLES * 32, dtype=np.int16))

        # Start voice detection
        for chunk in _make_voice(amplitude=0.4, n_chunks=5):
            vad.process_chunk(chunk)

        vad.reset()
        assert vad._state == "silence"
        assert vad._speech_buf == []
        assert vad._speech_frames == 0
