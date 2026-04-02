"""
jarvis_memory.py — JARVIS v4.0 Persistent Memory (SQLite + Fernet encryption)

Schema:
  conversations   — full chat log with mood/intent/context
  mood_baseline   — daily mood tracking
  preferences     — key/value user settings
  scheduled_actions — trigger-based automation rules
"""

import sqlite3
import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jarvis.memory")

try:
    from cryptography.fernet import Fernet
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    logger.warning("cryptography not installed — memory.db stored unencrypted")


class JarvisMemory:
    """Thread-safe SQLite memory manager with optional field-level encryption."""

    DB_PATH = Path("memory.db")
    KEY_PATH = Path("memory.key")

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or self.DB_PATH
        self._fernet = self._load_or_create_key() if ENCRYPTION_AVAILABLE else None
        self._init_schema()

    # ------------------------------------------------------------------ #
    # Encryption helpers                                                   #
    # ------------------------------------------------------------------ #

    def _load_or_create_key(self):
        if self.KEY_PATH.exists():
            key = self.KEY_PATH.read_bytes()
        else:
            key = Fernet.generate_key()
            self.KEY_PATH.write_bytes(key)
            self.KEY_PATH.chmod(0o600)
        return Fernet(key)

    def _encrypt(self, text: str) -> str:
        if self._fernet and text:
            return self._fernet.encrypt(text.encode()).decode()
        return text

    def _decrypt(self, text: str) -> str:
        if self._fernet and text:
            try:
                return self._fernet.decrypt(text.encode()).decode()
            except Exception:
                return text  # already plaintext (old row)
        return text

    # ------------------------------------------------------------------ #
    # Schema                                                               #
    # ------------------------------------------------------------------ #

    def _init_schema(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_input     TEXT,
                    jarvis_response TEXT,
                    mood_detected  TEXT,
                    intent         TEXT,
                    context        TEXT
                );

                CREATE TABLE IF NOT EXISTS mood_baseline (
                    date          DATE PRIMARY KEY,
                    morning_mood  TEXT,
                    evening_mood  TEXT,
                    stress_level  INTEGER,
                    sleep_hours   INTEGER,
                    notes         TEXT
                );

                CREATE TABLE IF NOT EXISTS preferences (
                    key   TEXT PRIMARY KEY,
                    value TEXT
                );

                CREATE TABLE IF NOT EXISTS scheduled_actions (
                    id      INTEGER PRIMARY KEY AUTOINCREMENT,
                    trigger TEXT,
                    action  TEXT,
                    enabled BOOLEAN DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS news_articles (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    source        TEXT,
                    title         TEXT,
                    content       TEXT,
                    url           TEXT UNIQUE,
                    published_at  DATETIME,
                    fetched_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                    category      TEXT,
                    countries     TEXT,
                    relevance_score REAL
                );

                CREATE TABLE IF NOT EXISTS tension_analysis (
                    id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                    date                   DATE,
                    tension_type           TEXT,
                    countries_involved     TEXT,
                    tension_score          REAL,
                    appeasement_score      REAL,
                    trend                  TEXT,
                    duration_estimate_days INTEGER,
                    impact_assessment      TEXT,
                    articles               TEXT,
                    created_at             DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS market_impact_predictions (
                    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
                    tension_event_id         INTEGER,
                    prediction_date          DATETIME DEFAULT CURRENT_TIMESTAMP,
                    affected_markets         TEXT,
                    impact_direction         TEXT,
                    confidence               REAL,
                    affected_sectors         TEXT,
                    volatility_expected      REAL,
                    estimated_timeline       TEXT,
                    predicted_indices_movement TEXT,
                    created_at               DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS social_impact_analysis (
                    id                           INTEGER PRIMARY KEY AUTOINCREMENT,
                    tension_event_id             INTEGER,
                    prediction_date              DATETIME DEFAULT CURRENT_TIMESTAMP,
                    affected_countries           TEXT,
                    employment_impact            TEXT,
                    inflation_impact             TEXT,
                    migration_risk               REAL,
                    humanitarian_risk            REAL,
                    supply_chain_disruption_risk REAL,
                    currency_stability           TEXT,
                    summary                      TEXT,
                    created_at                   DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS morning_briefings (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    date             DATE UNIQUE,
                    generated_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
                    briefing_text    TEXT,
                    key_tensions     TEXT,
                    market_impacts   TEXT,
                    social_impacts   TEXT,
                    actionable_items TEXT,
                    confidence       REAL
                );

                CREATE TABLE IF NOT EXISTS calendar_events (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id    TEXT UNIQUE,
                    title       TEXT,
                    description TEXT,
                    start_time  DATETIME,
                    end_time    DATETIME,
                    location    TEXT,
                    event_type  TEXT,
                    importance  INTEGER DEFAULT 3,
                    synced_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_all_day  BOOLEAN DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS schedule_patterns (
                    id           INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT,
                    start_time   TIME,
                    end_time     TIME,
                    days_of_week TEXT,
                    frequency    INTEGER,
                    confidence   REAL,
                    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS break_history (
                    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                    scheduled_time     DATETIME,
                    actual_break_time  DATETIME DEFAULT CURRENT_TIMESTAMP,
                    duration_minutes   INTEGER,
                    break_type         TEXT,
                    mood_before        REAL,
                    mood_after         REAL,
                    effectiveness      REAL,
                    created_at         DATETIME DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS event_reminders (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id      TEXT,
                    reminder_time DATETIME,
                    reminder_type TEXT,
                    message       TEXT,
                    notified      BOOLEAN DEFAULT 0,
                    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------------------------------------------------------ #
    # Conversations                                                        #
    # ------------------------------------------------------------------ #

    def save_conversation(
        self,
        user_input: str,
        jarvis_response: str,
        mood_detected: str = "neutral",
        intent: str = "unknown",
        context: Optional[dict] = None,
    ):
        ctx_json = json.dumps(context or {})
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO conversations
                   (user_input, jarvis_response, mood_detected, intent, context)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    self._encrypt(user_input),
                    self._encrypt(jarvis_response),
                    mood_detected,
                    intent,
                    ctx_json,
                ),
            )

    def get_recent_conversations(self, limit: int = 5) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM conversations ORDER BY timestamp DESC LIMIT ?", (limit,)
            ).fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"],
                "timestamp": row["timestamp"],
                "user_input": self._decrypt(row["user_input"]),
                "jarvis_response": self._decrypt(row["jarvis_response"]),
                "mood_detected": row["mood_detected"],
                "intent": row["intent"],
                "context": json.loads(row["context"] or "{}"),
            })
        return list(reversed(result))  # chronological order

    def build_context_summary(self, limit: int = 5) -> str:
        """Return a compact string of recent exchanges for Sonnet system prompt."""
        convs = self.get_recent_conversations(limit)
        if not convs:
            return "No previous conversations."
        lines = []
        for c in convs:
            ts = c["timestamp"][:16]
            lines.append(f"[{ts}] User: {c['user_input']}")
            lines.append(f"[{ts}] JARVIS: {c['jarvis_response']}")
        return "\n".join(lines)

    # ------------------------------------------------------------------ #
    # Mood baseline                                                        #
    # ------------------------------------------------------------------ #

    def update_mood(
        self,
        stress_level: int,
        mood: str,
        sleep_hours: int = 0,
        notes: str = "",
        period: str = "morning",  # "morning" | "evening"
    ):
        today = date.today().isoformat()
        col = "morning_mood" if period == "morning" else "evening_mood"
        with self._conn() as conn:
            conn.execute(
                f"""INSERT INTO mood_baseline (date, {col}, stress_level, sleep_hours, notes)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(date) DO UPDATE SET
                      {col} = excluded.{col},
                      stress_level = excluded.stress_level,
                      sleep_hours  = CASE WHEN excluded.sleep_hours > 0 THEN excluded.sleep_hours ELSE mood_baseline.sleep_hours END,
                      notes = excluded.notes
                """,
                (today, mood, stress_level, sleep_hours, notes),
            )

    def get_today_mood(self) -> Optional[dict]:
        today = date.today().isoformat()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM mood_baseline WHERE date = ?", (today,)
            ).fetchone()
        return dict(row) if row else None

    # ------------------------------------------------------------------ #
    # Preferences                                                          #
    # ------------------------------------------------------------------ #

    def set_preference(self, key: str, value):
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)",
                (key, json.dumps(value)),
            )

    def get_preference(self, key: str, default=None):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT value FROM preferences WHERE key = ?", (key,)
            ).fetchone()
        if row:
            return json.loads(row["value"])
        return default

    # ------------------------------------------------------------------ #
    # Scheduled actions                                                    #
    # ------------------------------------------------------------------ #

    def add_scheduled_action(self, trigger: str, action: str):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO scheduled_actions (trigger, action) VALUES (?, ?)",
                (trigger, action),
            )

    def get_active_scheduled_actions(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM scheduled_actions WHERE enabled = 1"
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------ #
    # News & Briefings                                                     #
    # ------------------------------------------------------------------ #

    def save_news_articles(self, articles: list[dict]):
        """Bulk-insert news articles (ignore duplicates by URL)."""
        with self._conn() as conn:
            for a in articles:
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO news_articles
                           (source, title, content, url, published_at, category, countries, relevance_score)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            a.get("source"), a.get("title"), a.get("content"),
                            a.get("url"), a.get("published_at"), a.get("category"),
                            json.dumps(a.get("countries", [])),
                            a.get("relevance_score", 0.0),
                        ),
                    )
                except Exception:
                    pass

    def save_morning_briefing(self, briefing: dict):
        """Upsert today's morning briefing."""
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO morning_briefings
                   (date, generated_at, briefing_text, key_tensions,
                    market_impacts, social_impacts, actionable_items, confidence)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    briefing.get("date"),
                    briefing.get("generated_at"),
                    briefing.get("briefing_text"),
                    json.dumps(briefing.get("key_tensions", [])),
                    json.dumps(briefing.get("market_impacts", [])),
                    json.dumps(briefing.get("social_impacts", [])),
                    briefing.get("actionable_items"),
                    briefing.get("confidence", 0.0),
                ),
            )

    def get_morning_briefing(self, date_str: str) -> Optional[dict]:
        """Return saved briefing for a given date (ISO format), or None."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM morning_briefings WHERE date = ?", (date_str,)
            ).fetchone()
        if not row:
            return None
        return {
            "date":            row["date"],
            "generated_at":    row["generated_at"],
            "briefing_text":   row["briefing_text"],
            "key_tensions":    json.loads(row["key_tensions"] or "[]"),
            "market_impacts":  json.loads(row["market_impacts"] or "[]"),
            "social_impacts":  json.loads(row["social_impacts"] or "[]"),
            "actionable_items": row["actionable_items"],
            "confidence":      row["confidence"],
        }

    def get_recent_news(self, limit: int = 20) -> list[dict]:
        """Return most recently fetched news articles."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM news_articles ORDER BY fetched_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        result = []
        for row in rows:
            result.append({
                "id": row["id"], "source": row["source"], "title": row["title"],
                "content": row["content"], "url": row["url"],
                "published_at": row["published_at"], "category": row["category"],
                "countries": json.loads(row["countries"] or "[]"),
                "relevance_score": row["relevance_score"],
            })
        return result

    # ------------------------------------------------------------------ #
    # Calendar                                                             #
    # ------------------------------------------------------------------ #

    def save_calendar_events(self, events: list[dict]):
        """Upsert calendar events by event_id."""
        with self._conn() as conn:
            for ev in events:
                conn.execute(
                    """INSERT OR REPLACE INTO calendar_events
                       (event_id, title, description, start_time, end_time,
                        location, event_type, importance, is_all_day)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        ev.get("event_id", ""), ev.get("title", ""),
                        ev.get("description", ""), ev.get("start_time", ""),
                        ev.get("end_time", ""),   ev.get("location", ""),
                        ev.get("event_type", "work"), ev.get("importance", 3),
                        1 if ev.get("is_all_day") else 0,
                    ),
                )

    def get_events_for_date(self, date_str: str) -> list[dict]:
        """Return all events that overlap with the given date (YYYY-MM-DD)."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT * FROM calendar_events
                   WHERE start_time LIKE ? OR start_time LIKE ?
                   ORDER BY start_time""",
                (f"{date_str}%", f"{date_str} %"),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_events_in_range(self, start: str, end: str) -> list[dict]:
        """Return events whose start_time falls in [start, end]."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT * FROM calendar_events
                   WHERE start_time >= ? AND start_time <= ?
                   ORDER BY start_time""",
                (start, end),
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_calendar_event(self, event_id: str):
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM calendar_events WHERE event_id = ?", (event_id,)
            )

    def save_break(
        self,
        break_type: str,
        duration_minutes: int,
        effectiveness: float = 0.5,
        mood_before: float = 0.5,
        mood_after: float = 0.5,
        scheduled_time: Optional[str] = None,
    ):
        now = datetime.now().isoformat()
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO break_history
                   (scheduled_time, actual_break_time, duration_minutes,
                    break_type, mood_before, mood_after, effectiveness)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (scheduled_time or now, now, duration_minutes,
                 break_type, mood_before, mood_after, effectiveness),
            )

    def get_break_history(self, limit: int = 20) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM break_history ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def save_event_reminder(
        self,
        event_id: str,
        reminder_time: str,
        message: str,
        reminder_type: str = "advance",
    ):
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO event_reminders
                   (event_id, reminder_time, reminder_type, message)
                   VALUES (?, ?, ?, ?)""",
                (event_id, reminder_time, reminder_type, message),
            )

    def get_pending_reminders(self, before: str) -> list[dict]:
        """Return unnotified reminders due before `before` (ISO datetime)."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT * FROM event_reminders
                   WHERE notified = 0 AND reminder_time <= ?
                   ORDER BY reminder_time""",
                (before,),
            ).fetchall()
        return [dict(r) for r in rows]

    def mark_reminder_notified(self, reminder_id: int):
        with self._conn() as conn:
            conn.execute(
                "UPDATE event_reminders SET notified = 1 WHERE id = ?",
                (reminder_id,),
            )

    # ------------------------------------------------------------------ #
    # Stats                                                                #
    # ------------------------------------------------------------------ #

    def stats(self) -> dict:
        with self._conn() as conn:
            n_convs = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            n_moods = conn.execute("SELECT COUNT(*) FROM mood_baseline").fetchone()[0]
        return {"conversations": n_convs, "mood_days_tracked": n_moods}
