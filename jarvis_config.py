import json
from pathlib import Path


class JarvisConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.config = self._load()

    def _load(self) -> dict:
        config_file = self.config_dir / "jarvis_config.json"
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def get(self, key, default=None):
        # Support dotted keys like "ai.local_url"
        keys = key.split(".") if isinstance(key, str) else [key]
        val = self.config
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
            if val is None:
                return default
        return val

    def get_voice(self) -> str:
        return self.get("voice.name", "it-IT-DiegoNeural")

    def get_local_model(self) -> str:
        return self.get("ai.local_model", "llama3.1:8b")

    def get_cloud_model(self) -> str:
        return self.get("ai.cloud_model", "claude-haiku-4-5-20251001")


config = JarvisConfig()
