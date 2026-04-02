"""
jarvis_actions.py — JARVIS v4.0 Action Executor (Haiku-powered quick tasks)

Handles:
  - Git operations (commit, push, status)
  - App launch / URL open
  - System info (time, date, battery)
  - Quick commands from config
  - Reminder / timer (in-memory, no external service)
"""

import asyncio
import datetime
import json
import logging
import os
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.actions")


class JarvisActions:
    """Executes deterministic actions without calling LLM when possible."""

    def __init__(self, config: dict):
        self.config = config
        self.quick_commands: dict = config.get("quick_commands", {})
        self._reminders: list[dict] = []
        self._timers: list[asyncio.Task] = []

    # ------------------------------------------------------------------ #
    # Dispatch                                                             #
    # ------------------------------------------------------------------ #

    async def execute(self, intent: str, user_input: str) -> Optional[str]:
        """
        Returns a string result if this action was handled, else None
        (so jarvis_core can fall through to LLM).
        """
        text = user_input.lower()

        if intent == "git_push":
            return await self._git_push(text)
        elif intent == "git_commit":
            return await self._git_commit(text)
        elif intent == "git_status":
            return await self._git_status()
        elif intent == "what_time":
            return self._what_time()
        elif intent == "what_date":
            return self._what_date()
        elif intent == "open_app":
            return await self._open_app(text)
        elif intent == "add_reminder":
            return self._add_reminder(text)
        elif intent == "set_timer":
            return await self._set_timer(text)

        # Check quick commands
        for keyword, cmd in self.quick_commands.items():
            if keyword in text:
                return await self._run_quick_command(keyword, cmd)

        return None  # Not handled — let LLM take it

    # ------------------------------------------------------------------ #
    # Git                                                                  #
    # ------------------------------------------------------------------ #

    async def _git_push(self, text: str) -> str:
        msg = self._extract_commit_message(text) or "JARVIS auto-commit"
        try:
            result = await self._run_shell(
                f'git add . && git commit -m "{msg}" && git push'
            )
            if "nothing to commit" in result:
                return "Nessun cambiamento da pushare, Sir."
            return f"Push completato, Sir. Messaggio: '{msg}'"
        except Exception as e:
            return f"Errore git push, Sir: {e}"

    async def _git_commit(self, text: str) -> str:
        msg = self._extract_commit_message(text) or "JARVIS auto-commit"
        try:
            result = await self._run_shell(f'git add . && git commit -m "{msg}"')
            if "nothing to commit" in result:
                return "Nulla da committare, Sir."
            return f"Commit eseguito: '{msg}'"
        except Exception as e:
            return f"Errore commit: {e}"

    async def _git_status(self) -> str:
        try:
            result = await self._run_shell("git status --short")
            if not result.strip():
                return "Repository pulita, Sir. Nessuna modifica in sospeso."
            lines = result.strip().split("\n")
            return f"Ci sono {len(lines)} file modificati, Sir."
        except Exception as e:
            return f"Errore git status: {e}"

    @staticmethod
    def _extract_commit_message(text: str) -> Optional[str]:
        for marker in ['"', "'", "messaggio:", "message:"]:
            if marker in text:
                parts = text.split(marker)
                if len(parts) >= 3:
                    return parts[1].strip()
        return None

    # ------------------------------------------------------------------ #
    # System info                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _what_time() -> str:
        now = datetime.datetime.now()
        return f"Sono le {now.strftime('%H:%M')}, Sir."

    @staticmethod
    def _what_date() -> str:
        today = datetime.date.today()
        days_it = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
        months_it = ["", "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                     "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
        wd = days_it[today.weekday()]
        mn = months_it[today.month]
        return f"Oggi è {wd} {today.day} {mn} {today.year}, Sir."

    # ------------------------------------------------------------------ #
    # App control                                                          #
    # ------------------------------------------------------------------ #

    APP_MAP = {
        "chrome":    "chrome",
        "firefox":   "firefox",
        "code":      "code",
        "vscode":    "code",
        "notepad":   "notepad",
        "spotify":   "spotify",
        "discord":   "discord",
        "telegram":  "telegram",
        "explorer":  "explorer",
        "task manager": "taskmgr",
    }

    URL_MAP = {
        "youtube":   "https://youtube.com",
        "github":    "https://github.com",
        "google":    "https://google.com",
        "gmail":     "https://mail.google.com",
        "chatgpt":   "https://chat.openai.com",
        "spotify":   "https://open.spotify.com",
    }

    async def _open_app(self, text: str) -> str:
        for name, url in self.URL_MAP.items():
            if name in text:
                webbrowser.open(url)
                return f"Ho aperto {name} nel browser, Sir."

        for name, cmd in self.APP_MAP.items():
            if name in text:
                try:
                    subprocess.Popen(cmd, shell=True)
                    return f"Ho avviato {name}, Sir."
                except Exception as e:
                    return f"Impossibile avviare {name}: {e}"

        return None  # Unknown app — let LLM handle

    # ------------------------------------------------------------------ #
    # Reminders                                                            #
    # ------------------------------------------------------------------ #

    def _add_reminder(self, text: str) -> str:
        # Simple extraction: "ricorda di <thing>"
        for marker in ["ricorda di ", "reminder: ", "promemoria: ", "remind me to "]:
            if marker in text:
                reminder = text.split(marker, 1)[1].strip().rstrip(".")
                self._reminders.append({
                    "text": reminder,
                    "created_at": datetime.datetime.now().isoformat(),
                })
                return f"Ho aggiunto il promemoria: '{reminder}', Sir."
        return f"Non ho capito cosa devo ricordare, Sir. Dica 'ricorda di [cosa]'."

    def get_reminders(self) -> list[dict]:
        return self._reminders

    # ------------------------------------------------------------------ #
    # Timer                                                                #
    # ------------------------------------------------------------------ #

    async def _set_timer(self, text: str) -> str:
        minutes = self._extract_minutes(text)
        if not minutes:
            return "Non ho capito la durata del timer, Sir."

        async def _timer_task():
            await asyncio.sleep(minutes * 60)
            logger.info("⏰ TIMER scaduto (%d minuti)", minutes)
            print(f"\n⏰ JARVIS: Timer di {minutes} minuti scaduto, Sir!\n")

        task = asyncio.create_task(_timer_task())
        self._timers.append(task)
        return f"Timer impostato per {minutes} minuti, Sir."

    @staticmethod
    def _extract_minutes(text: str) -> Optional[int]:
        import re
        patterns = [
            r"(\d+)\s*minut",
            r"(\d+)\s*min",
            r"tra\s+(\d+)",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return int(m.group(1))
        return None

    # ------------------------------------------------------------------ #
    # Quick commands                                                       #
    # ------------------------------------------------------------------ #

    async def _run_quick_command(self, keyword: str, cmd: str) -> str:
        try:
            result = await self._run_shell(cmd)
            return f"Comando '{keyword}' eseguito, Sir."
        except Exception as e:
            return f"Errore nell'eseguire '{keyword}': {e}"

    # ------------------------------------------------------------------ #
    # Shell helper                                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    async def _run_shell(cmd: str) -> str:
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        return stdout.decode(errors="replace")
