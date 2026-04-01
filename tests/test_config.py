"""
Tests for configuration, security, and code quality.
"""
import re
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class TestNoHardcodedKeys:

    # Patterns that suggest hardcoded secrets
    SECRET_PATTERNS = [
        r'sk-[a-zA-Z0-9]{20,}',           # OpenAI/Anthropic API key format
        r'key-[a-zA-Z0-9]{20,}',           # Generic API key
        r'Bearer\s+[a-zA-Z0-9._-]{20,}',   # Bearer token
        r'password\s*=\s*["\'][^"\']+["\']', # password = "..."
        r'api_key\s*=\s*["\'][^"\']+["\']',  # api_key = "..."
        r'secret\s*=\s*["\'][^"\']+["\']',   # secret = "..."
    ]

    def test_no_secrets_in_source(self):
        """Scan all .py files for patterns that look like hardcoded secrets."""
        violations = []

        for py_file in PROJECT_ROOT.glob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            for pattern in self.SECRET_PATTERNS:
                matches = re.findall(pattern, content)
                for match in matches:
                    violations.append(f"{py_file.name}: {match[:40]}...")

        assert violations == [], f"Possible hardcoded secrets found:\n" + "\n".join(violations)


class TestUTF8Encoding:

    def test_all_py_files_valid_utf8(self):
        """Every .py file in project root should be valid UTF-8."""
        errors = []
        for py_file in PROJECT_ROOT.glob("*.py"):
            try:
                py_file.read_text(encoding="utf-8")
            except UnicodeDecodeError as e:
                errors.append(f"{py_file.name}: {e}")

        assert errors == [], f"UTF-8 encoding errors:\n" + "\n".join(errors)


class TestRequirementsComplete:

    # Map of import names to pip package names
    IMPORT_TO_PACKAGE = {
        "pygame": "pygame",
        "requests": "requests",
        "flask": "flask",
        "numpy": "numpy",
        "psutil": "psutil",
        "pyautogui": "pyautogui",
        "thefuzz": "thefuzz",
        "streamlit": "streamlit",
        "chromadb": "chromadb",
        "edge_tts": "edge-tts",
        "sounddevice": "sounddevice",
        "faster_whisper": "faster-whisper",
        "anthropic": "anthropic",
        "scipy": "scipy",
    }

    def test_imports_have_requirements(self):
        """Every third-party import in .py files should have a requirements.txt entry."""
        req_file = PROJECT_ROOT / "requirements.txt"
        assert req_file.exists(), "requirements.txt not found"
        req_content = req_file.read_text(encoding="utf-8").lower()

        missing = []
        for py_file in PROJECT_ROOT.glob("*.py"):
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            for import_name, package_name in self.IMPORT_TO_PACKAGE.items():
                # Check if this import is used
                if f"import {import_name}" in content or f"from {import_name}" in content:
                    if package_name.lower() not in req_content:
                        missing.append(f"{py_file.name} imports '{import_name}' but '{package_name}' not in requirements.txt")

        assert missing == [], "Missing requirements:\n" + "\n".join(missing)


class TestJarvisConfig:

    def test_config_singleton(self):
        from jarvis_config import JarvisConfig
        c1 = JarvisConfig()
        c2 = JarvisConfig()
        assert c1 is c2

    def test_get_with_default(self):
        from jarvis_config import config
        result = config.get("nonexistent.key", "fallback")
        assert result == "fallback"

    def test_get_voice(self):
        from jarvis_config import config
        voice = config.get_voice()
        assert "it-IT" in voice
        assert "Diego" in voice

    def test_get_local_model(self):
        from jarvis_config import config
        model = config.get_local_model()
        assert isinstance(model, str)
        assert len(model) > 0
