"""
JARVIS System Eye — Context-aware system monitoring.
Detects active apps, resource usage, and infers user context mode.
"""
import logging
from datetime import datetime
from typing import Optional

import psutil

logger = logging.getLogger("jarvis.system_eye")

# App categories for context detection
DEV_APPS = {"code", "pycharm", "intellij", "visual studio", "vscode", "git", "cmd", "powershell", "terminal", "bash", "python", "node"}
STUDY_APPS = {"acrobat", "pdf", "word", "excel", "powerpoint", "onenote", "notion", "obsidian", "anki", "teams", "zoom"}
RELAX_APPS = {"spotify", "netflix", "vlc", "youtube", "steam", "epic", "discord", "twitch"}
BUSY_APPS = {"outlook", "thunderbird", "slack", "teams", "zoom", "meet"}


class SystemEye:
    """Monitors system state and infers user context."""

    def get_active_apps(self) -> list[str]:
        """Get list of currently running app names (unique, lowercase)."""
        apps = set()
        try:
            for proc in psutil.process_iter(["name"]):
                name = proc.info.get("name", "")
                if name:
                    apps.add(name.lower().replace(".exe", ""))
        except Exception as e:
            logger.warning(f"[EYE] Errore lista processi: {e}")
        return sorted(apps)

    def get_system_stats(self) -> dict:
        """Get current CPU, RAM, disk, battery stats."""
        stats = {}
        try:
            stats["cpu_percent"] = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            stats["ram_percent"] = mem.percent
            stats["ram_used_gb"] = round(mem.used / (1024**3), 1)
            stats["ram_total_gb"] = round(mem.total / (1024**3), 1)
            disk = psutil.disk_usage("/")
            stats["disk_percent"] = disk.percent
            battery = psutil.sensors_battery()
            if battery:
                stats["battery_percent"] = battery.percent
                stats["battery_plugged"] = battery.power_plugged
        except Exception as e:
            logger.warning(f"[EYE] Errore stats: {e}")
        return stats

    def get_time_context(self) -> str:
        """Get time-of-day context string."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "mattina"
        elif 12 <= hour < 14:
            return "ora di pranzo"
        elif 14 <= hour < 18:
            return "pomeriggio"
        elif 18 <= hour < 22:
            return "sera"
        else:
            return "notte"

    def get_context_mode(self) -> str:
        """
        Infer user context mode from running apps.

        Returns one of: developer, study, relax, busy, general
        """
        apps = set(self.get_active_apps())

        dev_count = len(apps & DEV_APPS)
        study_count = len(apps & STUDY_APPS)
        relax_count = len(apps & RELAX_APPS)
        busy_count = len(apps & BUSY_APPS)

        scores = {
            "developer": dev_count,
            "study": study_count,
            "relax": relax_count,
            "busy": busy_count,
        }

        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return "general"
        return best

    def get_summary(self) -> str:
        """
        Get a full context summary for injection into LLM system prompt.
        """
        stats = self.get_system_stats()
        mode = self.get_context_mode()
        time_ctx = self.get_time_context()

        parts = [f"Orario: {time_ctx}. Modalità utente: {mode}."]

        cpu = stats.get("cpu_percent", 0)
        ram = stats.get("ram_percent", 0)
        parts.append(f"CPU: {cpu}%, RAM: {ram}%.")

        battery = stats.get("battery_percent")
        if battery is not None:
            plugged = "in carica" if stats.get("battery_plugged") else "a batteria"
            parts.append(f"Batteria: {battery}% ({plugged}).")

        if cpu > 80:
            parts.append("ATTENZIONE: CPU sotto carico elevato.")
        if ram > 85:
            parts.append("ATTENZIONE: RAM quasi piena.")

        return " ".join(parts)


# Singleton
_eye: Optional[SystemEye] = None


def get_eye() -> SystemEye:
    """Get or create the SystemEye singleton."""
    global _eye
    if _eye is None:
        _eye = SystemEye()
    return _eye
