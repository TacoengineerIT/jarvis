"""
jarvis_memory_patterns.py — Pattern detection over JARVIS mood + conversation history.
Pure statistical analysis, no ML required.
"""
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("jarvis.memory.patterns")

# ── Pattern types ─────────────────────────────────────────────────────────────

PATTERN_TYPES = {
    "monday_stress":      "Stress elevato il lunedì",
    "weekend_energy":     "Energia alta nel weekend",
    "post_lunch_slump":   "Calo energia post-pranzo (13-15h)",
    "morning_anxiety":    "Ansia mattutina (6-9h)",
    "evening_calm":       "Rilassamento serale (19-22h)",
    "late_night_stress":  "Stress notturno (22-24h)",
    "deadline_trigger":   "Stress da deadline/scadenza",
    "exercise_boost":     "Miglioramento umore dopo esercizio",
    "monday_to_friday_rise": "Umore in salita durante la settimana",
}

_RECOMMENDED_ACTIONS = {
    "monday_stress":      "Suggerisci rituale mattutino (caffè, passeggiata) il lunedì.",
    "post_lunch_slump":   "Suggerisci pausa caffè o micro-nap (20min) alle 14:00.",
    "morning_anxiety":    "Suggerisci respirazione o meditazione breve al mattino.",
    "evening_calm":       "Sfrutta la serata per attività creative o lettura.",
    "late_night_stress":  "Suggerisci di smettere di lavorare e prepararsi al sonno.",
    "deadline_trigger":   "Pianifica piccole milestone intermedie per ridurre la pressione.",
    "exercise_boost":     "Ricorda all'utente di fare esercizio quando è giù.",
    "weekend_energy":     "Pianifica attività creative/ricreative nel weekend.",
    "monday_to_friday_rise": "Ricorda che la settimana migliora giorno per giorno.",
}

_MIN_CONFIDENCE = 0.55   # below this, don't report a pattern
_MIN_DATA_POINTS = 3     # need at least this many samples to detect a pattern


class PatternDetector:
    """
    Detects recurring mood and behaviour patterns from JarvisMemory data.
    Uses statistical analysis over mood_timeline + conversation history.
    """

    def __init__(self, memory=None):
        if memory is None:
            from jarvis_memory import JarvisMemory
            memory = JarvisMemory()
        self.memory = memory

    # ── Public API ────────────────────────────────────────────────────────────

    def detect_stress_patterns(self, window_days: int = 30) -> list[dict]:
        """
        Analyse mood_timeline to find recurring stress patterns.
        Returns list of pattern dicts sorted by confidence desc.
        """
        timeline = self.memory.get_mood_timeline(days=window_days)
        if len(timeline) < _MIN_DATA_POINTS:
            return []

        patterns = []
        patterns.extend(self._detect_day_of_week_patterns(timeline))
        patterns.extend(self._detect_hour_patterns(timeline))
        patterns.extend(self._detect_keyword_triggers(timeline))

        # Deduplicate + filter by confidence
        seen = set()
        result = []
        for p in sorted(patterns, key=lambda x: x["confidence"], reverse=True):
            if p["pattern_type"] not in seen and p["confidence"] >= _MIN_CONFIDENCE:
                seen.add(p["pattern_type"])
                result.append(p)

        # Persist to DB
        for p in result:
            self.memory.save_pattern(p)

        return result

    def detect_energy_cycles(self) -> dict:
        """
        Identify the user's peak productivity / energy windows.
        Returns: {peak_hours, low_hours, description}
        """
        timeline = self.memory.get_mood_timeline(days=14)
        if len(timeline) < _MIN_DATA_POINTS:
            return {
                "peak_hours": "mattina (9-12)",
                "low_hours":  "post-pranzo (13-15)",
                "description": "Dati insufficienti — usando valori circadiani standard.",
                "data_driven": False,
            }

        hour_scores: dict[int, list[float]] = defaultdict(list)
        for row in timeline:
            h = row.get("hour")
            s = row.get("mood_score")
            if h is not None and s is not None:
                hour_scores[h].append(s)

        if not hour_scores:
            return {"peak_hours": "mattina", "low_hours": "post-pranzo",
                    "description": "Nessun dato orario.", "data_driven": False}

        avg_by_hour = {h: sum(v)/len(v) for h, v in hour_scores.items() if len(v) >= 1}
        if not avg_by_hour:
            return {"peak_hours": "mattina", "low_hours": "post-pranzo",
                    "description": "Nessun dato.", "data_driven": False}

        peak_hour = max(avg_by_hour, key=avg_by_hour.get)
        low_hour  = min(avg_by_hour, key=avg_by_hour.get)

        return {
            "peak_hours":  f"{peak_hour:02d}:00-{peak_hour+1:02d}:00",
            "low_hours":   f"{low_hour:02d}:00-{low_hour+1:02d}:00",
            "avg_by_hour": {f"{h:02d}h": round(v, 1) for h, v in sorted(avg_by_hour.items())},
            "description": (
                f"Picco energetico: {peak_hour:02d}:00. "
                f"Calo: {low_hour:02d}:00."
            ),
            "data_driven": True,
        }

    def detect_trigger_keywords(self) -> list[dict]:
        """
        Find keywords that consistently correlate with low/high mood scores.
        Returns list: {keyword, effect: "negative"|"positive", avg_mood_delta, frequency}
        """
        timeline = self.memory.get_mood_timeline(days=30)
        if len(timeline) < _MIN_DATA_POINTS:
            return []

        # Collect keyword → mood scores
        kw_scores: dict[str, list[float]] = defaultdict(list)
        overall_scores: list[float] = []
        for row in timeline:
            score = row.get("mood_score")
            if score is None:
                continue
            overall_scores.append(score)
            kws = json.loads(row.get("triggering_keywords", "[]") or "[]")
            for kw in kws:
                kw_scores[kw].append(score)

        if not overall_scores:
            return []

        baseline = sum(overall_scores) / len(overall_scores)

        triggers = []
        for kw, scores in kw_scores.items():
            if len(scores) < 2:
                continue
            avg = sum(scores) / len(scores)
            delta = avg - baseline
            if abs(delta) >= 0.8:  # meaningful difference
                triggers.append({
                    "keyword":         kw,
                    "effect":          "positive" if delta > 0 else "negative",
                    "avg_mood_delta":  round(delta, 2),
                    "avg_mood_score":  round(avg, 2),
                    "frequency":       len(scores),
                })

        triggers.sort(key=lambda t: abs(t["avg_mood_delta"]), reverse=True)
        return triggers[:10]

    def recommend_action_for_mood(self, current_mood: str) -> str:
        """
        Return a personalised suggestion based on past patterns and current mood.
        Falls back to generic advice if no data.
        """
        # Get saved patterns from DB
        saved_patterns = self.memory.get_patterns()
        now = datetime.now()

        # Time-contextual pattern matching
        dow = now.weekday()   # 0=Monday
        hour = now.hour

        # Check saved patterns for active matches
        for p in saved_patterns:
            ptype = p.get("pattern_type", "")
            if ptype == "monday_stress" and dow == 0 and hour < 12:
                return _RECOMMENDED_ACTIONS["monday_stress"]
            if ptype == "post_lunch_slump" and 13 <= hour <= 15:
                return _RECOMMENDED_ACTIONS["post_lunch_slump"]
            if ptype == "morning_anxiety" and 6 <= hour <= 9:
                return _RECOMMENDED_ACTIONS["morning_anxiety"]
            if ptype == "late_night_stress" and hour >= 22:
                return _RECOMMENDED_ACTIONS["late_night_stress"]

        # Mood-based fallback
        _MOOD_FALLBACK = {
            "stressed":  "Fai una pausa di 10 minuti. Una passeggiata o respirazione profonda aiutano.",
            "anxious":   "Respira lentamente. Scrivi 3 cose che puoi controllare ora.",
            "tired":     "Considera una micro-siesta (20min) o un caffè. Non forzare.",
            "sad":       "Ascolta musica che ti piace. Parla con qualcuno di cui ti fidi.",
            "angry":     "Cammina, fai esercizio fisico. L'energia va scaricata fisicamente.",
            "neutral":   "Ottimo momento per lavoro di concentrazione profonda.",
            "happy":     "Sfrutta questo momento di energia per i task creativi.",
            "calm":      "Ideale per pianificazione a lungo termine.",
        }
        return _MOOD_FALLBACK.get(
            current_mood.lower(),
            "Prenditi cura di te, Sir. Un po' di riposo non guasta mai.",
        )

    def get_weekly_summary(self) -> dict:
        """
        Summarise the current week's mood patterns for morning briefing.
        """
        timeline = self.memory.get_mood_timeline(days=7)
        if not timeline:
            return {
                "avg_score": None,
                "best_day": None,
                "worst_day": None,
                "trend": "unknown",
                "summary": "Nessun dato per questa settimana.",
            }

        day_scores: dict[int, list[float]] = defaultdict(list)
        scores_all: list[float] = []
        for row in timeline:
            score = row.get("mood_score")
            if score is None:
                continue
            scores_all.append(score)
            created = row.get("created_at", "")
            try:
                dt = datetime.fromisoformat(created[:19])
                day_scores[dt.weekday()].append(score)
            except Exception:
                pass

        if not scores_all:
            return {"avg_score": None, "best_day": None, "worst_day": None,
                    "trend": "unknown", "summary": "Nessun dato."}

        avg = sum(scores_all) / len(scores_all)
        day_avgs = {d: sum(v)/len(v) for d, v in day_scores.items()}
        _DOW = ["Lunedì","Martedì","Mercoledì","Giovedì","Venerdì","Sabato","Domenica"]

        best_day  = _DOW[max(day_avgs, key=day_avgs.get)] if day_avgs else "N/D"
        worst_day = _DOW[min(day_avgs, key=day_avgs.get)] if day_avgs else "N/D"

        # Trend: compare first half vs second half
        mid = len(scores_all) // 2
        if mid > 0:
            delta = sum(scores_all[mid:]) / len(scores_all[mid:]) - sum(scores_all[:mid]) / mid
            trend = "migliorando" if delta > 0.3 else "peggiorando" if delta < -0.3 else "stabile"
        else:
            trend = "stabile"

        return {
            "avg_score": round(avg, 1),
            "best_day":  best_day,
            "worst_day": worst_day,
            "trend":     trend,
            "summary": (
                f"Media settimanale: {avg:.1f}/10. "
                f"Giorno migliore: {best_day}. "
                f"Giorno peggiore: {worst_day}. "
                f"Tendenza: {trend}."
            ),
        }

    # ── Internal analysis ─────────────────────────────────────────────────────

    def _detect_day_of_week_patterns(self, timeline: list[dict]) -> list[dict]:
        """Detect day-of-week stress/energy patterns."""
        day_scores: dict[int, list[float]] = defaultdict(list)
        for row in timeline:
            created = row.get("created_at", "")
            score = row.get("mood_score")
            if not created or score is None:
                continue
            try:
                dt = datetime.fromisoformat(created[:19])
                day_scores[dt.weekday()].append(score)
            except Exception:
                continue

        if not day_scores:
            return []

        overall_avg = sum(s for v in day_scores.values() for s in v) / sum(len(v) for v in day_scores.values())
        patterns = []

        for dow, scores in day_scores.items():
            if len(scores) < _MIN_DATA_POINTS:
                continue
            avg = sum(scores) / len(scores)
            if dow == 0 and avg < overall_avg - 1.0:  # Monday significantly worse
                confidence = min(0.5 + (overall_avg - avg) * 0.1 * len(scores), 0.98)
                patterns.append({
                    "pattern_type": "monday_stress",
                    "frequency": len(scores),
                    "confidence": round(confidence, 2),
                    "associated_keywords": json.dumps(["lunedì", "stress", "inizio settimana"]),
                    "recommended_action": _RECOMMENDED_ACTIONS["monday_stress"],
                    "avg_score": round(avg, 2),
                })
            if dow in (4, 5) and avg > overall_avg + 0.8:  # Friday/Saturday high
                confidence = min(0.5 + (avg - overall_avg) * 0.08 * len(scores), 0.95)
                patterns.append({
                    "pattern_type": "weekend_energy",
                    "frequency": len(scores),
                    "confidence": round(confidence, 2),
                    "associated_keywords": json.dumps(["weekend", "energia", "libero"]),
                    "recommended_action": _RECOMMENDED_ACTIONS["weekend_energy"],
                    "avg_score": round(avg, 2),
                })

        # Check monotonic rise Mon→Fri
        if all(d in day_scores for d in range(5)):
            mon_avg = sum(day_scores[0]) / len(day_scores[0])
            fri_avg = sum(day_scores[4]) / len(day_scores[4])
            if fri_avg > mon_avg + 2.0:
                patterns.append({
                    "pattern_type": "monday_to_friday_rise",
                    "frequency": sum(len(day_scores[d]) for d in range(5)),
                    "confidence": round(min(0.6 + (fri_avg - mon_avg) * 0.05, 0.90), 2),
                    "associated_keywords": json.dumps(["settimana", "progressione"]),
                    "recommended_action": _RECOMMENDED_ACTIONS["monday_to_friday_rise"],
                    "avg_score": None,
                })

        return patterns

    def _detect_hour_patterns(self, timeline: list[dict]) -> list[dict]:
        """Detect time-of-day patterns."""
        hour_scores: dict[int, list[float]] = defaultdict(list)
        for row in timeline:
            h = row.get("hour")
            score = row.get("mood_score")
            if h is not None and score is not None:
                hour_scores[h].append(score)

        if not hour_scores:
            return []

        overall_scores = [s for v in hour_scores.values() for s in v]
        if not overall_scores:
            return []
        overall_avg = sum(overall_scores) / len(overall_scores)

        patterns = []

        # Post-lunch slump 13-15h
        lunch_hours = [h for h in (13, 14, 15) if h in hour_scores and len(hour_scores[h]) >= _MIN_DATA_POINTS]
        if lunch_hours:
            lunch_avg = sum(s for h in lunch_hours for s in hour_scores[h]) / sum(len(hour_scores[h]) for h in lunch_hours)
            if lunch_avg < overall_avg - 0.8:
                n = sum(len(hour_scores[h]) for h in lunch_hours)
                confidence = min(0.55 + (overall_avg - lunch_avg) * 0.08 * n / 5, 0.92)
                patterns.append({
                    "pattern_type": "post_lunch_slump",
                    "frequency": n,
                    "confidence": round(confidence, 2),
                    "associated_keywords": json.dumps(["pranzo", "pomeriggio", "stanchezza"]),
                    "recommended_action": _RECOMMENDED_ACTIONS["post_lunch_slump"],
                    "avg_score": round(lunch_avg, 2),
                })

        # Morning anxiety 6-9h
        morn_hours = [h for h in (6, 7, 8, 9) if h in hour_scores and len(hour_scores[h]) >= _MIN_DATA_POINTS]
        if morn_hours:
            morn_avg = sum(s for h in morn_hours for s in hour_scores[h]) / sum(len(hour_scores[h]) for h in morn_hours)
            if morn_avg < overall_avg - 0.5:
                n = sum(len(hour_scores[h]) for h in morn_hours)
                patterns.append({
                    "pattern_type": "morning_anxiety",
                    "frequency": n,
                    "confidence": round(min(0.55 + (overall_avg - morn_avg) * 0.07 * n / 5, 0.90), 2),
                    "associated_keywords": json.dumps(["mattina", "ansia", "sveglia"]),
                    "recommended_action": _RECOMMENDED_ACTIONS["morning_anxiety"],
                    "avg_score": round(morn_avg, 2),
                })

        # Evening calm 19-22h
        eve_hours = [h for h in (19, 20, 21, 22) if h in hour_scores and len(hour_scores[h]) >= _MIN_DATA_POINTS]
        if eve_hours:
            eve_avg = sum(s for h in eve_hours for s in hour_scores[h]) / sum(len(hour_scores[h]) for h in eve_hours)
            if eve_avg > overall_avg + 0.5:
                n = sum(len(hour_scores[h]) for h in eve_hours)
                patterns.append({
                    "pattern_type": "evening_calm",
                    "frequency": n,
                    "confidence": round(min(0.55 + (eve_avg - overall_avg) * 0.07 * n / 5, 0.90), 2),
                    "associated_keywords": json.dumps(["sera", "rilassato", "riposo"]),
                    "recommended_action": _RECOMMENDED_ACTIONS["evening_calm"],
                    "avg_score": round(eve_avg, 2),
                })

        return patterns

    def _detect_keyword_triggers(self, timeline: list[dict]) -> list[dict]:
        """Detect keywords that consistently trigger stress."""
        kw_scores: dict[str, list[float]] = defaultdict(list)
        all_scores: list[float] = []

        for row in timeline:
            score = row.get("mood_score")
            if score is None:
                continue
            all_scores.append(score)
            kws = json.loads(row.get("triggering_keywords", "[]") or "[]")
            for kw in kws:
                kw_scores[kw].append(score)

        if not all_scores:
            return []

        baseline = sum(all_scores) / len(all_scores)
        patterns = []

        for kw, scores in kw_scores.items():
            if len(scores) < _MIN_DATA_POINTS:
                continue
            avg = sum(scores) / len(scores)
            if kw in ("deadline", "scadenza", "esame") and avg < baseline - 1.0:
                patterns.append({
                    "pattern_type": "deadline_trigger",
                    "frequency": len(scores),
                    "confidence": round(min(0.6 + len(scores) * 0.05, 0.92), 2),
                    "associated_keywords": json.dumps([kw, "stress", "pressione"]),
                    "recommended_action": _RECOMMENDED_ACTIONS["deadline_trigger"],
                    "avg_score": round(avg, 2),
                })
            if kw in ("palestra", "gym", "corsa", "esercizio") and avg > baseline + 1.0:
                patterns.append({
                    "pattern_type": "exercise_boost",
                    "frequency": len(scores),
                    "confidence": round(min(0.6 + len(scores) * 0.05, 0.92), 2),
                    "associated_keywords": json.dumps([kw, "energia", "benessere"]),
                    "recommended_action": _RECOMMENDED_ACTIONS["exercise_boost"],
                    "avg_score": round(avg, 2),
                })

        return patterns
