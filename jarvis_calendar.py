"""
jarvis_calendar.py — Google Calendar integration for JARVIS v4.0.

Google Calendar API is optional:
  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2

If not installed, CalendarManager works in offline/manual mode using only
events stored in the local SQLite DB via JarvisMemory.
"""
import json
import logging
import threading
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.calendar")

_GOOGLE_AVAILABLE = False
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    _GOOGLE_AVAILABLE = True
except ImportError:
    logger.warning("[CALENDAR] google-api-python-client not installed — offline mode only")

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
TOKEN_PATH = Path("calendar_token.json")

# Event type classification keywords
_EVENT_TYPE_MAP = {
    "meeting":  ["standup", "riunione", "meeting", "call", "zoom", "teams", "interview"],
    "deadline": ["deadline", "scadenza", "consegna", "submission", "due"],
    "break":    ["pausa", "break", "lunch", "pranzo", "coffee", "caffè"],
    "work":     ["studio", "studio", "lavoro", "project", "progetto", "coding", "review"],
    "personal": ["palestra", "gym", "doctor", "medico", "famiglia", "birthday", "compleanno"],
}

_IMPORTANCE_MAP = {
    "deadline": 5,
    "meeting":  3,
    "work":     3,
    "break":    2,
    "personal": 2,
}


def _classify_event(title: str, description: str = "") -> tuple[str, int]:
    """Return (event_type, importance) from title/description."""
    text = f"{title} {description}".lower()
    for etype, keywords in _EVENT_TYPE_MAP.items():
        if any(kw in text for kw in keywords):
            return etype, _IMPORTANCE_MAP[etype]
    return "work", 3


def _parse_dt(dt_str: str) -> Optional[datetime]:
    """Parse ISO datetime string (with or without timezone)."""
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(dt_str[:19], fmt[:len(fmt)])
        except ValueError:
            pass
    return None


class CalendarManager:
    """
    Manages calendar events: Google Calendar sync + local SQLite cache.
    Falls back to manual/local-only mode when Google API unavailable.
    """

    def __init__(self, memory=None, credentials_path: str = "credentials.json"):
        if memory is None:
            from jarvis_memory import JarvisMemory
            memory = JarvisMemory()
        self.memory = memory
        self.credentials_path = Path(credentials_path)
        self._service = None
        self._sync_lock = threading.Lock()
        self.last_sync: Optional[datetime] = None
        self._google_enabled = _GOOGLE_AVAILABLE and self.credentials_path.exists()

    # ── Google Calendar Auth ──────────────────────────────────────────────────

    def authenticate_google_calendar(
        self, credentials_path: Optional[str] = None
    ) -> bool:
        """
        OAuth2 authentication with Google Calendar.
        On first run opens browser for user consent.
        Token saved to calendar_token.json for future use.

        Returns True if authentication succeeded.
        """
        if not _GOOGLE_AVAILABLE:
            logger.error("[CALENDAR] google-api-python-client not installed")
            return False

        creds_path = Path(credentials_path or self.credentials_path)
        if not creds_path.exists():
            logger.error("[CALENDAR] credentials.json not found at %s", creds_path)
            return False

        creds = None
        if TOKEN_PATH.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
            except Exception as e:
                logger.warning("[CALENDAR] Could not load token: %s", e)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("[CALENDAR] Token refreshed")
                except Exception as e:
                    logger.warning("[CALENDAR] Token refresh failed: %s", e)
                    creds = None

            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(creds_path), SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    TOKEN_PATH.write_text(creds.to_json())
                    logger.info("[CALENDAR] New credentials saved to %s", TOKEN_PATH)
                except Exception as e:
                    logger.error("[CALENDAR] OAuth2 flow failed: %s", e)
                    return False

        try:
            self._service = build("calendar", "v3", credentials=creds)
            self._google_enabled = True
            logger.info("[CALENDAR] Google Calendar authenticated")
            return True
        except Exception as e:
            logger.error("[CALENDAR] Failed to build service: %s", e)
            return False

    # ── Sync ─────────────────────────────────────────────────────────────────

    def sync_calendar(self, days_ahead: int = 30) -> int:
        """
        Fetch events from Google Calendar and store in SQLite.
        Returns number of events synced.
        Falls back gracefully if Google API unavailable.
        """
        if not self._google_enabled or self._service is None:
            logger.info("[CALENDAR] Offline mode — skipping Google sync")
            return 0

        with self._sync_lock:
            try:
                now = datetime.now(timezone.utc)
                time_max = (now + timedelta(days=days_ahead)).isoformat()

                result = self._service.events().list(
                    calendarId="primary",
                    timeMin=now.isoformat(),
                    timeMax=time_max,
                    maxResults=250,
                    singleEvents=True,
                    orderBy="startTime",
                ).execute()

                events = result.get("items", [])
                self._store_events(events)
                self.last_sync = datetime.now(timezone.utc)
                logger.info("[CALENDAR] Synced %d events", len(events))
                return len(events)

            except Exception as e:
                logger.error("[CALENDAR] Sync failed: %s", e)
                return 0

    def _store_events(self, raw_events: list[dict]):
        """Convert Google Calendar events and upsert into SQLite."""
        parsed = []
        for ev in raw_events:
            start = ev.get("start", {})
            end = ev.get("end", {})
            start_str = start.get("dateTime") or start.get("date", "")
            end_str = end.get("dateTime") or end.get("date", "")
            is_all_day = "date" in start and "dateTime" not in start
            title = ev.get("summary", "")
            description = ev.get("description", "")
            etype, importance = _classify_event(title, description)

            parsed.append({
                "event_id":    ev.get("id", ""),
                "title":       title,
                "description": description,
                "start_time":  start_str,
                "end_time":    end_str,
                "location":    ev.get("location", ""),
                "event_type":  etype,
                "importance":  importance,
                "is_all_day":  is_all_day,
            })

        self.memory.save_calendar_events(parsed)

    def add_event_manual(
        self,
        title: str,
        start_time: str,
        end_time: str,
        event_type: Optional[str] = None,
        importance: int = 3,
        description: str = "",
        location: str = "",
    ) -> str:
        """Add an event manually (no Google Calendar needed). Returns generated event_id."""
        import hashlib
        event_id = "manual_" + hashlib.md5(
            f"{title}{start_time}".encode()
        ).hexdigest()[:10]
        etype = event_type or _classify_event(title, description)[0]
        self.memory.save_calendar_events([{
            "event_id":    event_id,
            "title":       title,
            "description": description,
            "start_time":  start_time,
            "end_time":    end_time,
            "location":    location,
            "event_type":  etype,
            "importance":  importance,
            "is_all_day":  False,
        }])
        return event_id

    # ── Query ─────────────────────────────────────────────────────────────────

    def get_todays_schedule(self) -> list[dict]:
        """Return today's events ordered by start time."""
        return self.memory.get_events_for_date(date.today().isoformat())

    def get_upcoming_events(self, hours: int = 6) -> list[dict]:
        """Return events starting within the next N hours."""
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        events = self.memory.get_events_in_range(
            now.isoformat(), cutoff.isoformat()
        )
        return [e for e in events if _parse_dt(e["start_time"]) and
                _parse_dt(e["start_time"]) >= now]

    def get_free_slots(
        self,
        duration_minutes: int = 30,
        search_date: Optional[str] = None,
    ) -> list[dict]:
        """
        Find free time slots of at least `duration_minutes` in the given date.
        Returns list of {"start": "HH:MM", "end": "HH:MM", "duration_minutes": N}.
        """
        target = date.fromisoformat(search_date) if search_date else date.today()
        events = self.memory.get_events_for_date(target.isoformat())
        return _compute_free_slots(events, target, duration_minutes)

    def is_busy_now(self) -> tuple[bool, str, int]:
        """
        Returns (is_busy, event_name, minutes_until_free).
        minutes_until_free = 0 if not busy.
        """
        now = datetime.now()
        events = self.get_todays_schedule()
        for ev in events:
            start = _parse_dt(ev["start_time"])
            end   = _parse_dt(ev["end_time"])
            if start and end and start <= now <= end:
                mins_free = max(0, int((end - now).total_seconds() / 60))
                return True, ev["title"], mins_free
        return False, "", 0

    def get_next_event(self) -> Optional[dict]:
        """Return the next upcoming event (after now)."""
        now = datetime.now()
        events = sorted(
            self.get_todays_schedule(),
            key=lambda e: _parse_dt(e["start_time"]) or datetime.max,
        )
        for ev in events:
            start = _parse_dt(ev["start_time"])
            if start and start > now:
                mins_until = int((start - now).total_seconds() / 60)
                return {**ev, "minutes_until": mins_until}
        return None

    def get_schedule_context(self) -> dict:
        """
        Rich context dict for Sonnet system prompt.
        """
        events = self.get_todays_schedule()
        free_slots = self.get_free_slots(duration_minutes=30)
        busy, busy_event, busy_until = self.is_busy_now()
        next_ev = self.get_next_event()

        # Find busiest hours span
        busiest = _busiest_hours_span(events)

        # Urgency: any high-importance event in next 3h?
        now = datetime.now()
        urgency = "low"
        next_important = None
        for ev in events:
            start = _parse_dt(ev["start_time"])
            if start and start > now:
                mins = (start - now).total_seconds() / 60
                if ev.get("importance", 1) >= 4 and mins <= 180:
                    urgency = "high"
                    next_important = f"{ev['title']} tra {int(mins)} minuti"
                    break
                elif ev.get("importance", 1) >= 3 and mins <= 60:
                    urgency = "moderate"

        return {
            "schedule":        events,
            "event_count":     len(events),
            "is_busy_now":     busy,
            "current_event":   busy_event,
            "busiest_hours":   busiest,
            "free_slots":      free_slots,
            "urgency":         urgency,
            "next_important":  next_important,
            "next_event":      next_ev,
        }

    def format_todays_schedule(self) -> str:
        """Human-readable Italian schedule string."""
        events = self.get_todays_schedule()
        if not events:
            return "Nessun evento programmato per oggi."
        lines = [f"📅 Oggi hai {len(events)} eventi:"]
        for ev in events:
            start = _parse_dt(ev["start_time"])
            end   = _parse_dt(ev["end_time"])
            s = start.strftime("%H:%M") if start else "?"
            e = end.strftime("%H:%M")   if end   else "?"
            imp = "⭐" * max(1, ev.get("importance", 1) - 2)
            lines.append(f"  • {s}-{e}  {ev['title']} {imp}")
        return "\n".join(lines)


# ── Free-slot computation ─────────────────────────────────────────────────────

def _compute_free_slots(
    events: list[dict],
    target: date,
    min_duration_minutes: int,
) -> list[dict]:
    """Compute free time blocks between events on a given date."""
    # Work window: 08:00 – 22:00
    day_start = datetime(target.year, target.month, target.day, 8, 0)
    day_end   = datetime(target.year, target.month, target.day, 22, 0)

    # Build sorted list of (start, end) busy intervals
    busy: list[tuple[datetime, datetime]] = []
    for ev in events:
        s = _parse_dt(ev["start_time"])
        e = _parse_dt(ev["end_time"])
        if s and e and not ev.get("is_all_day"):
            # Strip timezone for naive comparison
            s = s.replace(tzinfo=None)
            e = e.replace(tzinfo=None)
            if s.date() == target or e.date() == target:
                busy.append((s, e))

    busy.sort()

    # Merge overlapping intervals
    merged: list[tuple[datetime, datetime]] = []
    for s, e in busy:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    # Find gaps
    free_slots = []
    cursor = day_start
    for s, e in merged:
        if s > cursor:
            gap_min = int((s - cursor).total_seconds() / 60)
            if gap_min >= min_duration_minutes:
                free_slots.append({
                    "start": cursor.strftime("%H:%M"),
                    "end":   s.strftime("%H:%M"),
                    "duration_minutes": gap_min,
                    "date": target.isoformat(),
                })
        cursor = max(cursor, e)

    if cursor < day_end:
        gap_min = int((day_end - cursor).total_seconds() / 60)
        if gap_min >= min_duration_minutes:
            free_slots.append({
                "start": cursor.strftime("%H:%M"),
                "end":   day_end.strftime("%H:%M"),
                "duration_minutes": gap_min,
                "date": target.isoformat(),
            })

    return free_slots


def _busiest_hours_span(events: list[dict]) -> str:
    """Return human-readable description of the busiest part of the day."""
    if not events:
        return "nessun evento"
    hours = []
    for ev in events:
        s = _parse_dt(ev["start_time"])
        if s:
            hours.append(s.hour)
    if not hours:
        return "orari non determinabili"
    min_h = min(hours)
    max_h = max(hours) + 1
    return f"{min_h:02d}:00-{max_h:02d}:00"
