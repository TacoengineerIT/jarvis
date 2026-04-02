"""
tests/test_calendar.py — Phase 3: Calendar integration + schedule optimizer.
All Google API calls fully mocked. No real network access.
"""
import json
import pytest
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile

# ── Shared helpers ────────────────────────────────────────────────────────────

def _memory(tmp_path=None):
    from jarvis_memory import JarvisMemory
    p = Path(tmp_path) / "test.db" if tmp_path else Path(tempfile.mktemp(suffix=".db"))
    return JarvisMemory(db_path=p)


def _today_str():
    return date.today().isoformat()


def _make_event(
    title="Test Meeting",
    start_offset_h=2,
    end_offset_h=3,
    event_type="meeting",
    importance=3,
    event_id=None,
):
    base = datetime.now().replace(minute=0, second=0, microsecond=0)
    start = (base + timedelta(hours=start_offset_h)).strftime("%Y-%m-%dT%H:%M:%S")
    end   = (base + timedelta(hours=end_offset_h)).strftime("%Y-%m-%dT%H:%M:%S")
    return {
        "event_id":    event_id or f"ev_{title.replace(' ','_')}",
        "title":       title,
        "description": "",
        "start_time":  start,
        "end_time":    end,
        "location":    "",
        "event_type":  event_type,
        "importance":  importance,
        "is_all_day":  False,
    }


def _make_today_events(mem):
    """Insert 3 events spread across today."""
    today = _today_str()
    events = [
        {**_make_event("Standup",    start_offset_h=0, end_offset_h=0), "start_time": f"{today}T09:00:00", "end_time": f"{today}T09:30:00"},
        {**_make_event("Lunch",      start_offset_h=0, end_offset_h=0), "start_time": f"{today}T12:00:00", "end_time": f"{today}T13:00:00"},
        {**_make_event("Deadline",   start_offset_h=0, end_offset_h=0), "start_time": f"{today}T16:00:00", "end_time": f"{today}T17:00:00",
         "event_type": "deadline", "importance": 5},
    ]
    mem.save_calendar_events(events)
    return events


# ═══════════════════════════════════════════════════════════════════
# 1. JarvisMemory calendar tables
# ═══════════════════════════════════════════════════════════════════

class TestMemoryCalendarTables:
    def test_save_and_get_events_for_date(self, tmp_path):
        mem = _memory(tmp_path)
        _make_today_events(mem)
        events = mem.get_events_for_date(_today_str())
        assert len(events) == 3

    def test_save_events_upserts_by_event_id(self, tmp_path):
        mem = _memory(tmp_path)
        ev = _make_event("Meeting")
        ev["event_id"] = "unique_001"
        mem.save_calendar_events([ev])
        ev["title"] = "Updated Meeting"
        mem.save_calendar_events([ev])
        events = mem.get_events_for_date(_today_str())
        titles = [e["title"] for e in events]
        assert titles.count("Updated Meeting") == 1
        assert "Meeting" not in titles

    def test_get_events_in_range(self, tmp_path):
        mem = _memory(tmp_path)
        _make_today_events(mem)
        today = _today_str()
        results = mem.get_events_in_range(f"{today}T08:00:00", f"{today}T10:00:00")
        assert any("Standup" in e["title"] for e in results)

    def test_save_and_get_break_history(self, tmp_path):
        mem = _memory(tmp_path)
        mem.save_break("walk", 20, effectiveness=0.8, mood_before=0.4, mood_after=0.7)
        history = mem.get_break_history(limit=5)
        assert len(history) == 1
        assert history[0]["break_type"] == "walk"
        assert history[0]["duration_minutes"] == 20

    def test_break_history_limit(self, tmp_path):
        mem = _memory(tmp_path)
        for i in range(5):
            mem.save_break("coffee", 10)
        assert len(mem.get_break_history(limit=3)) == 3

    def test_save_and_get_reminder(self, tmp_path):
        mem = _memory(tmp_path)
        mem.save_event_reminder("ev_001", "2026-04-02T08:50:00", "Standup in 10min")
        pending = mem.get_pending_reminders("2026-04-02T09:00:00")
        assert len(pending) == 1
        assert "Standup" in pending[0]["message"]

    def test_mark_reminder_notified(self, tmp_path):
        mem = _memory(tmp_path)
        mem.save_event_reminder("ev_002", "2026-04-02T08:50:00", "Test reminder")
        pending = mem.get_pending_reminders("2026-04-02T09:00:00")
        mem.mark_reminder_notified(pending[0]["id"])
        assert mem.get_pending_reminders("2026-04-02T09:00:00") == []

    def test_delete_calendar_event(self, tmp_path):
        mem = _memory(tmp_path)
        ev = _make_event("ToDelete")
        ev["event_id"] = "del_001"
        mem.save_calendar_events([ev])
        mem.delete_calendar_event("del_001")
        events = mem.get_events_for_date(_today_str())
        assert all(e["event_id"] != "del_001" for e in events)


# ═══════════════════════════════════════════════════════════════════
# 2. CalendarManager
# ═══════════════════════════════════════════════════════════════════

class TestCalendarManagerOfflineMode:
    def _cal(self, tmp_path):
        from jarvis_calendar import CalendarManager
        return CalendarManager(memory=_memory(tmp_path))

    def test_sync_skipped_without_google(self, tmp_path):
        cal = self._cal(tmp_path)
        count = cal.sync_calendar()
        assert count == 0  # offline mode

    def test_add_event_manual(self, tmp_path):
        cal = self._cal(tmp_path)
        eid = cal.add_event_manual(
            "My Study Session",
            f"{_today_str()}T14:00:00",
            f"{_today_str()}T16:00:00",
        )
        assert eid.startswith("manual_")
        events = cal.get_todays_schedule()
        assert any(e["title"] == "My Study Session" for e in events)

    def test_get_todays_schedule_returns_todays_events(self, tmp_path):
        cal = self._cal(tmp_path)
        _make_today_events(cal.memory)
        events = cal.get_todays_schedule()
        assert len(events) == 3

    def test_get_todays_schedule_empty(self, tmp_path):
        cal = self._cal(tmp_path)
        assert cal.get_todays_schedule() == []

    def test_get_upcoming_events(self, tmp_path):
        cal = self._cal(tmp_path)
        today = _today_str()
        now = datetime.now()
        future_start = (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
        future_end   = (now + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")
        past_start = (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")
        past_end   = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
        cal.memory.save_calendar_events([
            {**_make_event("Future"), "start_time": future_start, "end_time": future_end},
            {**_make_event("Past"),   "start_time": past_start,   "end_time": past_end,
             "event_id": "past_ev"},
        ])
        upcoming = cal.get_upcoming_events(hours=3)
        titles = [e["title"] for e in upcoming]
        assert "Future" in titles
        assert "Past" not in titles

    def test_is_busy_now_false_when_no_events(self, tmp_path):
        cal = self._cal(tmp_path)
        busy, name, mins = cal.is_busy_now()
        assert busy is False
        assert name == ""
        assert mins == 0

    def test_is_busy_now_true_during_event(self, tmp_path):
        cal = self._cal(tmp_path)
        now = datetime.now()
        start = (now - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S")
        end   = (now + timedelta(minutes=20)).strftime("%Y-%m-%dT%H:%M:%S")
        cal.memory.save_calendar_events([{
            **_make_event("Active Meeting"), "start_time": start, "end_time": end
        }])
        busy, name, mins = cal.is_busy_now()
        assert busy is True
        assert "Active" in name or "Meeting" in name
        assert mins > 0

    def test_get_next_event(self, tmp_path):
        cal = self._cal(tmp_path)
        now = datetime.now()
        future = (now + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")
        future_end = (now + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%S")
        cal.memory.save_calendar_events([{
            **_make_event("Next Up"), "start_time": future, "end_time": future_end
        }])
        nxt = cal.get_next_event()
        assert nxt is not None
        assert nxt["title"] == "Next Up"
        assert nxt["minutes_until"] > 100

    def test_get_next_event_none_when_empty(self, tmp_path):
        cal = self._cal(tmp_path)
        assert cal.get_next_event() is None

    def test_get_free_slots_finds_gaps(self, tmp_path):
        cal = self._cal(tmp_path)
        today = _today_str()
        # Block 10:00-12:00 and 14:00-15:00
        cal.memory.save_calendar_events([
            {**_make_event("Morning Block"), "start_time": f"{today}T10:00:00",
             "end_time": f"{today}T12:00:00"},
            {**_make_event("Afternoon"), "start_time": f"{today}T14:00:00",
             "end_time": f"{today}T15:00:00", "event_id": "ev_afternoon"},
        ])
        slots = cal.get_free_slots(duration_minutes=30)
        # Gap before 10:00 (08:00-10:00), between 12:00-14:00, after 15:00
        assert len(slots) >= 1
        for slot in slots:
            assert slot["duration_minutes"] >= 30

    def test_get_free_slots_empty_day_is_free(self, tmp_path):
        cal = self._cal(tmp_path)
        slots = cal.get_free_slots(duration_minutes=30)
        # Full day is free (08:00-22:00 = 840 min)
        assert len(slots) >= 1
        assert slots[0]["duration_minutes"] >= 60

    def test_get_schedule_context_keys(self, tmp_path):
        cal = self._cal(tmp_path)
        _make_today_events(cal.memory)
        ctx = cal.get_schedule_context()
        for key in ("schedule", "event_count", "is_busy_now",
                    "free_slots", "urgency", "busiest_hours"):
            assert key in ctx

    def test_format_todays_schedule_string(self, tmp_path):
        cal = self._cal(tmp_path)
        _make_today_events(cal.memory)
        text = cal.format_todays_schedule()
        assert "Standup" in text or "oggi" in text.lower()

    def test_format_empty_schedule(self, tmp_path):
        cal = self._cal(tmp_path)
        text = cal.format_todays_schedule()
        assert "Nessun" in text


class TestCalendarManagerGoogleMocked:
    """Tests that exercise the Google API path via mocks."""

    def test_sync_stores_events(self, tmp_path):
        from jarvis_calendar import CalendarManager
        mem = _memory(tmp_path)
        cal = CalendarManager(memory=mem)

        today = _today_str()
        mock_items = [
            {
                "id": "goog_001",
                "summary": "Sprint Standup",
                "description": "",
                "start": {"dateTime": f"{today}T09:00:00+00:00"},
                "end":   {"dateTime": f"{today}T09:30:00+00:00"},
                "location": "",
            }
        ]
        mock_service = MagicMock()
        mock_service.events.return_value.list.return_value.execute.return_value = {
            "items": mock_items
        }
        cal._service = mock_service
        cal._google_enabled = True

        count = cal.sync_calendar()
        assert count == 1
        events = mem.get_events_for_date(today)
        assert any("Standup" in e["title"] for e in events)

    def test_sync_handles_api_error(self, tmp_path):
        from jarvis_calendar import CalendarManager
        mem = _memory(tmp_path)
        cal = CalendarManager(memory=mem)
        mock_service = MagicMock()
        mock_service.events.return_value.list.return_value.execute.side_effect = Exception("API Error")
        cal._service = mock_service
        cal._google_enabled = True

        count = cal.sync_calendar()
        assert count == 0  # Should not raise

    def test_authenticate_returns_false_without_credentials(self, tmp_path):
        from jarvis_calendar import CalendarManager
        cal = CalendarManager(memory=_memory(tmp_path), credentials_path="nonexistent.json")
        result = cal.authenticate_google_calendar("nonexistent.json")
        assert result is False


# ═══════════════════════════════════════════════════════════════════
# 3. ScheduleOptimizer
# ═══════════════════════════════════════════════════════════════════

class TestScheduleOptimizer:
    def _opt(self, tmp_path, events=None):
        from jarvis_calendar import CalendarManager
        from jarvis_schedule_optimizer import ScheduleOptimizer
        mem = _memory(tmp_path)
        if events:
            mem.save_calendar_events(events)
        cal = CalendarManager(memory=mem)
        return ScheduleOptimizer(calendar_manager=cal, memory=mem), mem

    def test_recommend_break_returns_required_keys(self, tmp_path):
        opt, _ = self._opt(tmp_path)
        result = opt.recommend_break()
        for key in ("should_break", "recommendation", "break_type",
                    "duration_minutes", "best_time", "benefits", "reason"):
            assert key in result

    def test_recommend_break_when_free(self, tmp_path):
        opt, _ = self._opt(tmp_path)  # No events = all free
        result = opt.recommend_break()
        assert isinstance(result["recommendation"], str)
        assert len(result["recommendation"]) > 0

    def test_recommend_break_not_during_active_event(self, tmp_path):
        now = datetime.now()
        active_start = (now - timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%S")
        active_end   = (now + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%S")
        ev = {**_make_event("Active"), "start_time": active_start, "end_time": active_end}
        opt, _ = self._opt(tmp_path, events=[ev])
        result = opt.recommend_break()
        assert result["should_break"] is False

    def test_suggest_work_time_returns_keys(self, tmp_path):
        opt, _ = self._opt(tmp_path)
        result = opt.suggest_work_time()
        for key in ("current_quality", "suggestion", "hour",
                    "total_free_today", "event_count_today"):
            assert key in result

    def test_suggest_work_time_quality_is_string(self, tmp_path):
        opt, _ = self._opt(tmp_path)
        result = opt.suggest_work_time()
        assert isinstance(result["current_quality"], str)
        assert len(result["current_quality"]) > 0

    def test_predict_stress_low_with_no_events(self, tmp_path):
        opt, _ = self._opt(tmp_path)
        result = opt.predict_stress_level()
        assert result["level"] == "LOW"
        assert result["score"] == 0

    def test_predict_stress_high_with_many_events(self, tmp_path):
        today = _today_str()
        events = [
            {**_make_event(f"Meeting{i}"), "start_time": f"{today}T{9+i:02d}:00:00",
             "end_time": f"{today}T{9+i:02d}:50:00", "event_id": f"ev_{i}"}
            for i in range(7)
        ] + [
            {**_make_event("Deadline", importance=5, event_type="deadline"),
             "start_time": f"{today}T16:00:00", "end_time": f"{today}T17:00:00",
             "event_id": "deadline_ev"}
        ]
        opt, _ = self._opt(tmp_path, events=events)
        result = opt.predict_stress_level()
        assert result["level"] in ("HIGH", "EXTREME", "MEDIUM")
        assert result["score"] >= 3

    def test_predict_stress_has_recommendations(self, tmp_path):
        opt, _ = self._opt(tmp_path)
        result = opt.predict_stress_level()
        assert isinstance(result["recommendations"], list)

    def test_predict_stress_required_keys(self, tmp_path):
        opt, _ = self._opt(tmp_path)
        result = opt.predict_stress_level()
        for key in ("level", "score", "event_count",
                    "high_importance", "back_to_back", "recommendations"):
            assert key in result

    def test_optimize_break_no_history(self, tmp_path):
        opt, _ = self._opt(tmp_path)
        result = opt.optimize_break_timing()
        assert "best_break_type" in result
        assert "recommendation" in result
        assert result["avg_effectiveness"] is None

    def test_optimize_break_with_history(self, tmp_path):
        opt, mem = self._opt(tmp_path)
        for _ in range(5):
            mem.save_break("walk", 20, effectiveness=0.9)
        for _ in range(2):
            mem.save_break("coffee", 10, effectiveness=0.3)
        result = opt.optimize_break_timing()
        assert result["best_break_type"] == "walk"
        assert result["avg_effectiveness"] is not None
        assert 0 < result["avg_effectiveness"] <= 1.0

    def test_log_break_saves_to_memory(self, tmp_path):
        opt, mem = self._opt(tmp_path)
        opt.log_break("nap", 20, effectiveness=0.7, mood_before=0.3, mood_after=0.6)
        history = mem.get_break_history()
        assert len(history) == 1
        assert history[0]["break_type"] == "nap"

    def test_count_back_to_back(self, tmp_path):
        today = _today_str()
        events = [
            {**_make_event("M1"), "start_time": f"{today}T09:00:00", "end_time": f"{today}T10:00:00"},
            {**_make_event("M2"), "start_time": f"{today}T10:05:00", "end_time": f"{today}T11:00:00", "event_id": "ev_m2"},
            {**_make_event("M3"), "start_time": f"{today}T13:00:00", "end_time": f"{today}T14:00:00", "event_id": "ev_m3"},
        ]
        opt, _ = self._opt(tmp_path, events=events)
        count = opt._count_back_to_back(opt.calendar.get_todays_schedule())
        assert count == 1  # Only M1→M2 are back-to-back (5min gap)

    def test_deadline_increases_stress(self, tmp_path):
        today = _today_str()
        opt_no_dl, _ = self._opt(tmp_path)

        (tmp_path / "m2").mkdir()
        mem2 = _memory(tmp_path / "m2")
        from jarvis_calendar import CalendarManager
        from jarvis_schedule_optimizer import ScheduleOptimizer
        mem2.save_calendar_events([{
            **_make_event("Deadline", importance=5, event_type="deadline"),
            "start_time": f"{today}T16:00:00", "end_time": f"{today}T17:00:00",
        }])
        cal2 = CalendarManager(memory=mem2)
        opt_dl = ScheduleOptimizer(calendar_manager=cal2, memory=mem2)

        score_no_dl = opt_no_dl.predict_stress_level()["score"]
        score_dl    = opt_dl.predict_stress_level()["score"]
        assert score_dl > score_no_dl


# ═══════════════════════════════════════════════════════════════════
# 4. Event classification helpers
# ═══════════════════════════════════════════════════════════════════

class TestEventClassification:
    def test_classify_meeting(self):
        from jarvis_calendar import _classify_event
        etype, importance = _classify_event("Team standup meeting")
        assert etype == "meeting"

    def test_classify_deadline(self):
        from jarvis_calendar import _classify_event
        etype, importance = _classify_event("Project deadline submission")
        assert etype == "deadline"
        assert importance == 5

    def test_classify_break(self):
        from jarvis_calendar import _classify_event
        etype, importance = _classify_event("Lunch break")
        assert etype == "break"

    def test_classify_personal(self):
        from jarvis_calendar import _classify_event
        etype, importance = _classify_event("Palestra / gym workout")
        assert etype == "personal"

    def test_classify_default_work(self):
        from jarvis_calendar import _classify_event
        etype, importance = _classify_event("Random unclassified event")
        assert etype == "work"


# ═══════════════════════════════════════════════════════════════════
# 5. Free slot computation
# ═══════════════════════════════════════════════════════════════════

class TestFreeSlotComputation:
    def test_empty_day_returns_full_slot(self):
        from jarvis_calendar import _compute_free_slots
        today = date.today()
        slots = _compute_free_slots([], today, 30)
        assert len(slots) >= 1
        total = sum(s["duration_minutes"] for s in slots)
        assert total >= 840  # 08:00-22:00 = 14h = 840 min

    def test_blocked_day_no_slots(self):
        from jarvis_calendar import _compute_free_slots
        today = date.today()
        today_str = today.isoformat()
        events = [{
            "start_time": f"{today_str}T08:00:00",
            "end_time":   f"{today_str}T22:00:00",
            "is_all_day": False,
        }]
        slots = _compute_free_slots(events, today, 30)
        assert slots == []

    def test_gap_between_events(self):
        from jarvis_calendar import _compute_free_slots
        today = date.today()
        today_str = today.isoformat()
        events = [
            {"start_time": f"{today_str}T10:00:00", "end_time": f"{today_str}T11:00:00", "is_all_day": False},
            {"start_time": f"{today_str}T14:00:00", "end_time": f"{today_str}T15:00:00", "is_all_day": False},
        ]
        slots = _compute_free_slots(events, today, 30)
        starts = [s["start"] for s in slots]
        # Gap 11:00-14:00 should be free
        assert any(s == "11:00" for s in starts)

    def test_min_duration_filter(self):
        from jarvis_calendar import _compute_free_slots
        today = date.today()
        today_str = today.isoformat()
        # Leave only a 10-minute gap
        events = [
            {"start_time": f"{today_str}T09:00:00", "end_time": f"{today_str}T09:50:00", "is_all_day": False},
            {"start_time": f"{today_str}T10:00:00", "end_time": f"{today_str}T22:00:00", "is_all_day": False},
        ]
        slots = _compute_free_slots(events, today, 30)
        # The 10-minute gap (09:50-10:00) should not appear
        for s in slots:
            assert s["duration_minutes"] >= 30
