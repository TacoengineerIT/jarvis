"""
Tests for finance_engine.py — rent gap tracker.
Uses isolated tmp_path for JSON file so no side effects on real data.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch

import finance_engine as fe


@pytest.fixture(autouse=True)
def _patch_finance_file(tmp_path):
    """Redirect FINANCE_FILE to temp dir for every test."""
    fpath = tmp_path / "config" / "finances.json"
    with patch.object(fe, "FINANCE_FILE", fpath):
        yield fpath


class TestCheckGap:

    def test_zero_entrate(self):
        """Fresh state: gap should equal target (110)."""
        gap, msg = fe.check_gap()
        assert gap == 110.0
        assert "110" in msg
        assert "mancano" in msg.lower()

    def test_partial_entrate(self, tmp_path):
        """Entrate=50 → gap should be 60."""
        fe.update_finances(50.0)
        gap, msg = fe.check_gap()
        assert gap == pytest.approx(60.0)
        assert "60.00" in msg

    def test_coperto(self):
        """Entrate >= target → gap <= 0, surplus message."""
        fe.update_finances(120.0)
        gap, msg = fe.check_gap()
        assert gap <= 0
        assert "surplus" in msg.lower() or "obiettivo" in msg.lower()

    def test_exact_match(self):
        """Entrate == target → gap = 0."""
        fe.update_finances(110.0)
        gap, msg = fe.check_gap()
        assert gap == 0.0
        assert "obiettivo" in msg.lower()


class TestUpdateFinances:

    def test_aggiorna_entrate(self):
        """Update income to 80, verify persistence."""
        fe.update_finances(80.0)
        data = fe.load_finances()
        assert data["entrate_attuali"] == 80.0

    def test_aggiorna_target(self):
        """Update both income and target."""
        fe.update_finances(50.0, new_target=200.0)
        data = fe.load_finances()
        assert data["entrate_attuali"] == 50.0
        assert data["target_affitto"] == 200.0

    def test_add_income(self):
        """Add incremental income entries."""
        fe.add_income(30.0, "lezione privata")
        fe.add_income(20.0, "ripetizione")
        data = fe.load_finances()
        assert data["entrate_attuali"] == pytest.approx(50.0)
        assert len(data["voci_entrata"]) == 2


class TestTTSOutput:

    def test_tts_output_not_empty(self):
        """check_gap message is never empty."""
        _, msg = fe.check_gap()
        assert msg and len(msg) > 5

    def test_report_not_empty(self):
        """get_report always returns non-empty string."""
        report = fe.get_report()
        assert report and len(report) > 10
        assert "Sir" in report or "euro" in report

    def test_tts_randomization(self):
        """Report content changes when data changes (not static)."""
        fe.update_finances(0.0)
        r1 = fe.get_report()
        fe.update_finances(80.0)
        r2 = fe.get_report()
        assert r1 != r2


class TestEdgeCases:

    def test_corrupt_json(self, tmp_path):
        """Corrupt JSON falls back to defaults."""
        fpath = tmp_path / "config" / "finances.json"
        fpath.parent.mkdir(parents=True, exist_ok=True)
        fpath.write_text("{invalid json!!!", encoding="utf-8")
        data = fe.load_finances()
        assert data["target_affitto"] == 110.0

    def test_missing_file(self):
        """Missing file returns defaults."""
        data = fe.load_finances()
        assert data["target_affitto"] == 110.0
        assert data["entrate_attuali"] == 0.0
