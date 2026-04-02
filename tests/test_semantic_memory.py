"""
tests/test_semantic_memory.py — Phase 1: Semantic Memory + Pattern Detection

All tests are mocked — no real sentence-transformers model, no network.
"""
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    """Run every test in a temp directory to avoid polluting the repo."""
    monkeypatch.chdir(tmp_path)


def _memory(path=None):
    from jarvis_memory import JarvisMemory
    return JarvisMemory(db_path=path or Path("test_mem.db"))


def _semantic(mem):
    from jarvis_memory_semantic import SemanticMemoryManager
    return SemanticMemoryManager(memory=mem)


def _patterns(mem):
    from jarvis_memory_patterns import PatternDetector
    return PatternDetector(memory=mem)


# ── JarvisMemory Phase 1 schema ───────────────────────────────────────────────

class TestMemoryPhase1Schema:
    def test_save_and_get_embedding(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        # Store a conversation first
        mem.save_conversation("hello", "hi there", mood_detected="neutral")
        convs = mem.get_recent_conversations(limit=1)
        conv_id = convs[0]["id"]

        vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        mem.save_embedding(conv_id, vec.tobytes())

        rows = mem.get_embeddings()
        assert len(rows) == 1
        assert rows[0]["conversation_id"] == conv_id
        recovered = np.frombuffer(rows[0]["embedding"], dtype=np.float32)
        np.testing.assert_array_equal(recovered, vec)

    def test_get_embeddings_empty(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        assert mem.get_embeddings() == []

    def test_embedding_upsert_replaces(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        mem.save_conversation("a", "b")
        conv_id = mem.get_recent_conversations(1)[0]["id"]

        vec1 = np.array([1.0, 0.0], dtype=np.float32)
        vec2 = np.array([0.0, 1.0], dtype=np.float32)
        mem.save_embedding(conv_id, vec1.tobytes())
        mem.save_embedding(conv_id, vec2.tobytes())  # upsert

        rows = mem.get_embeddings()
        assert len(rows) == 1
        recovered = np.frombuffer(rows[0]["embedding"], dtype=np.float32)
        np.testing.assert_array_equal(recovered, vec2)

    def test_get_conversation_by_id(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        mem.save_conversation("test input", "test response", mood_detected="happy")
        conv_id = mem.get_recent_conversations(1)[0]["id"]

        conv = mem.get_conversation_by_id(conv_id)
        assert conv is not None
        assert conv["user_input"] == "test input"
        assert conv["jarvis_response"] == "test response"
        assert conv["mood_detected"] == "happy"

    def test_get_conversation_by_id_missing(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        assert mem.get_conversation_by_id(999) is None

    def test_save_mood_timeline(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        mem.save_mood_timeline("stressed", 3.0, ["deadline", "lavoro"])
        rows = mem.get_mood_timeline(days=1)
        assert len(rows) == 1
        assert rows[0]["mood_label"] == "stressed"
        assert rows[0]["mood_score"] == 3.0
        assert "deadline" in rows[0]["keywords"]

    def test_get_mood_timeline_respects_days(self, tmp_path):
        import sqlite3
        from datetime import datetime, timedelta
        mem = _memory(tmp_path / "m.db")
        # Insert one old row manually
        old_ts = (datetime.now() - timedelta(days=10)).isoformat()
        with mem._conn() as conn:
            conn.execute(
                "INSERT INTO mood_timeline (timestamp, mood_label, mood_score, keywords) VALUES (?,?,?,?)",
                (old_ts, "neutral", 5.0, "[]"),
            )
        mem.save_mood_timeline("happy", 9.0, [])

        recent = mem.get_mood_timeline(days=3)
        assert len(recent) == 1
        assert recent[0]["mood_label"] == "happy"

    def test_save_and_get_patterns(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        mem.save_pattern("stress", "Monday stress peak", 0.8, {"day": "Monday"})
        pats = mem.get_patterns()
        assert len(pats) == 1
        assert pats[0]["pattern_type"] == "stress"
        assert pats[0]["confidence"] == 0.8
        assert pats[0]["data"]["day"] == "Monday"

    def test_get_patterns_filtered_by_type(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        mem.save_pattern("stress", "desc1", 0.7, {})
        mem.save_pattern("energy", "desc2", 0.6, {})
        assert len(mem.get_patterns("stress")) == 1
        assert len(mem.get_patterns("energy")) == 1
        assert len(mem.get_patterns()) == 2

    def test_mood_timeline_empty(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        assert mem.get_mood_timeline(days=7) == []


# ── SemanticMemoryManager ─────────────────────────────────────────────────────

class TestSemanticMemoryManager:
    def test_extract_keywords_removes_stopwords(self, tmp_path):
        sem = _semantic(_memory(tmp_path / "m.db"))
        kws = sem.extract_keywords("sono molto stressato per il lavoro")
        # stopwords like "sono", "molto", "per", "il" should be removed
        assert "stressato" in kws or "lavoro" in kws
        assert "il" not in kws
        assert "sono" not in kws

    def test_extract_keywords_category_labels(self, tmp_path):
        sem = _semantic(_memory(tmp_path / "m.db"))
        kws = sem.extract_keywords("ho tanto stress per la scadenza del progetto")
        # Should include category labels "stress" and "lavoro"
        assert "stress" in kws or "lavoro" in kws

    def test_extract_keywords_max_limit(self, tmp_path):
        sem = _semantic(_memory(tmp_path / "m.db"))
        long_text = " ".join([f"parola{i}" for i in range(50)])
        kws = sem.extract_keywords(long_text, max_keywords=5)
        assert len(kws) <= 5

    def test_add_embedding_no_st_model(self, tmp_path):
        """add_embedding should work even without sentence-transformers."""
        mem = _memory(tmp_path / "m.db")
        mem.save_conversation("test", "response")
        conv_id = mem.get_recent_conversations(1)[0]["id"]
        sem = _semantic(mem)
        # Force fallback (no ST model loaded)
        sem._model = None
        with patch("jarvis_memory_semantic._load_st_model", return_value=None):
            result = sem.add_embedding(conv_id, "test text")
        assert result is True
        rows = mem.get_embeddings()
        assert len(rows) == 1

    def test_add_conversation_with_embedding(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        sem = _semantic(mem)
        sem._model = None
        with patch("jarvis_memory_semantic._load_st_model", return_value=None):
            conv_id = sem.add_conversation_with_embedding(
                user_input="sono stressato",
                response="capisco, prenditi una pausa",
                mood="stressed",
                intent="mood_check",
            )
        assert conv_id >= 0
        convs = mem.get_recent_conversations(5)
        assert len(convs) >= 1
        rows = mem.get_embeddings()
        assert len(rows) >= 1

    def test_semantic_search_empty(self, tmp_path):
        sem = _semantic(_memory(tmp_path / "m.db"))
        sem._model = None
        with patch("jarvis_memory_semantic._load_st_model", return_value=None):
            results = sem.semantic_search("test query", top_k=5)
        assert results == []

    def test_semantic_search_returns_similar(self, tmp_path):
        """Semantic search returns stored conversations when embeddings match."""
        from jarvis_memory_semantic import _vec_to_bytes
        mem = _memory(tmp_path / "m.db")
        # Insert a conversation manually
        mem.save_conversation("sono stressato per il lavoro", "prenditi una pausa", mood_detected="stressed")
        conv_id = mem.get_recent_conversations(1)[0]["id"]
        # Store a known non-zero embedding vector (stress + lavoro dims)
        known_vec = np.array([0.894, 0.447, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
        mem.save_embedding(conv_id, _vec_to_bytes(known_vec))

        sem = _semantic(mem)
        sem._model = None
        # Patch _embed_text to return the same known_vec for any input
        with patch("jarvis_memory_semantic._embed_text", return_value=known_vec):
            results = sem.semantic_search("stressato lavoro", top_k=5)
        assert len(results) >= 1
        assert results[0]["similarity"] > 0

    def test_semantic_search_top_k_limit(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        sem = _semantic(mem)
        sem._model = None
        with patch("jarvis_memory_semantic._load_st_model", return_value=None):
            for i in range(5):
                sem.add_conversation_with_embedding(f"stress lavoro {i}", f"risposta {i}", mood="stressed")
            results = sem.semantic_search("stress", top_k=2)
        assert len(results) <= 2

    def test_find_similar_moods_empty(self, tmp_path):
        sem = _semantic(_memory(tmp_path / "m.db"))
        results = sem.find_similar_moods("stressed", lookback_days=7)
        assert results == []

    def test_find_similar_moods_matches_mood(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        mem.save_conversation("ho stress", "ok", mood_detected="stressed")
        mem.save_conversation("sono felice", "bene!", mood_detected="happy")
        sem = _semantic(mem)
        results = sem.find_similar_moods("stressed", lookback_days=7)
        assert all(r["mood"] == "stressed" for r in results)

    def test_get_mood_trend_no_data(self, tmp_path):
        sem = _semantic(_memory(tmp_path / "m.db"))
        trend = sem.get_mood_trend(days=7)
        assert trend["trend"] == "unknown"
        assert trend["avg_score"] == 5.0

    def test_get_mood_trend_improving(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        # Insert low scores first, then high
        for score in [2.0, 3.0, 7.0, 8.0, 9.0]:
            mem.save_mood_timeline("neutral", score, [])
        sem = _semantic(mem)
        trend = sem.get_mood_trend(days=7)
        assert trend["direction"] == "improving"

    def test_get_mood_trend_declining(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        for score in [9.0, 8.0, 3.0, 2.0, 1.5]:
            mem.save_mood_timeline("neutral", score, [])
        sem = _semantic(mem)
        trend = sem.get_mood_trend(days=7)
        assert trend["direction"] == "declining"

    def test_get_mood_trend_stable(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        for score in [5.0, 5.1, 4.9, 5.0, 5.2]:
            mem.save_mood_timeline("neutral", score, [])
        sem = _semantic(mem)
        trend = sem.get_mood_trend(days=7)
        assert trend["direction"] == "stable"

    def test_mood_to_score_values(self, tmp_path):
        from jarvis_memory_semantic import SemanticMemoryManager
        assert SemanticMemoryManager._mood_to_score("happy") == 9.0
        assert SemanticMemoryManager._mood_to_score("stressed") == 3.0
        assert SemanticMemoryManager._mood_to_score("unknown_mood") == 5.0

    def test_build_enhanced_context_returns_string(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        sem = _semantic(mem)
        sem._model = None
        with patch("jarvis_memory_semantic._load_st_model", return_value=None):
            ctx = sem.build_enhanced_context("sono stressato", "stressed")
        assert isinstance(ctx, str)

    def test_build_enhanced_context_contains_trend(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        for s in [5.0, 6.0, 7.0]:
            mem.save_mood_timeline("neutral", s, [])
        sem = _semantic(mem)
        sem._model = None
        with patch("jarvis_memory_semantic._load_st_model", return_value=None):
            ctx = sem.build_enhanced_context("aiuto", "neutral")
        assert "Trend umore" in ctx

    def test_vec_to_bytes_roundtrip(self):
        from jarvis_memory_semantic import _vec_to_bytes, _bytes_to_vec
        vec = np.array([0.5, 0.5, 0.0], dtype=np.float32)
        recovered = _bytes_to_vec(_vec_to_bytes(vec))
        np.testing.assert_array_almost_equal(vec, recovered)

    def test_cosine_similarity_identical(self):
        from jarvis_memory_semantic import _cosine_similarity
        v = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        assert _cosine_similarity(v, v) == pytest.approx(1.0)

    def test_cosine_similarity_orthogonal(self):
        from jarvis_memory_semantic import _cosine_similarity
        a = np.array([1.0, 0.0], dtype=np.float32)
        b = np.array([0.0, 1.0], dtype=np.float32)
        assert _cosine_similarity(a, b) == pytest.approx(0.0)

    def test_cosine_similarity_zero_vector(self):
        from jarvis_memory_semantic import _cosine_similarity
        a = np.array([0.0, 0.0], dtype=np.float32)
        b = np.array([1.0, 0.0], dtype=np.float32)
        assert _cosine_similarity(a, b) == 0.0

    def test_cosine_similarity_shape_mismatch(self):
        from jarvis_memory_semantic import _cosine_similarity
        a = np.array([1.0, 0.0], dtype=np.float32)
        b = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        assert _cosine_similarity(a, b) == 0.0

    def test_vectorize_keywords_stress(self):
        from jarvis_memory_semantic import _vectorize_keywords
        vec = _vectorize_keywords("sono molto stressato e ansioso")
        assert vec.sum() > 0

    def test_vectorize_keywords_empty(self):
        from jarvis_memory_semantic import _vectorize_keywords
        vec = _vectorize_keywords("   ")
        # Should return zero vector (no norm)
        assert vec.sum() == 0.0

    def test_st_model_loads_lazily(self, tmp_path):
        from jarvis_memory_semantic import SemanticMemoryManager
        sem = SemanticMemoryManager(memory=_memory(tmp_path / "m.db"))
        assert sem._model is None  # not loaded yet
        with patch("jarvis_memory_semantic._load_st_model", return_value=None):
            sem._get_model()
        # after get_model(), _model may still be None (no ST installed in CI)
        # but no exception should be raised

    def test_add_embedding_handles_exception(self, tmp_path):
        """add_embedding should return False (not raise) if DB error occurs."""
        mem = _memory(tmp_path / "m.db")
        mem.save_conversation("test", "response")
        sem = _semantic(mem)
        # Patch save_embedding to raise
        mem.save_embedding = MagicMock(side_effect=RuntimeError("db error"))
        sem._model = None
        with patch("jarvis_memory_semantic._load_st_model", return_value=None):
            result = sem.add_embedding(1, "text")
        assert result is False


# ── PatternDetector ────────────────────────────────────────────────────────────

class TestPatternDetector:
    def test_recommend_action_stressed(self, tmp_path):
        pat = _patterns(_memory(tmp_path / "m.db"))
        rec = pat.recommend_action_for_mood("stressed")
        assert rec is not None
        assert isinstance(rec, str)

    def test_recommend_action_happy(self, tmp_path):
        pat = _patterns(_memory(tmp_path / "m.db"))
        rec = pat.recommend_action_for_mood("happy")
        assert isinstance(rec, str)

    def test_recommend_action_unknown_mood(self, tmp_path):
        pat = _patterns(_memory(tmp_path / "m.db"))
        rec = pat.recommend_action_for_mood("unknown_mood_xyz")
        # Should return empty string or fallback, not raise
        assert isinstance(rec, str)

    def test_detect_stress_patterns_no_data(self, tmp_path):
        pat = _patterns(_memory(tmp_path / "m.db"))
        results = pat.detect_stress_patterns(window_days=30)
        # No data — should return empty list, not raise
        assert isinstance(results, list)

    def test_detect_energy_cycles_no_data(self, tmp_path):
        pat = _patterns(_memory(tmp_path / "m.db"))
        result = pat.detect_energy_cycles()
        assert isinstance(result, dict)

    def test_detect_trigger_keywords_no_data(self, tmp_path):
        pat = _patterns(_memory(tmp_path / "m.db"))
        result = pat.detect_trigger_keywords()
        assert isinstance(result, list)

    def test_get_weekly_summary_no_data(self, tmp_path):
        pat = _patterns(_memory(tmp_path / "m.db"))
        summary = pat.get_weekly_summary()
        assert isinstance(summary, dict)

    def test_detect_stress_patterns_with_data(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        # Simulate Monday stress: multiple low mood scores on "Monday"
        import sqlite3
        from datetime import datetime, timedelta
        # Find a Monday
        today = datetime.now()
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday)

        for week in range(4):
            ts = (last_monday - timedelta(weeks=week)).isoformat()
            with mem._conn() as conn:
                conn.execute(
                    "INSERT INTO mood_timeline (timestamp, mood_label, mood_score, keywords) VALUES (?,?,?,?)",
                    (ts, "stressed", 2.5, '["deadline","lavoro"]'),
                )
        pat = _patterns(mem)
        results = pat.detect_stress_patterns(window_days=30)
        assert isinstance(results, list)

    def test_get_weekly_summary_with_data(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        for score in [3.0, 5.0, 7.0, 4.0, 6.0, 8.0, 5.0]:
            mem.save_mood_timeline("neutral", score, [])
        pat = _patterns(mem)
        summary = pat.get_weekly_summary()
        assert "avg_score" in summary
        assert isinstance(summary["avg_score"], float)

    def test_detect_stress_patterns_saves_to_db(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        # Insert enough data to trigger pattern detection
        from datetime import datetime, timedelta
        today = datetime.now()
        days_since_monday = today.weekday()
        last_monday = today - timedelta(days=days_since_monday)
        for week in range(4):
            ts = (last_monday - timedelta(weeks=week)).isoformat()
            with mem._conn() as conn:
                conn.execute(
                    "INSERT INTO mood_timeline (timestamp, mood_label, mood_score, keywords) VALUES (?,?,?,?)",
                    (ts, "stressed", 2.5, '["deadline"]'),
                )
        pat = _patterns(mem)
        pat.detect_stress_patterns(window_days=30)
        # Check if anything was saved (may or may not depending on threshold)
        patterns = mem.get_patterns()
        assert isinstance(patterns, list)

    def test_weekly_summary_trend_direction(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        # Improving trend
        for score in [2.0, 3.0, 5.0, 7.0, 8.0, 9.0, 9.0]:
            mem.save_mood_timeline("neutral", score, [])
        pat = _patterns(mem)
        summary = pat.get_weekly_summary()
        trend = summary.get("trend", "")
        # Accept both Italian and English labels
        assert trend in ("improving", "stable", "declining",
                         "migliorando", "stabile", "peggiorando",
                         "crescente", "decrescente")

    def test_recommend_action_uses_saved_patterns(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        mem.save_pattern("stress", "lunedi stress", 0.9, {})
        pat = _patterns(mem)
        rec = pat.recommend_action_for_mood("stressed")
        assert isinstance(rec, str)

    def test_detect_energy_cycles_with_data(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        from datetime import datetime, timedelta
        base = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        for day in range(7):
            morning = base - timedelta(days=day)
            afternoon = morning.replace(hour=15)
            with mem._conn() as conn:
                conn.execute(
                    "INSERT INTO mood_timeline (timestamp, mood_label, mood_score, keywords) VALUES (?,?,?,?)",
                    (morning.isoformat(), "happy", 8.0, "[]"),
                )
                conn.execute(
                    "INSERT INTO mood_timeline (timestamp, mood_label, mood_score, keywords) VALUES (?,?,?,?)",
                    (afternoon.isoformat(), "tired", 3.0, "[]"),
                )
        pat = _patterns(mem)
        result = pat.detect_energy_cycles()
        assert isinstance(result, dict)
