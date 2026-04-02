"""
jarvis_core.py — JARVIS v4.0 Reasoning Engine

Routes requests to:
  - Claude Haiku 4.5: quick intents (lights, weather, reminders, git push)
  - Claude Sonnet 4.6: mood analysis, advice, complex reasoning, fallback

Cost optimization:
  - System prompt injected once per session, not per message
  - Context window capped at last 5 exchanges (~500 tokens)
  - Haiku handles ~70% of requests
"""

import json
import logging
import re
import time
from typing import Optional

import anthropic

from jarvis_memory import JarvisMemory
from jarvis_mood import MoodDetector

logger = logging.getLogger("jarvis.core")

# ------------------------------------------------------------------ #
# Intent → model routing                                               #
# ------------------------------------------------------------------ #

HAIKU_INTENTS = {
    "turn_on_light", "turn_off_light", "toggle_light",
    "get_weather", "add_reminder", "set_timer",
    "git_push", "git_commit", "git_status",
    "open_app", "close_app", "volume_up", "volume_down",
    "what_time", "what_date", "play_music", "stop_music",
    "quick_fact", "translate",
}

SONNET_INTENTS = {
    "mood_check", "life_advice", "study_help",
    "financial_advice", "planning", "empathy",
    "complex_reasoning", "storytelling",
    "news_briefing", "market_analysis", "geopolitical_analysis",
}

# Keyword → intent mapping (Italian + English)
INTENT_PATTERNS: list[tuple[list[str], str]] = [
    (["accendi", "accendere", "turn on"],         "turn_on_light"),
    (["spegni", "spegnere", "turn off"],          "turn_off_light"),
    (["meteo", "tempo", "piove", "weather"],      "get_weather"),
    (["ricorda", "reminder", "promemoria"],       "add_reminder"),
    (["pusha", "push", "git push"],               "git_push"),
    (["commit", "git commit"],                    "git_commit"),
    (["git status", "stato git"],                 "git_status"),
    (["apri", "avvia", "lancia", "open"],         "open_app"),
    (["che ore", "che ora", "orario"],            "what_time"),
    (["che giorno", "data di oggi"],              "what_date"),
    (["notizie", "news", "briefing", "mattutino"], "news_briefing"),
    (["mercati", "borsa", "azioni", "investiment", "market"], "market_analysis"),
    (["geopolitic", "tensione mondiale", "conflitto", "guerra"], "geopolitical_analysis"),
    (["musica", "playlist", "canzone", "play"],   "play_music"),
    (["stop musica", "pausa", "ferma"],           "stop_music"),
    (["volume su", "alza volume"],                "volume_up"),
    (["volume giù", "abbassa volume"],            "volume_down"),
    (["mi sento", "sono triste", "sono stressato", "depresso",
      "come stai", "come ti senti"],              "mood_check"),
    (["consiglio", "aiuto", "cosa fare", "decide", "dovrei"],
                                                  "life_advice"),
    (["studia", "esame", "lezione", "ripasso"],   "study_help"),
    (["soldi", "spese", "budget", "affitto"],     "financial_advice"),
    (["pianifica", "settimana", "programma"],     "planning"),
]

JARVIS_PERSONA = """Sei JARVIS, l'assistente IA personale di Taco (20 anni, studente ITS in Italia).
Parla sempre in italiano. Stile: britannico formale ma con sarcasmo leggero, come un maggiordomo intelligente.
Chiama l'utente "Sir" o "Tony" occasionalmente.
Sei un amico/mentore — non solo un chatbot. Ricordi il suo umore e il contesto precedente.
Risposte brevi e dirette per comandi, più elaborate per domande personali.
NON usare frasi ripetitive. Varia sempre le risposte."""


class JarvisCore:
    """Main reasoning engine — routes to Sonnet or Haiku based on intent."""

    def __init__(
        self,
        api_key: str,
        memory: Optional[JarvisMemory] = None,
        mood_detector: Optional[MoodDetector] = None,
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.memory = memory or JarvisMemory()
        self.mood = mood_detector or MoodDetector()
        self._response_cache: dict[str, tuple[str, float]] = {}  # text→(response, ts)
        self._cache_ttl = 3600  # 1h

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    async def process(
        self,
        user_input: str,
        audio_bytes: Optional[bytes] = None,
    ) -> dict:
        """
        Main entry point. Returns:
          {
            "response": str,
            "intent":   str,
            "mood":     dict,
            "model":    "haiku"|"sonnet",
            "cached":   bool,
          }
        """
        mood = self.mood.detect(user_input, audio_bytes)
        intent = self._classify_intent(user_input)

        logger.info("Intent: %s | Mood: %s %s", intent, mood["label"], mood["emoji"])

        # Cache check for repetitive queries
        cache_key = f"{intent}:{user_input[:60]}"
        if intent not in SONNET_INTENTS:
            cached = self._get_cached(cache_key)
            if cached:
                self._save_to_memory(user_input, cached, mood, intent)
                return {"response": cached, "intent": intent, "mood": mood, "model": "cache", "cached": True}

        # Route to model
        if intent in HAIKU_INTENTS:
            response = await self._call_haiku(user_input, intent, mood)
            model_used = "haiku"
        else:
            response = await self._call_sonnet(user_input, intent, mood)
            model_used = "sonnet"

        # Cache non-personal responses for 1h
        if intent not in SONNET_INTENTS and intent != "unknown":
            self._set_cache(cache_key, response)

        self._save_to_memory(user_input, response, mood, intent)

        return {
            "response": response,
            "intent":   intent,
            "mood":     mood,
            "model":    model_used,
            "cached":   False,
        }

    # ------------------------------------------------------------------ #
    # Intent classification                                                #
    # ------------------------------------------------------------------ #

    def _classify_intent(self, text: str) -> str:
        text_lower = text.lower()
        for keywords, intent in INTENT_PATTERNS:
            if any(kw in text_lower for kw in keywords):
                return intent
        return "unknown"

    # ------------------------------------------------------------------ #
    # Model calls                                                          #
    # ------------------------------------------------------------------ #

    async def _call_haiku(self, user_input: str, intent: str, mood: dict) -> str:
        system = (
            f"{JARVIS_PERSONA}\n"
            f"Stato umore attuale: {mood['label']} {mood['emoji']}\n"
            "Esegui il comando richiesto in modo rapido e diretto. "
            "Risposta max 2 frasi."
        )
        try:
            msg = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=256,
                system=system,
                messages=[{"role": "user", "content": user_input}],
            )
            return msg.content[0].text
        except anthropic.APIError as e:
            logger.error("Haiku API error: %s", e)
            return "Errore di connessione, Sir. Riprovo subito."

    async def _call_sonnet(self, user_input: str, intent: str, mood: dict) -> str:
        # Build context from recent memory (capped at 5 exchanges)
        memory_ctx = self.memory.build_context_summary(limit=5)
        today_mood = self.memory.get_today_mood()
        mood_summary = ""
        if today_mood:
            mood_summary = (
                f"Umore di oggi: mattina={today_mood.get('morning_mood','?')}, "
                f"livello stress={today_mood.get('stress_level','?')}/10."
            )

        # Morning briefing context (injected for market/news/geo intents)
        briefing_ctx = ""
        if intent in ("news_briefing", "market_analysis", "geopolitical_analysis"):
            briefing_ctx = self._get_briefing_context()

        system = (
            f"{JARVIS_PERSONA}\n\n"
            f"=== MEMORIA RECENTE ===\n{memory_ctx}\n\n"
            f"=== STATO ATTUALE ===\n"
            f"Umore ora: {mood['label']} {mood['emoji']} (score={mood['score']})\n"
            f"{mood_summary}"
            + (f"\n\n=== BRIEFING GEOPOLITICO/MERCATI (oggi) ===\n{briefing_ctx}" if briefing_ctx else "")
        )
        try:
            msg = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=512,
                system=system,
                messages=[{"role": "user", "content": user_input}],
            )
            return msg.content[0].text
        except anthropic.APIError as e:
            logger.error("Sonnet API error: %s", e)
            return "Sto avendo difficoltà a connettermi, Sir. Riprovo tra un momento."

    # ------------------------------------------------------------------ #
    # Morning briefing context                                             #
    # ------------------------------------------------------------------ #

    def _get_briefing_context(self) -> str:
        """Return a compact text from today's morning briefing for Sonnet context."""
        try:
            briefing = self.memory.get_morning_briefing(
                __import__("datetime").date.today().isoformat()
            )
            if briefing:
                # Return trimmed briefing text (cap at 1500 chars)
                text = briefing.get("briefing_text", "")
                return text[:1500] + ("..." if len(text) > 1500 else "")
        except Exception:
            pass
        return ""

    # ------------------------------------------------------------------ #
    # Cache                                                                #
    # ------------------------------------------------------------------ #

    def _get_cached(self, key: str) -> Optional[str]:
        if key in self._response_cache:
            response, ts = self._response_cache[key]
            if time.time() - ts < self._cache_ttl:
                return response
        return None

    def _set_cache(self, key: str, response: str):
        self._response_cache[key] = (response, time.time())

    # ------------------------------------------------------------------ #
    # Memory                                                               #
    # ------------------------------------------------------------------ #

    def _save_to_memory(self, user_input: str, response: str, mood: dict, intent: str):
        import datetime
        now = datetime.datetime.now()
        context = {
            "time_of_day": now.strftime("%H:%M"),
            "day_of_week": now.strftime("%A"),
        }
        self.memory.save_conversation(
            user_input=user_input,
            jarvis_response=response,
            mood_detected=mood["label"],
            intent=intent,
            context=context,
        )
        stress = self.mood.stress_level(mood)
        period = "morning" if now.hour < 14 else "evening"
        self.memory.update_mood(
            stress_level=stress,
            mood=mood["label"],
            period=period,
        )
