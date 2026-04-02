"""
jarvis_home.py — JARVIS v4.0 Smart Home (Tuya)

Controls Tuya smart plugs/lights via tinytuya.
Falls back gracefully if tinytuya not installed or devices unconfigured.

Config (config.json):
  smart_home.devices: list of {id, ip, local_key, version, alias}
  smart_home.lights:  list of alias names
  smart_home.plugs:   list of alias names
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.home")

try:
    import tinytuya
    TUYA_AVAILABLE = True
except ImportError:
    TUYA_AVAILABLE = False
    logger.warning("tinytuya not installed — smart home disabled. pip install tinytuya")


class JarvisHome:
    """Tuya smart home bridge with alias resolution and state caching."""

    CACHE_TTL = 30  # seconds

    def __init__(self, config: dict):
        self.config = config.get("smart_home", {})
        self._devices: dict[str, dict] = {}   # alias → device config
        self._state_cache: dict[str, dict] = {}
        self._cache_ts: dict[str, float] = {}
        self._load_devices()

    # ------------------------------------------------------------------ #
    # Setup                                                                #
    # ------------------------------------------------------------------ #

    def _load_devices(self):
        raw = self.config.get("devices", [])
        for dev in raw:
            alias = dev.get("alias", dev.get("id", "unknown")).lower()
            self._devices[alias] = dev

    def is_configured(self) -> bool:
        return TUYA_AVAILABLE and bool(self._devices)

    def _get_device(self, alias: str) -> Optional[object]:
        """Return a connected tinytuya.OutletDevice or BulbDevice."""
        if not TUYA_AVAILABLE:
            return None
        cfg = self._devices.get(alias.lower())
        if not cfg:
            # Try partial match
            for key, val in self._devices.items():
                if alias.lower() in key:
                    cfg = val
                    break
        if not cfg:
            return None
        dev_version = float(cfg.get("version", 3.3))
        device = tinytuya.OutletDevice(
            dev_id=cfg["id"],
            address=cfg.get("ip", "Auto"),
            local_key=cfg.get("local_key", ""),
            version=dev_version,
        )
        device.set_timeout(5)
        return device

    # ------------------------------------------------------------------ #
    # Actions                                                              #
    # ------------------------------------------------------------------ #

    def turn_on(self, alias: str) -> str:
        if not self.is_configured():
            return "Smart home non configurata, Sir. Installa tinytuya e aggiungi i dispositivi."
        dev = self._get_device(alias)
        if not dev:
            return f"Dispositivo '{alias}' non trovato, Sir."
        try:
            dev.turn_on()
            self._update_cache(alias, {"switch_1": True})
            return f"Ho acceso {alias}, Sir."
        except Exception as e:
            logger.error("turn_on %s: %s", alias, e)
            return f"Impossibile accendere {alias}: {e}"

    def turn_off(self, alias: str) -> str:
        if not self.is_configured():
            return "Smart home non configurata, Sir."
        dev = self._get_device(alias)
        if not dev:
            return f"Dispositivo '{alias}' non trovato, Sir."
        try:
            dev.turn_off()
            self._update_cache(alias, {"switch_1": False})
            return f"Ho spento {alias}, Sir."
        except Exception as e:
            logger.error("turn_off %s: %s", alias, e)
            return f"Impossibile spegnere {alias}: {e}"

    def toggle(self, alias: str) -> str:
        state = self.get_state(alias)
        if state and state.get("switch_1"):
            return self.turn_off(alias)
        return self.turn_on(alias)

    def set_brightness(self, alias: str, percent: int) -> str:
        """Set brightness 0-100%. Converts to Tuya 10-1000 range."""
        if not self.is_configured():
            return "Smart home non configurata, Sir."
        dev = self._get_device(alias)
        if not dev:
            return f"Dispositivo '{alias}' non trovato, Sir."
        try:
            brightness = max(10, min(1000, int(percent * 10)))
            dev.set_value(3, brightness)
            self._update_cache(alias, {"brightness": brightness})
            return f"Luminosità di {alias} impostata al {percent}%, Sir."
        except Exception as e:
            return f"Errore luminosità: {e}"

    def get_state(self, alias: str) -> Optional[dict]:
        ts = self._cache_ts.get(alias, 0)
        if time.time() - ts < self.CACHE_TTL and alias in self._state_cache:
            return self._state_cache[alias]
        if not self.is_configured():
            return None
        dev = self._get_device(alias)
        if not dev:
            return None
        try:
            status = dev.status()
            state = status.get("dps", {})
            self._update_cache(alias, state)
            return state
        except Exception as e:
            logger.error("get_state %s: %s", alias, e)
            return None

    def get_all_states(self) -> dict:
        return {alias: self.get_state(alias) for alias in self._devices}

    # ------------------------------------------------------------------ #
    # Natural language dispatch                                            #
    # ------------------------------------------------------------------ #

    def handle_command(self, text: str) -> Optional[str]:
        """
        Parse Italian voice commands and dispatch to device action.
        Returns response string or None if not a home command.
        """
        text_lower = text.lower()

        # Detect action
        if any(w in text_lower for w in ["accendi", "turn on", "accendere"]):
            action = "turn_on"
        elif any(w in text_lower for w in ["spegni", "turn off", "spegnere"]):
            action = "turn_off"
        elif any(w in text_lower for w in ["regola", "imposta", "luminosità", "brightness"]):
            action = "set_brightness"
        elif any(w in text_lower for w in ["toggle", "inverti"]):
            action = "toggle"
        else:
            return None

        # Detect target
        target = self._resolve_target(text_lower)
        if not target:
            return None

        if action == "turn_on":
            return self.turn_on(target)
        elif action == "turn_off":
            return self.turn_off(target)
        elif action == "toggle":
            return self.toggle(target)
        elif action == "set_brightness":
            import re
            m = re.search(r"(\d+)\s*%?", text_lower)
            pct = int(m.group(1)) if m else 50
            return self.set_brightness(target, pct)
        return None

    def _resolve_target(self, text: str) -> Optional[str]:
        # Check known aliases first
        for alias in self._devices:
            if alias in text:
                return alias

        # Generic Italian room/device keywords
        keywords = {
            "luce":         "luce",
            "luci":         "luce",
            "lampada":      "lampada",
            "camera":       "camera",
            "salotto":      "salotto",
            "cucina":       "cucina",
            "bagno":        "bagno",
            "presa":        "presa",
            "caffè":        "coffee_machine",
            "ventilatore":  "desk_fan",
        }
        for kw, alias in keywords.items():
            if kw in text:
                return alias
        return None

    # ------------------------------------------------------------------ #
    # Cache                                                                #
    # ------------------------------------------------------------------ #

    def _update_cache(self, alias: str, state: dict):
        self._state_cache[alias] = state
        self._cache_ts[alias] = time.time()

    # ------------------------------------------------------------------ #
    # List devices                                                         #
    # ------------------------------------------------------------------ #

    def list_devices(self) -> str:
        if not self._devices:
            return "Nessun dispositivo configurato, Sir."
        names = ", ".join(self._devices.keys())
        return f"Dispositivi configurati: {names}."


# ------------------------------------------------------------------ #
# v3 compatibility: HomeAssistantBridge facade                         #
# ------------------------------------------------------------------ #

import os
import requests as _requests

HA_CONFIG_FILE = Path("config") / "home_assistant.json"

DEFAULT_ALIASES = {
    "luce camera": "light.bedroom",
    "luce salotto": "light.living_room",
    "luce cucina": "light.kitchen",
    "luce bagno": "light.bathroom",
    "lampada": "light.lamp",
    "ventilatore": "fan.bedroom",
    "condizionatore": "climate.living_room",
    "termostato": "climate.thermostat",
    "tv": "media_player.tv",
    "televisione": "media_player.tv",
}


def _load_ha_config() -> dict:
    if HA_CONFIG_FILE.exists():
        try:
            with open(HA_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


class HomeAssistantBridge:
    """Home Assistant REST API bridge (v3 compatibility)."""

    def __init__(self):
        cfg = _load_ha_config()
        self._url = cfg.get("url", "").rstrip("/")
        self._token = os.environ.get("HA_TOKEN", cfg.get("token", ""))
        self._aliases = {**DEFAULT_ALIASES, **cfg.get("aliases", {})}
        self._available = bool(self._url and self._token)

    @property
    def available(self) -> bool:
        return self._available

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    def _resolve_entity(self, device_name: str) -> Optional[str]:
        name = device_name.lower().strip()
        if name in self._aliases:
            return self._aliases[name]
        for alias, entity in self._aliases.items():
            if alias in name or name in alias:
                return entity
        if "." in name:
            return name
        return None

    def _call_service(self, domain: str, service: str, entity_id: str, **data) -> bool:
        if not self._available:
            return False
        url = f"{self._url}/api/services/{domain}/{service}"
        payload = {"entity_id": entity_id, **data}
        try:
            resp = _requests.post(url, headers=self._headers(), json=payload, timeout=10)
            return resp.status_code == 200
        except Exception:
            return False

    def turn_on(self, device_name: str) -> str:
        entity = self._resolve_entity(device_name)
        if not entity:
            return f"Dispositivo '{device_name}' non trovato, Sir."
        domain = entity.split(".")[0]
        if self._call_service(domain, "turn_on", entity):
            return f"Ho acceso {device_name}, Sir."
        return f"Errore nell'accensione di {device_name}, Sir."

    def turn_off(self, device_name: str) -> str:
        entity = self._resolve_entity(device_name)
        if not entity:
            return f"Dispositivo '{device_name}' non trovato, Sir."
        domain = entity.split(".")[0]
        if self._call_service(domain, "turn_off", entity):
            return f"Ho spento {device_name}, Sir."
        return f"Errore nello spegnimento di {device_name}, Sir."

    def toggle(self, device_name: str) -> str:
        entity = self._resolve_entity(device_name)
        if not entity:
            return f"Dispositivo '{device_name}' non trovato, Sir."
        domain = entity.split(".")[0]
        if self._call_service(domain, "toggle", entity):
            return f"Ho alternato {device_name}, Sir."
        return f"Errore nel toggle di {device_name}, Sir."

    def set_brightness(self, device_name: str, brightness_pct: int) -> str:
        entity = self._resolve_entity(device_name)
        if not entity:
            return f"Dispositivo '{device_name}' non trovato, Sir."
        brightness = max(0, min(255, int(brightness_pct * 255 / 100)))
        if self._call_service("light", "turn_on", entity, brightness=brightness):
            return f"Luminosità {device_name} al {brightness_pct}%, Sir."
        return f"Errore nell'impostazione luminosità di {device_name}, Sir."

    def set_temperature(self, device_name: str, temperature: float) -> str:
        entity = self._resolve_entity(device_name)
        if not entity:
            return f"Dispositivo '{device_name}' non trovato, Sir."
        if self._call_service("climate", "set_temperature", entity, temperature=temperature):
            return f"Temperatura {device_name} impostata a {temperature}°C, Sir."
        return f"Errore nell'impostazione temperatura di {device_name}, Sir."

    def get_state(self, device_name: str) -> str:
        if not self._available:
            return "Home Assistant non configurato, Sir."
        entity = self._resolve_entity(device_name)
        if not entity:
            return f"Dispositivo '{device_name}' non trovato, Sir."
        try:
            url = f"{self._url}/api/states/{entity}"
            resp = _requests.get(url, headers=self._headers(), timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                state = data.get("state", "sconosciuto")
                friendly = data.get("attributes", {}).get("friendly_name", device_name)
                return f"{friendly}: {state}"
        except Exception:
            pass
        return f"Errore stato {device_name}, Sir."

    def get_all_states(self) -> str:
        if not self._available:
            return "Home Assistant non configurato, Sir."
        try:
            url = f"{self._url}/api/states"
            resp = _requests.get(url, headers=self._headers(), timeout=10)
            if resp.status_code == 200:
                entities = resp.json()
                lines = []
                for e in entities[:20]:
                    name = e.get("attributes", {}).get("friendly_name", e["entity_id"])
                    lines.append(f"  {name}: {e['state']}")
                return "Stato dispositivi:\n" + "\n".join(lines)
        except Exception:
            pass
        return "Errore recupero stati, Sir."


# Singleton for v3 compatibility
_ha_bridge: Optional[HomeAssistantBridge] = None


def get_bridge() -> HomeAssistantBridge:
    """Get or create the HA bridge singleton (v3 API)."""
    global _ha_bridge
    if _ha_bridge is None:
        _ha_bridge = HomeAssistantBridge()
    return _ha_bridge
