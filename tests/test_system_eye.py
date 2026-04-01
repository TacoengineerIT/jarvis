"""
Tests for jarvis_system_eye.py — System awareness module.
Process listing is mocked to avoid platform-specific flakiness.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

import jarvis_system_eye as eye_mod
from jarvis_system_eye import SystemEye, get_eye


@pytest.fixture(autouse=True)
def _reset_eye_singleton():
    """Reset singleton between tests."""
    eye_mod._eye = None
    yield
    eye_mod._eye = None


class TestGetActiveApps:

    @patch("jarvis_system_eye.psutil")
    def test_returns_sorted_lowercase(self, mock_psutil):
        """Active apps should be sorted and lowercased."""
        mock_psutil.process_iter.return_value = [
            MagicMock(info={"name": "Chrome.exe"}),
            MagicMock(info={"name": "Spotify.exe"}),
            MagicMock(info={"name": "code.exe"}),
        ]
        se = SystemEye()
        apps = se.get_active_apps()
        assert apps == ["chrome", "code", "spotify"]

    @patch("jarvis_system_eye.psutil")
    def test_deduplicates(self, mock_psutil):
        """Duplicate process names should be deduplicated."""
        mock_psutil.process_iter.return_value = [
            MagicMock(info={"name": "chrome.exe"}),
            MagicMock(info={"name": "chrome.exe"}),
        ]
        se = SystemEye()
        apps = se.get_active_apps()
        assert apps == ["chrome"]

    @patch("jarvis_system_eye.psutil")
    def test_handles_empty_name(self, mock_psutil):
        """Processes with empty name should be skipped."""
        mock_psutil.process_iter.return_value = [
            MagicMock(info={"name": ""}),
            MagicMock(info={"name": "python.exe"}),
        ]
        se = SystemEye()
        apps = se.get_active_apps()
        assert apps == ["python"]


class TestGetSystemStats:

    @patch("jarvis_system_eye.psutil")
    def test_returns_cpu_ram_disk(self, mock_psutil):
        """Stats should include CPU, RAM, disk."""
        mock_psutil.cpu_percent.return_value = 45.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=60.0, used=8 * 1024**3, total=16 * 1024**3
        )
        mock_psutil.disk_usage.return_value = MagicMock(percent=55.0)
        mock_psutil.sensors_battery.return_value = MagicMock(
            percent=78, power_plugged=True
        )

        se = SystemEye()
        stats = se.get_system_stats()

        assert stats["cpu_percent"] == 45.0
        assert stats["ram_percent"] == 60.0
        assert stats["ram_used_gb"] == 8.0
        assert stats["disk_percent"] == 55.0
        assert stats["battery_percent"] == 78
        assert stats["battery_plugged"] is True

    @patch("jarvis_system_eye.psutil")
    def test_no_battery(self, mock_psutil):
        """Should handle no battery gracefully."""
        mock_psutil.cpu_percent.return_value = 30.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=50.0, used=8 * 1024**3, total=16 * 1024**3
        )
        mock_psutil.disk_usage.return_value = MagicMock(percent=40.0)
        mock_psutil.sensors_battery.return_value = None

        se = SystemEye()
        stats = se.get_system_stats()

        assert "battery_percent" not in stats
        assert stats["cpu_percent"] == 30.0


class TestTimeContext:

    @patch("jarvis_system_eye.datetime")
    def test_morning(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 31, 9, 0)
        se = SystemEye()
        assert se.get_time_context() == "mattina"

    @patch("jarvis_system_eye.datetime")
    def test_lunch(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 31, 13, 0)
        se = SystemEye()
        assert se.get_time_context() == "ora di pranzo"

    @patch("jarvis_system_eye.datetime")
    def test_afternoon(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 31, 15, 0)
        se = SystemEye()
        assert se.get_time_context() == "pomeriggio"

    @patch("jarvis_system_eye.datetime")
    def test_evening(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 31, 20, 0)
        se = SystemEye()
        assert se.get_time_context() == "sera"

    @patch("jarvis_system_eye.datetime")
    def test_night(self, mock_dt):
        mock_dt.now.return_value = datetime(2026, 3, 31, 2, 0)
        se = SystemEye()
        assert se.get_time_context() == "notte"


class TestContextMode:

    @patch("jarvis_system_eye.psutil")
    def test_developer_mode(self, mock_psutil):
        """Should detect developer mode from dev apps."""
        mock_psutil.process_iter.return_value = [
            MagicMock(info={"name": "code.exe"}),
            MagicMock(info={"name": "git.exe"}),
            MagicMock(info={"name": "python.exe"}),
        ]
        se = SystemEye()
        assert se.get_context_mode() == "developer"

    @patch("jarvis_system_eye.psutil")
    def test_study_mode(self, mock_psutil):
        """Should detect study mode from study apps."""
        mock_psutil.process_iter.return_value = [
            MagicMock(info={"name": "acrobat.exe"}),
            MagicMock(info={"name": "onenote.exe"}),
        ]
        se = SystemEye()
        assert se.get_context_mode() == "study"

    @patch("jarvis_system_eye.psutil")
    def test_relax_mode(self, mock_psutil):
        """Should detect relax mode from entertainment apps."""
        mock_psutil.process_iter.return_value = [
            MagicMock(info={"name": "spotify.exe"}),
            MagicMock(info={"name": "steam.exe"}),
        ]
        se = SystemEye()
        assert se.get_context_mode() == "relax"

    @patch("jarvis_system_eye.psutil")
    def test_general_mode_no_apps(self, mock_psutil):
        """Should return general when no category apps detected."""
        mock_psutil.process_iter.return_value = [
            MagicMock(info={"name": "explorer.exe"}),
            MagicMock(info={"name": "svchost.exe"}),
        ]
        se = SystemEye()
        assert se.get_context_mode() == "general"


class TestGetSummary:

    @patch("jarvis_system_eye.psutil")
    @patch("jarvis_system_eye.datetime")
    def test_summary_contains_all_info(self, mock_dt, mock_psutil):
        """Summary should include time, mode, CPU, RAM."""
        mock_dt.now.return_value = datetime(2026, 3, 31, 15, 0)
        mock_psutil.process_iter.return_value = [
            MagicMock(info={"name": "code.exe"}),
        ]
        mock_psutil.cpu_percent.return_value = 25.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=55.0, used=8 * 1024**3, total=16 * 1024**3
        )
        mock_psutil.disk_usage.return_value = MagicMock(percent=40.0)
        mock_psutil.sensors_battery.return_value = None

        se = SystemEye()
        summary = se.get_summary()

        assert "pomeriggio" in summary
        assert "developer" in summary
        assert "25" in summary
        assert "55" in summary

    @patch("jarvis_system_eye.psutil")
    @patch("jarvis_system_eye.datetime")
    def test_summary_high_cpu_warning(self, mock_dt, mock_psutil):
        """High CPU should trigger warning in summary."""
        mock_dt.now.return_value = datetime(2026, 3, 31, 10, 0)
        mock_psutil.process_iter.return_value = []
        mock_psutil.cpu_percent.return_value = 95.0
        mock_psutil.virtual_memory.return_value = MagicMock(
            percent=50.0, used=8 * 1024**3, total=16 * 1024**3
        )
        mock_psutil.disk_usage.return_value = MagicMock(percent=40.0)
        mock_psutil.sensors_battery.return_value = None

        se = SystemEye()
        summary = se.get_summary()

        assert "ATTENZIONE" in summary
        assert "CPU" in summary


class TestSingleton:

    def test_get_eye_returns_same_instance(self):
        """get_eye() should return the same instance."""
        e1 = get_eye()
        e2 = get_eye()
        assert e1 is e2
