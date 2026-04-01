"""
Shared fixtures for JARVIS test suite.
All audio I/O is mocked — no real mic, no real speaker, no real pygame playback.
"""
import sys
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    """Run each test in an isolated temp directory to avoid polluting project."""
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def mock_pygame():
    """Mock pygame.mixer so no audio is ever played."""
    mock_mixer = MagicMock()
    mock_channel = MagicMock()
    mock_channel.get_busy.return_value = False
    mock_channel.get_volume.return_value = 0.7
    mock_mixer.Channel.return_value = mock_channel
    mock_mixer.Sound.return_value = MagicMock()
    return mock_mixer


@pytest.fixture
def finance_file(tmp_path):
    """Create a temporary finances.json for isolated tests."""
    import json
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    fpath = config_dir / "finances.json"
    data = {"target_affitto": 110.0, "entrate_attuali": 0.0, "voci_entrata": []}
    fpath.write_text(json.dumps(data), encoding="utf-8")
    return fpath
