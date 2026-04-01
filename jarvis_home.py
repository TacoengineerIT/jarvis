"""
JARVIS Home — Home Assistant REST API integration.
Optional module: works without HA configured. Token from env var HA_TOKEN or config.
"""
import json
import os
import logging
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger("jarvis.home")

CONFIG_FILE = Path("config") / "home_assistant.json"

# Default Italian aliases → entity_id mapping
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


def _load_config() -> dict:
    """Load HA config from file. Returns empty dict if not found."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"[HOME] Errore lettura config: {e}")
    return {}


class HomeAssistantBridge:
    """
    Bridge to Home Assistant REST API.

    Config loaded from config/home_assistant.json:
    {
        "url": "http://homeassistant.local:8123",
        "token": "...",           // optional, prefer HA_TOKEN env var
        "aliases": { ... }        // Italian name → entity_id
    }
    """

    def __init__(self):
        cfg = _load_config()
        self._url = cfg.get("url", "").rstrip("/")
        self._token = os.environ.get("HA_TOKEN", cfg.get("token", ""))
        self._aliases = {**DEFAULT_ALIASES, **cfg.get("aliases", {})}
        self._available = bool(self._url and self._token)

        if self._available:
            logger.info(f"[HOME] Configurato: {self._url}")
            print(f"[HOME] Home Assistant configurato: {self._url}")
        else:
            logger.info("[HOME] Non configurato (nessun URL/token). Modulo disabilitato.")

    @property
    def available(self) -> bool:
        return self._available

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _resolve_entity(self, device_name: str) -> Optional[str]:
        """Resolve Italian alias to entity_id."""
        name = device_name.lower().strip()
        # Direct alias match
        if name in self._aliases:
            return self._aliases[name]
        # Fuzzy search in aliases
        for alias, entity in self._aliases.items():
            if alias in name or name in alias:
                return entity
        # Assume it's already an entity_id
        if "." in name:
            return name
        return None

    def _call_service(self, domain: str, service: str, entity_id: str, **data) -> bool:
        """Call a Home Assistant service."""
        if not self._available:
            return False
        url = f"{self._url}/api/services/{domain}/{service}"
        payload = {"entity_id": entity_id, **data}
        try:
            resp = requests.post(url, headers=self._headers(), json=payload, timeout=10)
            ok = resp.status_code == 200
            if not ok:
                logger.warning(f"[HOME] Errore servizio {domain}.{service}: {resp.status_code}")
            return ok
        except Exception as e:
            logger.error(f"[HOME] Errore connessione: {e}")
            return False

    # ── Public API ────────────────────────────────────────

    def turn_on(self, device_name: str) -> str:
        """Turn on a device by Italian name or entity_id."""
        entity = self._resolve_entity(device_name)
        if not entity:
            return f"Dispositivo '{device_name}' non trovato, Sir."
        domain = entity.split(".")[0]
        if self._call_service(domain, "turn_on", entity):
            return f"Ho acceso {device_name}, Sir."
        return f"Errore nell'accensione di {device_name}, Sir."

    def turn_off(self, device_name: str) -> str:
        """Turn off a device by Italian name or entity_id."""
        entity = self._resolve_entity(device_name)
        if not entity:
            return f"Dispositivo '{device_name}' non trovato, Sir."
        domain = entity.split(".")[0]
        if self._call_service(domain, "turn_off", entity):
            return f"Ho spento {device_name}, Sir."
        return f"Errore nello spegnimento di {device_name}, Sir."

    def toggle(self, device_name: str) -> str:
        """Toggle a device."""
        entity = self._resolve_entity(device_name)
        if not entity:
            return f"Dispositivo '{device_name}' non trovato, Sir."
        domain = entity.split(".")[0]
        if self._call_service(domain, "toggle", entity):
            return f"Ho alternato {device_name}, Sir."
        return f"Errore nel toggle di {device_name}, Sir."

    def set_brightness(self, device_name: str, brightness_pct: int) -> str:
        """Set light brightness (0-100%)."""
        entity = self._resolve_entity(device_name)
        if not entity:
            return f"Dispositivo '{device_name}' non trovato, Sir."
        brightness = max(0, min(255, int(brightness_pct * 255 / 100)))
        if self._call_service("light", "turn_on", entity, brightness=brightness):
            return f"Luminosità {device_name} al {brightness_pct}%, Sir."
        return f"Errore nell'impostazione luminosità di {device_name}, Sir."

    def set_temperature(self, device_name: str, temperature: float) -> str:
        """Set thermostat/climate temperature."""
        entity = self._resolve_entity(device_name)
        if not entity:
            return f"Dispositivo '{device_name}' non trovato, Sir."
        if self._call_service("climate", "set_temperature", entity, temperature=temperature):
            return f"Temperatura {device_name} impostata a {temperature}°C, Sir."
        return f"Errore nell'impostazione temperatura di {device_name}, Sir."

    def get_state(self, device_name: str) -> str:
        """Get state of a single device."""
        if not self._available:
            return "Home Assistant non configurato, Sir."
        entity = self._resolve_entity(device_name)
        if not entity:
            return f"Dispositivo '{device_name}' non trovato, Sir."
        try:
            url = f"{self._url}/api/states/{entity}"
            resp = requests.get(url, headers=self._headers(), timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                state = data.get("state", "sconosciuto")
                friendly = data.get("attributes", {}).get("friendly_name", device_name)
                return f"{friendly}: {state}"
            return f"Errore stato {device_name}, Sir."
        except Exception as e:
            return f"Errore connessione Home Assistant: {e}"

    def get_all_states(self) -> str:
        """Get summary of all devices."""
        if not self._available:
            return "Home Assistant non configurato, Sir."
        try:
            url = f"{self._url}/api/states"
            resp = requests.get(url, headers=self._headers(), timeout=10)
            if resp.status_code == 200:
                entities = resp.json()
                lines = []
                for e in entities[:20]:  # Limit output
                    name = e.get("attributes", {}).get("friendly_name", e["entity_id"])
                    lines.append(f"  {name}: {e['state']}")
                return "Stato dispositivi:\n" + "\n".join(lines)
            return "Errore recupero stati, Sir."
        except Exception as e:
            return f"Errore connessione Home Assistant: {e}"


# Singleton instance
_bridge: Optional[HomeAssistantBridge] = None


def get_bridge() -> HomeAssistantBridge:
    """Get or create the HA bridge singleton."""
    global _bridge
    if _bridge is None:
        _bridge = HomeAssistantBridge()
    return _bridge
