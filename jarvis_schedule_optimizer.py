"""
jarvis_schedule_optimizer.py — Break recommendations and schedule analysis.
Rule-based logic; learns from break_history stored in JarvisMemory.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("jarvis.schedule")

# ── Constants ─────────────────────────────────────────────────────────────────

MAX_CONSECUTIVE_WORK_HOURS = 4   # Suggest break after this many h without one
SHORT_BREAK_MINUTES        = 10
MEDIUM_BREAK_MINUTES       = 20
LONG_BREAK_MINUTES         = 60

_BREAK_TYPES = {
    "walk":     {"duration": 20, "benefits": ["riduce stress", "aumenta focus", "esercizio fisico"]},
    "coffee":   {"duration": 10, "benefits": ["energia rapida", "pausa mentale"]},
    "nap":      {"duration": 20, "benefits": ["recupero profondo", "riduce fatica"]},
    "exercise": {"duration": 30, "benefits": ["riduce cortisolo", "migliora umore", "energia"]},
    "stretch":  {"duration":  5, "benefits": ["riduce tensione muscolare", "veloce"]},
}

_STRESS_THRESHOLDS = {
    "LOW":    (0, 2),
    "MEDIUM": (3, 5),
    "HIGH":   (6, 8),
    "EXTREME":(9, 99),
}


def _parse_dt(dt_str: str) -> Optional[datetime]:
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(dt_str[:19], fmt[:len(fmt)])
        except ValueError:
            pass
    return None


def _minutes_until(dt: datetime) -> int:
    """Return minutes from now until dt (negative if in the past)."""
    now = datetime.now()
    dt_naive = dt.replace(tzinfo=None) if dt.tzinfo else dt
    return int((dt_naive - now).total_seconds() / 60)


class ScheduleOptimizer:
    """
    Analyses today's schedule and recommends breaks and work patterns.
    Uses break_history from memory to improve recommendations over time.
    """

    def __init__(self, calendar_manager=None, memory=None):
        if calendar_manager is None:
            from jarvis_calendar import CalendarManager
            calendar_manager = CalendarManager()
        self.calendar = calendar_manager

        if memory is None:
            from jarvis_memory import JarvisMemory
            memory = JarvisMemory()
        self.memory = memory

    # ── Public API ────────────────────────────────────────────────────────────

    def recommend_break(self) -> dict:
        """
        Recommend a break based on today's schedule and current time.

        Returns:
        {
            "should_break": bool,
            "recommendation": str,
            "break_type": str,
            "duration_minutes": int,
            "best_time": str,   # "now" | "HH:MM"
            "benefits": list[str],
            "reason": str,
        }
        """
        now = datetime.now()
        events = self.calendar.get_todays_schedule()
        free_slots = self.calendar.get_free_slots(duration_minutes=10)
        next_ev = self.calendar.get_next_event()
        busy, _, busy_until = self.calendar.is_busy_now()

        # Work out consecutive work hours since last break
        consecutive_h = self._consecutive_work_hours(events, now)

        # Time until next event
        mins_to_next = next_ev["minutes_until"] if next_ev else 999

        # Pick break type based on history
        preferred_type = self._preferred_break_type()

        # ── Decision logic ────────────────────────────────────────────────
        if busy:
            return {
                "should_break": False,
                "recommendation": f"Sei in {busy_until} minuti libero — aspetta.",
                "break_type": preferred_type,
                "duration_minutes": 0,
                "best_time": f"tra {busy_until} min",
                "benefits": [],
                "reason": "Currently in meeting/event",
            }

        if consecutive_h >= MAX_CONSECUTIVE_WORK_HOURS:
            btype = "walk" if now.hour < 17 else "stretch"
            return {
                "should_break": True,
                "recommendation": (
                    f"Lavori da {consecutive_h:.0f}h di fila, Sir. "
                    f"Prenditi una pausa — una {btype} ti farà bene."
                ),
                "break_type": btype,
                "duration_minutes": _BREAK_TYPES[btype]["duration"],
                "best_time": "ora",
                "benefits": _BREAK_TYPES[btype]["benefits"],
                "reason": f"{consecutive_h:.0f}h consecutive di lavoro",
            }

        if mins_to_next <= 60 and mins_to_next >= 15:
            btype = "stretch" if mins_to_next < 20 else preferred_type
            dur = min(_BREAK_TYPES[btype]["duration"], mins_to_next - 5)
            return {
                "should_break": True,
                "recommendation": (
                    f"Hai {mins_to_next} min prima di '{next_ev['title']}'. "
                    f"Perfetto per una {btype} veloce."
                ),
                "break_type": btype,
                "duration_minutes": dur,
                "best_time": "ora",
                "benefits": _BREAK_TYPES[btype]["benefits"],
                "reason": f"Finestra libera prima del prossimo evento",
            }

        if free_slots:
            slot = free_slots[0]
            btype = "walk" if slot["duration_minutes"] >= 30 else "coffee"
            return {
                "should_break": True,
                "recommendation": (
                    f"Hai uno slot libero alle {slot['start']} "
                    f"({slot['duration_minutes']} min). "
                    f"Ottimo momento per {btype}."
                ),
                "break_type": btype,
                "duration_minutes": _BREAK_TYPES[btype]["duration"],
                "best_time": slot["start"],
                "benefits": _BREAK_TYPES[btype]["benefits"],
                "reason": "Slot libero disponibile",
            }

        return {
            "should_break": False,
            "recommendation": "Nessuna pausa urgente necessaria ora.",
            "break_type": preferred_type,
            "duration_minutes": 0,
            "best_time": "N/D",
            "benefits": [],
            "reason": "Schedule balanced",
        }

    def suggest_work_time(self) -> dict:
        """
        Return the optimal work period for today based on schedule + time of day.
        """
        now = datetime.now()
        hour = now.hour
        events = self.calendar.get_todays_schedule()
        free_slots = self.calendar.get_free_slots(duration_minutes=60)

        # Circadian productivity windows
        if 6 <= hour < 12:
            quality = "alta"
            suggestion = "Mattina: massima produttività. Lavora sui compiti più impegnativi."
        elif 12 <= hour < 14:
            quality = "bassa"
            suggestion = "Post-pranzo: calo energetico. Ideale per task leggeri o meeting."
        elif 14 <= hour < 17:
            quality = "media"
            suggestion = "Pomeriggio: seconda ondata di energia. Ottimo per coding."
        elif 17 <= hour < 20:
            quality = "decrescente"
            suggestion = "Tardo pomeriggio: inizia a rallentare. Revisioni, email."
        else:
            quality = "bassa"
            suggestion = "Sera: priorità al recupero. Evita lavoro intenso."

        # Next recommended deep-work slot
        deep_work_slot = None
        for slot in free_slots:
            if slot["duration_minutes"] >= 90:
                deep_work_slot = slot
                break

        return {
            "current_quality":  quality,
            "suggestion":       suggestion,
            "hour":             hour,
            "deep_work_slot":   deep_work_slot,
            "total_free_today": sum(s["duration_minutes"] for s in free_slots),
            "event_count_today": len(events),
        }

    def predict_stress_level(self) -> dict:
        """
        Predict today's stress level from calendar density.

        Factors:
        - Number of events
        - High-importance events (deadlines)
        - Back-to-back meetings (< 15min gap)
        - Total busy hours
        """
        events = self.calendar.get_todays_schedule()
        score = self._compute_stress_score(events)

        level = "LOW"
        for lvl, (lo, hi) in _STRESS_THRESHOLDS.items():
            if lo <= score <= hi:
                level = lvl
                break

        recommendations = _stress_recommendations(level, events)

        return {
            "level":            level,
            "score":            score,
            "event_count":      len(events),
            "high_importance":  sum(1 for e in events if e.get("importance", 1) >= 4),
            "back_to_back":     self._count_back_to_back(events),
            "recommendations":  recommendations,
        }

    def optimize_break_timing(self) -> dict:
        """
        Use break history to recommend the most effective break type + timing.
        Returns data-driven recommendations based on past effectiveness.
        """
        history = self.memory.get_break_history(limit=30)

        if not history:
            return {
                "best_break_type": "walk",
                "best_time_of_day": "14:00-15:00",
                "avg_effectiveness": None,
                "insight": "Nessuna cronologia. Inizia a registrare le tue pause!",
                "recommendation": "Prova una passeggiata di 20 minuti oggi e valuta l'effetto.",
            }

        # Aggregate effectiveness by type
        type_stats: dict[str, list[float]] = {}
        for h in history:
            btype = h.get("break_type", "walk")
            eff = h.get("effectiveness", 0.5)
            type_stats.setdefault(btype, []).append(eff)

        best_type = max(type_stats, key=lambda t: sum(type_stats[t]) / len(type_stats[t]))
        best_eff = sum(type_stats[best_type]) / len(type_stats[best_type])

        # Best time of day
        hour_stats: dict[int, list[float]] = {}
        for h in history:
            bt = h.get("actual_break_time") or h.get("scheduled_time", "")
            dt = _parse_dt(bt)
            if dt:
                hour_stats.setdefault(dt.hour, []).append(h.get("effectiveness", 0.5))

        best_hour = max(hour_stats, key=lambda h: sum(hour_stats[h]) / len(hour_stats[h])) if hour_stats else 14
        best_time_str = f"{best_hour:02d}:00-{best_hour+1:02d}:00"

        return {
            "best_break_type":   best_type,
            "best_time_of_day":  best_time_str,
            "avg_effectiveness": round(best_eff, 2),
            "insight": (
                f"Le tue {best_type} hanno efficacia media {best_eff*100:.0f}%. "
                f"Migliore orario: {best_time_str}."
            ),
            "recommendation": (
                f"Programma una {best_type} alle {best_hour:02d}:00 — "
                f"statisticamente il momento più efficace per te."
            ),
        }

    def log_break(
        self,
        break_type: str,
        duration_minutes: int,
        effectiveness: float = 0.5,
        mood_before: float = 0.5,
        mood_after: float = 0.5,
    ):
        """Record a completed break in break_history."""
        self.memory.save_break(
            break_type=break_type,
            duration_minutes=duration_minutes,
            effectiveness=effectiveness,
            mood_before=mood_before,
            mood_after=mood_after,
        )

    # ── Internals ─────────────────────────────────────────────────────────────

    def _consecutive_work_hours(self, events: list[dict], now: datetime) -> float:
        """Estimate hours of continuous work since last break/free period."""
        if not events:
            return 0.0
        # Walk backwards from now to find last gap ≥ 15 min
        busy_periods = []
        for ev in events:
            s = _parse_dt(ev["start_time"])
            e = _parse_dt(ev["end_time"])
            if s and e:
                s = s.replace(tzinfo=None)
                e = e.replace(tzinfo=None)
                if e <= now:
                    busy_periods.append((s, e))

        busy_periods.sort()
        if not busy_periods:
            return 0.0

        # Find continuous work block ending at/before now
        block_start = busy_periods[-1][0]
        for i in range(len(busy_periods) - 1, 0, -1):
            gap = (busy_periods[i][0] - busy_periods[i - 1][1]).total_seconds() / 60
            if gap >= 15:
                block_start = busy_periods[i][0]
                break
            else:
                block_start = busy_periods[i - 1][0]

        return (now - block_start).total_seconds() / 3600

    def _count_back_to_back(self, events: list[dict]) -> int:
        """Count consecutive event pairs with < 15 min gap."""
        count = 0
        sorted_ev = sorted(
            events,
            key=lambda e: _parse_dt(e["start_time"]) or datetime.max,
        )
        for i in range(len(sorted_ev) - 1):
            e1_end   = _parse_dt(sorted_ev[i]["end_time"])
            e2_start = _parse_dt(sorted_ev[i + 1]["start_time"])
            if e1_end and e2_start:
                e1_end   = e1_end.replace(tzinfo=None)
                e2_start = e2_start.replace(tzinfo=None)
                gap = (e2_start - e1_end).total_seconds() / 60
                if 0 <= gap < 15:
                    count += 1
        return count

    def _compute_stress_score(self, events: list[dict]) -> int:
        """Numeric stress score 0-10+ from calendar density."""
        score = 0
        score += min(len(events), 5)                                # events count (0-5)
        score += sum(2 for e in events if e.get("importance", 1) >= 4)  # deadlines (+2 each)
        score += self._count_back_to_back(events)                   # back-to-back (+1 each)
        return score

    def _preferred_break_type(self) -> str:
        """Return historically most effective break type, defaulting to 'walk'."""
        try:
            history = self.memory.get_break_history(limit=20)
            if not history:
                return "walk"
            type_eff: dict[str, list[float]] = {}
            for h in history:
                btype = h.get("break_type", "walk")
                type_eff.setdefault(btype, []).append(h.get("effectiveness", 0.5))
            return max(type_eff, key=lambda t: sum(type_eff[t]) / len(type_eff[t]))
        except Exception:
            return "walk"


def _stress_recommendations(level: str, events: list[dict]) -> list[str]:
    base = {
        "LOW":     ["Ottima giornata! Approfitta per lavoro creativo."],
        "MEDIUM":  ["Prenditi pause di 10min ogni 2h.", "Idrata bene."],
        "HIGH":    ["Prioritizza i task. Delega se possibile.",
                    "Pausa pranzo obbligatoria.", "Esercizio fisico dopo il lavoro."],
        "EXTREME": ["ATTENZIONE: calendario sovraccarico.",
                    "Valuta di spostare/cancellare meeting non urgenti.",
                    "Pausa di 20min prima del prossimo impegno."],
    }
    recs = list(base.get(level, []))
    deadlines = [e for e in events if e.get("event_type") == "deadline"]
    if deadlines:
        recs.append(f"Deadline oggi: {', '.join(e['title'] for e in deadlines[:2])}.")
    return recs
