"""
Tests for jarvis_home.py — Home Assistant integration.
CRITICAL: All HTTP requests are mocked. No real HA server is contacted.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import jarvis_home as home


@pytest.fixture(autouse=True)
def _reset_home_singleton():
    """Reset HA singleton between tests."""
    home._bridge = None
    yield
    home._bridge = None


@pytest.fixture
def ha_config(tmp_path):
    """Create a temporary HA config file."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cfg = {
        "url": "http://ha.local:8123",
        "token": "test-token-abc",
        "aliases": {
            "luce studio": "light.study",
        }
    }
    config_file = config_dir / "home_assistant.json"
    config_file.write_text(json.dumps(cfg), encoding="utf-8")
    return config_file


class TestBridgeInit:

    def test_not_available_without_config(self):
        """Bridge should be unavailable when no config exists."""
        with patch.object(home, "HA_CONFIG_FILE", Path("nonexistent/ha.json")):
            bridge = home.HomeAssistantBridge()
        assert bridge.available is False

    def test_available_with_config(self, ha_config):
        """Bridge should be available with valid config."""
        with patch.object(home, "HA_CONFIG_FILE", ha_config):
            bridge = home.HomeAssistantBridge()
        assert bridge.available is True
        assert bridge._url == "http://ha.local:8123"

    def test_token_from_env_var(self, ha_config):
        """HA_TOKEN env var should override config token."""
        with patch.object(home, "HA_CONFIG_FILE", ha_config), \
             patch.dict("os.environ", {"HA_TOKEN": "env-token-xyz"}):
            bridge = home.HomeAssistantBridge()
        assert bridge._token == "env-token-xyz"

    def test_custom_aliases_merged(self, ha_config):
        """Custom aliases should be merged with defaults."""
        with patch.object(home, "HA_CONFIG_FILE", ha_config):
            bridge = home.HomeAssistantBridge()
        assert "luce studio" in bridge._aliases
        assert "luce camera" in bridge._aliases  # Default still present


class TestEntityResolution:

    def test_resolve_direct_alias(self, ha_config):
        """Direct alias match should resolve to entity_id."""
        with patch.object(home, "HA_CONFIG_FILE", ha_config):
            bridge = home.HomeAssistantBridge()
        assert bridge._resolve_entity("luce camera") == "light.bedroom"

    def test_resolve_partial_match(self, ha_config):
        """Partial alias match should work."""
        with patch.object(home, "HA_CONFIG_FILE", ha_config):
            bridge = home.HomeAssistantBridge()
        result = bridge._resolve_entity("la luce camera")
        assert result == "light.bedroom"

    def test_resolve_entity_id_passthrough(self, ha_config):
        """entity_id format should pass through directly."""
        with patch.object(home, "HA_CONFIG_FILE", ha_config):
            bridge = home.HomeAssistantBridge()
        assert bridge._resolve_entity("light.custom") == "light.custom"

    def test_resolve_unknown_returns_none(self, ha_config):
        """Unknown device name should return None."""
        with patch.object(home, "HA_CONFIG_FILE", ha_config):
            bridge = home.HomeAssistantBridge()
        assert bridge._resolve_entity("frullatore magico") is None


class TestDeviceActions:

    @patch("jarvis_home._requests.post")
    def test_turn_on(self, mock_post, ha_config):
        """turn_on should call HA API and return success message."""
        mock_post.return_value = MagicMock(status_code=200)
        with patch.object(home, "HA_CONFIG_FILE", ha_config):
            bridge = home.HomeAssistantBridge()
        result = bridge.turn_on("luce camera")
        assert "acceso" in result.lower()
        mock_post.assert_called_once()
        call_url = mock_post.call_args[0][0]
        assert "/api/services/light/turn_on" in call_url

    @patch("jarvis_home._requests.post")
    def test_turn_off(self, mock_post, ha_config):
        """turn_off should call HA API."""
        mock_post.return_value = MagicMock(status_code=200)
        with patch.object(home, "HA_CONFIG_FILE", ha_config):
            bridge = home.HomeAssistantBridge()
        result = bridge.turn_off("luce camera")
        assert "spento" in result.lower()

    @patch("jarvis_home._requests.post")
    def test_toggle(self, mock_post, ha_config):
        """toggle should call HA API."""
        mock_post.return_value = MagicMock(status_code=200)
        with patch.object(home, "HA_CONFIG_FILE", ha_config):
            bridge = home.HomeAssistantBridge()
        result = bridge.toggle("tv")
        assert "alternato" in result.lower()

    @patch("jarvis_home._requests.post")
    def test_set_brightness(self, mock_post, ha_config):
        """set_brightness should convert percentage to 0-255."""
        mock_post.return_value = MagicMock(status_code=200)
        with patch.object(home, "HA_CONFIG_FILE", ha_config):
            bridge = home.HomeAssistantBridge()
        result = bridge.set_brightness("luce camera", 50)
        assert "50%" in result
        payload = mock_post.call_args[1]["json"]
        assert payload["brightness"] == 127  # 50% of 255

    @patch("jarvis_home._requests.post")
    def test_set_temperature(self, mock_post, ha_config):
        """set_temperature should pass temperature to HA."""
        mock_post.return_value = MagicMock(status_code=200)
        with patch.object(home, "HA_CONFIG_FILE", ha_config):
            bridge = home.HomeAssistantBridge()
        result = bridge.set_temperature("termostato", 22.5)
        assert "22.5" in result

    def test_turn_on_unknown_device(self, ha_config):
        """Unknown device should return error message."""
        with patch.object(home, "HA_CONFIG_FILE", ha_config):
            bridge = home.HomeAssistantBridge()
        result = bridge.turn_on("frullatore magico")
        assert "non trovato" in result.lower()

    def test_actions_when_unavailable(self):
        """Actions should return error when HA not configured."""
        with patch.object(home, "HA_CONFIG_FILE", Path("nonexistent/ha.json")):
            bridge = home.HomeAssistantBridge()
        # turn_on of known alias still fails because bridge is unavailable
        result = bridge.turn_on("luce camera")
        assert "errore" in result.lower()


class TestGetState:

    @patch("jarvis_home._requests.get")
    def test_get_state_success(self, mock_get, ha_config):
        """get_state should return friendly name and state."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "state": "on",
                "attributes": {"friendly_name": "Luce Camera"}
            }
        )
        with patch.object(home, "HA_CONFIG_FILE", ha_config):
            bridge = home.HomeAssistantBridge()
        result = bridge.get_state("luce camera")
        assert "Luce Camera" in result
        assert "on" in result

    @patch("jarvis_home._requests.get")
    def test_get_all_states(self, mock_get, ha_config):
        """get_all_states should list devices."""
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: [
                {"entity_id": "light.bedroom", "state": "on", "attributes": {"friendly_name": "Luce Camera"}},
                {"entity_id": "light.kitchen", "state": "off", "attributes": {"friendly_name": "Luce Cucina"}},
            ]
        )
        with patch.object(home, "HA_CONFIG_FILE", ha_config):
            bridge = home.HomeAssistantBridge()
        result = bridge.get_all_states()
        assert "Luce Camera" in result
        assert "Luce Cucina" in result

    def test_get_state_when_unavailable(self):
        """get_state should return message when HA not configured."""
        with patch.object(home, "HA_CONFIG_FILE", Path("nonexistent/ha.json")):
            bridge = home.HomeAssistantBridge()
        result = bridge.get_state("luce camera")
        assert "non configurato" in result.lower()


class TestSingleton:

    def test_get_bridge_returns_same_instance(self):
        """get_bridge() should return the same instance."""
        with patch.object(home, "HA_CONFIG_FILE", Path("nonexistent/ha.json")):
            b1 = home.get_bridge()
            b2 = home.get_bridge()
        assert b1 is b2
