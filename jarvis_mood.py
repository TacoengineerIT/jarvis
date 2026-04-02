"""
jarvis_mood.py — JARVIS v4.0 Mood Detection

Combines 3 signals:
  1. Voice tone (energy + pitch variance from raw audio bytes)
  2. Temporal pattern (time of day + day of week)
  3. Keyword analysis (Italian emotion words)

Returns: mood_label (str) + score (float 0-1) + emoji
"""

import datetime
import logging
import math
from typing import Optional

logger = logging.getLogger("jarvis.mood")

# Italian emotion keywords
_SAD_WORDS = {
    "stressato", "stressata", "depresso", "depressa", "giù", "male",
    "triste", "ansioso", "ansiosa", "stanco", "stanca", "esausto",
    "arrabbiato", "arrabbiata", "preoccupato", "preoccupata",
    "brutto", "terribile", "orribile", "pessimo", "pessima",
    "non riesco", "non ce la faccio", "difficile", "fatico"
}
_HAPPY_WORDS = {
    "felice", "contento", "contenta", "bene", "benissimo", "ottimo",
    "entusiasta", "eccitato", "eccitata", "fantastico", "fantastica",
    "meraviglioso", "meravigliosa", "perfetto", "perfetta",
    "riuscito", "riuscita", "bravo", "brava", "funziona", "funziona"
}
_STRESSED_WORDS = {
    "confuso", "confusa", "perso", "persa", "help", "aiuto",
    "non capisco", "non so", "non so cosa fare", "paura", "scadenza",
    "esame", "interrogazione", "consegna", "urgent", "urgente"
}

# Mood → emoji mapping
MOOD_EMOJI = {
    "happy":   "😊",
    "neutral": "😐",
    "sad":     "😞",
    "stressed":"😤",
}


def _voice_tone_score(audio_bytes: Optional[bytes]) -> float:
    """
    Returns 0.0 (low energy/sad) → 1.0 (high energy/happy).
    Uses RMS amplitude of int16 PCM samples.
    Returns 0.5 if no audio.
    """
    if not audio_bytes or len(audio_bytes) < 2:
        return 0.5
    import struct
    n_samples = len(audio_bytes) // 2
    samples = struct.unpack(f"{n_samples}h", audio_bytes[:n_samples * 2])
    rms = math.sqrt(sum(s * s for s in samples) / n_samples) if n_samples else 0
    # Normalise: 0→0.0,  ~3000→0.5,  ~8000+→1.0
    score = min(rms / 8000.0, 1.0)
    return score


def _temporal_score() -> float:
    """
    Returns baseline mood modifier from time/day.
    0.0 = low baseline, 1.0 = high baseline.
    """
    now = datetime.datetime.now()
    hour = now.hour
    weekday = now.weekday()  # 0=Monday

    # Time of day modifier
    if 6 <= hour < 9:
        time_score = 0.35   # early morning — low
    elif 9 <= hour < 12:
        time_score = 0.55   # morning — ok
    elif 12 <= hour < 14:
        time_score = 0.60   # lunch — slightly better
    elif 14 <= hour < 18:
        time_score = 0.55   # afternoon
    elif 18 <= hour < 22:
        time_score = 0.65   # evening — variable
    else:
        time_score = 0.40   # night — tired

    # Day of week modifier
    day_modifier = 0.0
    if weekday == 0:   # Monday
        day_modifier = -0.05
    elif weekday == 4:  # Friday
        day_modifier = +0.05
    elif weekday in (5, 6):  # Weekend
        day_modifier = +0.08

    return max(0.0, min(1.0, time_score + day_modifier))


def _keyword_score(text: str) -> tuple[float, str]:
    """
    Returns (score 0–1, dominant_sentiment).
    0.0=very sad, 0.5=neutral, 1.0=very happy.
    """
    text_lower = text.lower()
    words = set(text_lower.split())

    sad_hits = len(words & _SAD_WORDS) + sum(1 for phrase in _SAD_WORDS if " " in phrase and phrase in text_lower)
    happy_hits = len(words & _HAPPY_WORDS) + sum(1 for phrase in _HAPPY_WORDS if " " in phrase and phrase in text_lower)
    stress_hits = len(words & _STRESSED_WORDS) + sum(1 for phrase in _STRESSED_WORDS if " " in phrase and phrase in text_lower)

    if sad_hits == 0 and happy_hits == 0 and stress_hits == 0:
        return 0.5, "neutral"

    total = sad_hits + happy_hits + stress_hits
    if happy_hits >= sad_hits and happy_hits >= stress_hits:
        score = 0.5 + min(0.5, (happy_hits / total) * 0.5)
        return score, "happy"
    elif stress_hits >= sad_hits:
        score = 0.3
        return score, "stressed"
    else:
        score = 0.5 - min(0.4, (sad_hits / total) * 0.4)
        return score, "sad"


class MoodDetector:
    """Combines voice tone, temporal signal, and keyword analysis into a mood label."""

    WEIGHTS = (0.4, 0.3, 0.3)  # voice, temporal, keyword

    def detect(
        self,
        text: str,
        audio_bytes: Optional[bytes] = None,
    ) -> dict:
        """
        Returns:
          {
            "label":  "happy"|"neutral"|"sad"|"stressed",
            "score":  float 0–1,
            "emoji":  str,
            "signals": {"voice": float, "temporal": float, "keyword": float}
          }
        """
        voice_s = _voice_tone_score(audio_bytes)
        temporal_s = _temporal_score()
        keyword_s, keyword_label = _keyword_score(text)

        combined = (
            self.WEIGHTS[0] * voice_s
            + self.WEIGHTS[1] * temporal_s
            + self.WEIGHTS[2] * keyword_s
        )

        # Map combined score to label
        # Strong keyword signals override the combined score
        if keyword_label == "happy" and keyword_s >= 0.70:
            label = "happy"
        elif keyword_label in ("sad", "stressed") and keyword_s <= 0.35:
            label = keyword_label
        elif combined >= 0.62:
            label = "happy"
        elif combined >= 0.48:
            label = "neutral"
        elif combined >= 0.36:
            label = "sad"
        else:
            label = "stressed"

        result = {
            "label": label,
            "score": round(combined, 3),
            "emoji": MOOD_EMOJI[label],
            "signals": {
                "voice": round(voice_s, 3),
                "temporal": round(temporal_s, 3),
                "keyword": round(keyword_s, 3),
            },
        }
        logger.debug("Mood detected: %s", result)
        return result

    def stress_level(self, mood: dict) -> int:
        """Convert mood score to 1-10 stress level (10=most stressed)."""
        score = mood["score"]
        if mood["label"] == "stressed":
            return max(7, int((1 - score) * 10))
        return max(1, min(10, int((1 - score) * 10)))
