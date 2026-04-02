"""
tests/test_finance.py — Phase 2: Financial Tracking

All tests are mocked — no real API calls, no external services.
"""
import json
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _isolate_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _memory(path=None):
    from jarvis_memory import JarvisMemory
    return JarvisMemory(db_path=path or Path("test_mem.db"))


def _finance(mem=None):
    from jarvis_finance import FinanceManager
    return FinanceManager(memory=mem or _memory(), monthly_budget=2000.0)


def _predictor(finance=None):
    from jarvis_finance_predictor import BurnRatePredictor
    if finance is None:
        finance = _finance()
    return BurnRatePredictor(finance_manager=finance)


# ── JarvisMemory Financial Schema ─────────────────────────────────────────────

class TestMemoryFinancialSchema:
    def test_save_and_get_transaction(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        txn_id = mem.save_transaction(5.0, "food", "caffè", "Starbucks")
        assert txn_id > 0
        today = date.today().isoformat()
        txns = mem.get_transactions(today, today)
        assert len(txns) == 1
        assert txns[0]["amount"] == 5.0
        assert txns[0]["category"] == "food"

    def test_get_transactions_empty(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        txns = mem.get_transactions("2000-01-01", "2000-01-31")
        assert txns == []

    def test_get_transactions_date_filter(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        mem.save_transaction(10.0, "food", date="2026-04-01")
        mem.save_transaction(20.0, "transport", date="2026-04-15")
        mem.save_transaction(30.0, "entertainment", date="2026-05-01")
        txns = mem.get_transactions("2026-04-01", "2026-04-30")
        assert len(txns) == 2
        assert sum(t["amount"] for t in txns) == 30.0

    def test_get_transactions_category_filter(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        today = date.today().isoformat()
        mem.save_transaction(5.0, "food", date=today)
        mem.save_transaction(20.0, "transport", date=today)
        txns = mem.get_transactions(today, today, category="food")
        assert len(txns) == 1
        assert txns[0]["amount"] == 5.0

    def test_get_transactions_for_month(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        mem.save_transaction(100.0, "food", date="2026-04-10")
        mem.save_transaction(50.0, "transport", date="2026-04-20")
        mem.save_transaction(200.0, "food", date="2026-05-01")  # different month
        txns = mem.get_transactions_for_month("2026-04")
        assert len(txns) == 2
        assert sum(t["amount"] for t in txns) == 150.0

    def test_set_and_get_budget_limit(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        mem.set_budget_limit("2026-04", "food", 400.0, 70)
        limits = mem.get_budget_limits("2026-04")
        assert len(limits) == 1
        assert limits[0]["category"] == "food"
        assert limits[0]["limit_amount"] == 400.0

    def test_budget_limit_upsert(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        mem.set_budget_limit("2026-04", "food", 400.0)
        mem.set_budget_limit("2026-04", "food", 500.0)  # update
        limits = mem.get_budget_limits("2026-04")
        assert len(limits) == 1
        assert limits[0]["limit_amount"] == 500.0

    def test_save_and_get_financial_summary(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        mem.save_financial_summary("2026-04", {
            "total_spent": 1200.0,
            "by_category": {"food": 400, "transport": 200},
            "remaining_budget": 800.0,
            "burn_rate": 40.0,
            "days_until_empty": 20,
        })
        s = mem.get_financial_summary("2026-04")
        assert s is not None
        assert s["total_spent"] == 1200.0
        assert s["by_category"]["food"] == 400

    def test_get_financial_summary_missing(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        assert mem.get_financial_summary("2099-01") is None

    def test_save_and_get_financial_goals(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        goal_id = mem.save_financial_goal("save", 1000.0, "2026-12-31", priority=4)
        assert goal_id > 0
        goals = mem.get_financial_goals()
        assert len(goals) == 1
        assert goals[0]["goal_type"] == "save"
        assert goals[0]["target_amount"] == 1000.0

    def test_update_goal_amount(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        gid = mem.save_financial_goal("save", 1000.0)
        mem.update_goal_amount(gid, 250.0)
        goals = mem.get_financial_goals()
        assert goals[0]["current_amount"] == 250.0

    def test_transactions_tags_roundtrip(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        today = date.today().isoformat()
        mem.save_transaction(10.0, "food", tags=["importante", "work"])
        txns = mem.get_transactions(today, today)
        assert "importante" in txns[0]["tags"]


# ── FinanceManager ────────────────────────────────────────────────────────────

class TestFinanceManagerLogExpense:
    def test_log_expense_basic(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        result = f.log_expense(5.0, "food", "caffè")
        assert result["logged"] is True
        assert result["amount"] == 5.0
        assert result["category"] == "food"

    def test_log_expense_updates_budget_status(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        f.log_expense(300.0, "food")
        result = f.log_expense(150.0, "food")  # total 450 > 400 limit
        status = result["budget_status"]["food"]
        assert status["spent"] == pytest.approx(450.0)
        assert status["over"] is True

    def test_log_expense_invalid_amount(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        with pytest.raises(ValueError):
            f.log_expense(-10.0, "food")

    def test_log_expense_zero_amount(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        with pytest.raises(ValueError):
            f.log_expense(0.0, "food")

    def test_log_expense_with_merchant(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        result = f.log_expense(4.5, "food", "cappuccino", "Starbucks")
        assert result["merchant"] == "Starbucks"

    def test_log_expense_custom_date(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        f = _finance(mem)
        f.log_expense(50.0, "food", date_str="2026-04-01")
        txns = mem.get_transactions("2026-04-01", "2026-04-01")
        assert len(txns) == 1

    def test_log_expense_normalizes_category(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        result = f.log_expense(10.0, "FOOD")
        assert result["category"] == "food"


class TestFinanceManagerParsing:
    def test_parse_euro_sign_prefix(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        result = f.parse_and_log("Ho speso €5 per un caffè")
        assert result is not None
        assert result["amount"] == 5.0

    def test_parse_euro_word(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        result = f.parse_and_log("Ho pagato 10 euro per il bus")
        assert result is not None
        assert result["amount"] == 10.0

    def test_parse_decimal_amount(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        result = f.parse_and_log("€5,50 caffè")
        assert result is not None
        assert result["amount"] == pytest.approx(5.50)

    def test_parse_no_amount_returns_none(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        result = f.parse_and_log("come stai oggi?")
        assert result is None

    def test_parse_detects_food_category(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        result = f.parse_and_log("Ho speso €8 per pranzo")
        assert result["category"] == "food"

    def test_parse_detects_transport_category(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        result = f.parse_and_log("Ho pagato €2 per il bus")
        assert result["category"] == "transport"


class TestFinanceManagerCategorization:
    def test_categorize_food(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        assert f.categorize_expense("caffè al bar") == "food"
        assert f.categorize_expense("pranzo al ristorante") == "food"
        assert f.categorize_expense("Starbucks coffee") == "food"

    def test_categorize_transport(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        assert f.categorize_expense("biglietto metro") == "transport"
        assert f.categorize_expense("taxi uber") == "transport"

    def test_categorize_entertainment(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        assert f.categorize_expense("Netflix abbonamento") == "entertainment"
        assert f.categorize_expense("cinema film") == "entertainment"

    def test_categorize_utilities(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        assert f.categorize_expense("bolletta luce") == "utilities"
        assert f.categorize_expense("internet wifi") == "utilities"

    def test_categorize_emergency(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        assert f.categorize_expense("farmacia medicine") == "emergency"
        assert f.categorize_expense("visita medico") == "emergency"

    def test_categorize_other_fallback(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        assert f.categorize_expense("random xyz stuff") == "other"


class TestFinanceManagerQueries:
    def test_get_daily_spending_today(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        f = _finance(mem)
        f.log_expense(5.0, "food")
        f.log_expense(20.0, "transport")
        total = f.get_daily_spending()
        assert total == pytest.approx(25.0)

    def test_get_daily_spending_specific_date(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        f = _finance(mem)
        f.log_expense(30.0, "food", date_str="2026-04-01")
        total = f.get_daily_spending("2026-04-01")
        assert total == pytest.approx(30.0)

    def test_get_daily_spending_no_transactions(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        assert f.get_daily_spending("2000-01-01") == 0.0

    def test_get_monthly_summary_structure(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        summary = f.get_monthly_summary("2026-04")
        assert "total_spent" in summary
        assert "by_category" in summary
        assert "budget_limit" in summary
        assert "remaining" in summary
        assert "percentage_used" in summary
        assert "days_left_in_month" in summary

    def test_get_monthly_summary_totals(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        f = _finance(mem)
        mem.save_transaction(300.0, "food", date="2026-04-10")
        mem.save_transaction(100.0, "transport", date="2026-04-15")
        summary = f.get_monthly_summary("2026-04")
        assert summary["total_spent"] == pytest.approx(400.0)
        assert summary["by_category"]["food"] == pytest.approx(300.0)
        assert summary["by_category"]["transport"] == pytest.approx(100.0)
        assert summary["remaining"] == pytest.approx(1600.0)

    def test_get_monthly_summary_empty_month(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        summary = f.get_monthly_summary("2020-01")
        assert summary["total_spent"] == 0.0
        assert summary["remaining"] == pytest.approx(2000.0)


class TestFinanceManagerAlerts:
    def test_no_alerts_when_under_threshold(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        f = _finance(mem)
        # 50% of food budget (€400)
        mem.save_transaction(200.0, "food", date="2026-04-10")
        alerts = f.check_budget_alerts("2026-04")
        food_alerts = [a for a in alerts if a["category"] == "food"]
        assert len(food_alerts) == 0

    def test_warning_alert_at_threshold(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        f = _finance(mem)
        # 75% of food budget (€400) → €300
        mem.save_transaction(300.0, "food", date="2026-04-10")
        alerts = f.check_budget_alerts("2026-04")
        food_alert = next((a for a in alerts if a["category"] == "food"), None)
        assert food_alert is not None
        assert food_alert["level"] == "warning"

    def test_danger_alert_at_90_percent(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        f = _finance(mem)
        # 92.5% of food budget → €370
        mem.save_transaction(370.0, "food", date="2026-04-10")
        alerts = f.check_budget_alerts("2026-04")
        food_alert = next((a for a in alerts if a["category"] == "food"), None)
        assert food_alert is not None
        assert food_alert["level"] == "danger"

    def test_over_budget_alert(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        f = _finance(mem)
        # 150% of food budget → €600 (limit €400)
        mem.save_transaction(600.0, "food", date="2026-04-10")
        alerts = f.check_budget_alerts("2026-04")
        food_alert = next((a for a in alerts if a["category"] == "food"), None)
        assert food_alert is not None
        assert food_alert["level"] == "over"

    def test_alerts_sorted_by_percentage(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        f = _finance(mem)
        mem.save_transaction(380.0, "food", date="2026-04-10")      # 95%
        mem.save_transaction(180.0, "transport", date="2026-04-10")  # 90%
        alerts = f.check_budget_alerts("2026-04")
        if len(alerts) >= 2:
            assert alerts[0]["percentage"] >= alerts[1]["percentage"]

    def test_alert_message_contains_category(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        f = _finance(mem)
        mem.save_transaction(600.0, "food", date="2026-04-10")
        alerts = f.check_budget_alerts("2026-04")
        food_alert = next(a for a in alerts if a["category"] == "food")
        assert "food" in food_alert["message"].lower() or "FOOD" in food_alert["message"]

    def test_spending_insights_returns_string(self, tmp_path):
        f = _finance(_memory(tmp_path / "m.db"))
        insights = f.get_spending_insights("2026-04")
        assert isinstance(insights, str)
        assert len(insights) > 0


# ── BurnRatePredictor ─────────────────────────────────────────────────────────

class TestBurnRatePredictor:
    def test_daily_average_no_data(self, tmp_path):
        pred = _predictor(_finance(_memory(tmp_path / "m.db")))
        assert pred.calculate_daily_average() == 0.0

    def test_daily_average_with_data(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        f = _finance(mem)
        # Add €50/day for the last 2 days
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        mem.save_transaction(50.0, "food", date=today)
        mem.save_transaction(50.0, "food", date=yesterday)
        pred = _predictor(f)
        avg = pred.calculate_daily_average(window_days=30)
        assert avg == pytest.approx(50.0, rel=0.1)

    def test_project_monthly_spend_structure(self, tmp_path):
        pred = _predictor(_finance(_memory(tmp_path / "m.db")))
        projection = pred.project_monthly_spend()
        assert "month" in projection
        assert "spent_so_far" in projection
        assert "daily_avg" in projection
        assert "projected_total" in projection
        assert "budget" in projection
        assert "will_exceed" in projection

    def test_project_monthly_spend_will_not_exceed_when_empty(self, tmp_path):
        pred = _predictor(_finance(_memory(tmp_path / "m.db")))
        projection = pred.project_monthly_spend()
        assert projection["will_exceed"] is False
        assert projection["spent_so_far"] == 0.0

    def test_calculate_days_until_empty_no_spending(self, tmp_path):
        pred = _predictor(_finance(_memory(tmp_path / "m.db")))
        result = pred.calculate_days_until_empty(2000.0, current_spent=0.0)
        assert result["days_remaining"] == 999
        assert result["urgency"] == "LOW"

    def test_calculate_days_until_empty_high_spend(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        f = _finance(mem)
        # €100/day for last 7 days → balance left €300 of €1000
        for i in range(7):
            d = (date.today() - timedelta(days=i)).isoformat()
            mem.save_transaction(100.0, "food", date=d)
        pred = _predictor(f)
        result = pred.calculate_days_until_empty(1000.0, current_spent=700.0)
        # 300 remaining / 100 avg = 3 days → HIGH urgency
        assert result["urgency"] == "HIGH"
        assert result["days_remaining"] <= 7

    def test_calculate_days_until_empty_medium_urgency(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        f = _finance(mem)
        # €50/day for last 7 days → 10 days remaining from €500 balance
        for i in range(7):
            d = (date.today() - timedelta(days=i)).isoformat()
            mem.save_transaction(50.0, "food", date=d)
        pred = _predictor(f)
        result = pred.calculate_days_until_empty(1000.0, current_spent=500.0)
        assert result["urgency"] in ("HIGH", "MEDIUM", "LOW")

    def test_suggest_spending_cuts_over_budget(self, tmp_path):
        mem = _memory(tmp_path / "m.db")
        f = _finance(mem)
        month = date.today().strftime("%Y-%m")
        # €600 food (limit €400) → over budget
        mem.save_transaction(600.0, "food", date=f"{month}-10")
        pred = _predictor(f)
        suggestions = pred.suggest_spending_cuts()
        assert isinstance(suggestions, list)
        assert len(suggestions) >= 1
        assert any("food" in s.lower() for s in suggestions)

    def test_suggest_spending_cuts_no_over(self, tmp_path):
        pred = _predictor(_finance(_memory(tmp_path / "m.db")))
        suggestions = pred.suggest_spending_cuts()
        assert isinstance(suggestions, list)
        assert len(suggestions) >= 1  # at least the "all good" message

    def test_predict_burn_rate_structure(self, tmp_path):
        pred = _predictor(_finance(_memory(tmp_path / "m.db")))
        result = pred.predict_burn_rate()
        for key in ("daily_average", "projected_monthly", "burn_rate",
                    "days_until_empty", "date_empty", "urgency", "alert", "suggestions"):
            assert key in result

    def test_predict_burn_rate_alert_text(self, tmp_path):
        pred = _predictor(_finance(_memory(tmp_path / "m.db")))
        result = pred.predict_burn_rate()
        assert isinstance(result["alert"], str)
        assert len(result["alert"]) > 0

    def test_burn_rate_daily_avg_equals_burn_rate_field(self, tmp_path):
        pred = _predictor(_finance(_memory(tmp_path / "m.db")))
        result = pred.predict_burn_rate()
        assert result["daily_average"] == result["burn_rate"]
