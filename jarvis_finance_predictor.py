"""
jarvis_finance_predictor.py — JARVIS v4.0 Burn Rate & Spending Prediction

Statistical analysis of spending patterns:
  - Daily average calculation
  - End-of-month projection
  - Days until budget exhausted
  - Actionable spending-cut suggestions
"""

import logging
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger("jarvis.finance.predictor")

_URGENCY_HIGH   = 7   # days remaining
_URGENCY_MEDIUM = 14


class BurnRatePredictor:
    """
    Burn rate analysis using the FinanceManager data.
    All calculations are local — no API calls.
    """

    def __init__(self, finance_manager):
        self.finance = finance_manager

    # ── Core metrics ──────────────────────────────────────────────────────────

    def calculate_daily_average(self, window_days: int = 30) -> float:
        """
        Average daily spend over the last `window_days` days.
        Returns 0.0 if no transactions found.
        """
        end = date.today()
        start = end - timedelta(days=window_days - 1)
        txns = self.finance.memory.get_transactions(
            start.isoformat(), end.isoformat()
        )
        if not txns:
            return 0.0
        total = sum(t["amount"] for t in txns)
        # Use actual days with data to avoid division by zero
        days_with_data = len({t["date"] for t in txns})
        return round(total / max(days_with_data, 1), 2)

    def project_monthly_spend(self) -> dict:
        """
        At current daily average, how much will be spent by end of month?

        Returns:
          {
            "month": "2026-04",
            "spent_so_far": 650.0,
            "daily_avg": 43.33,
            "days_left": 15,
            "projected_total": 1300.0,
            "budget": 2000.0,
            "projected_remaining": 700.0,
            "will_exceed": False,
          }
        """
        today = date.today()
        month_str = today.strftime("%Y-%m")
        summary = self.finance.get_monthly_summary(month_str)
        daily_avg = self.calculate_daily_average(window_days=30)
        days_left = summary["days_left_in_month"]

        projected_total = round(summary["total_spent"] + daily_avg * days_left, 2)
        projected_remaining = round(summary["budget_limit"] - projected_total, 2)

        return {
            "month":                month_str,
            "spent_so_far":         summary["total_spent"],
            "daily_avg":            daily_avg,
            "days_left":            days_left,
            "projected_total":      projected_total,
            "budget":               summary["budget_limit"],
            "projected_remaining":  projected_remaining,
            "will_exceed":          projected_total > summary["budget_limit"],
        }

    def calculate_days_until_empty(
        self,
        initial_balance: float,
        current_spent: Optional[float] = None,
    ) -> dict:
        """
        At current burn rate, when will `initial_balance` run out?

        Args:
            initial_balance: total money available (e.g. monthly budget or actual balance)
            current_spent:   already spent this month (None = query from DB)

        Returns:
          {
            "days_remaining": 24,
            "date_empty": "2026-05-02",
            "urgency": "HIGH" | "MEDIUM" | "LOW",
            "daily_avg": 41.67,
            "balance_left": 750.0,
          }
        """
        today = date.today()
        month_str = today.strftime("%Y-%m")

        if current_spent is None:
            summary = self.finance.get_monthly_summary(month_str)
            current_spent = summary["total_spent"]

        balance_left = max(initial_balance - current_spent, 0.0)
        daily_avg = self.calculate_daily_average(window_days=30)

        if daily_avg <= 0:
            days_remaining = 999
        else:
            days_remaining = int(balance_left / daily_avg)

        empty_date = (today + timedelta(days=days_remaining)).isoformat()

        if days_remaining <= _URGENCY_HIGH:
            urgency = "HIGH"
        elif days_remaining <= _URGENCY_MEDIUM:
            urgency = "MEDIUM"
        else:
            urgency = "LOW"

        return {
            "days_remaining": days_remaining,
            "date_empty":     empty_date,
            "urgency":        urgency,
            "daily_avg":      daily_avg,
            "balance_left":   round(balance_left, 2),
        }

    # ── Suggestions ───────────────────────────────────────────────────────────

    def suggest_spending_cuts(self) -> list[str]:
        """
        Analyse current month's by-category spend vs budgets.
        Returns actionable Italian suggestions.
        """
        month_str = date.today().strftime("%Y-%m")
        summary = self.finance.get_monthly_summary(month_str)
        by_cat = summary.get("by_category", {})
        budgets = self.finance.category_budgets
        suggestions = []

        for cat, spent in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
            limit = budgets.get(cat, 0)
            if limit <= 0:
                continue
            pct = spent / limit
            if pct > 1.0:
                over = round(spent - limit, 2)
                suggestions.append(
                    f"Hai superato il budget {cat} di €{over:.0f}. "
                    f"Prova a ridurre le spese {cat} del 20% il prossimo mese."
                )
            elif pct > 0.80:
                saveable = round(spent * 0.20, 2)
                suggestions.append(
                    f"Spese {cat} al {pct*100:.0f}% del budget. "
                    f"Risparmiare €{saveable:.0f}/mese è possibile con piccoli tagli."
                )

        if not suggestions:
            suggestions.append(
                "Spese nella norma — continua così! "
                "Potresti mettere da parte una % delle entrate per i tuoi obiettivi."
            )
        return suggestions

    # ── Full prediction report ────────────────────────────────────────────────

    def predict_burn_rate(self) -> dict:
        """
        Main method: full burn-rate report.

        Returns:
          {
            "daily_average": 41.67,
            "projected_monthly": 1250.0,
            "burn_rate": 41.67,
            "days_until_empty": 24,
            "date_empty": "2026-05-02",
            "urgency": "MEDIUM",
            "alert": "...",
            "suggestions": [...],
          }
        """
        projection = self.project_monthly_spend()
        daily_avg = projection["daily_avg"]
        budget = projection["budget"]

        empty_info = self.calculate_days_until_empty(
            initial_balance=budget,
            current_spent=projection["spent_so_far"],
        )

        suggestions = self.suggest_spending_cuts()

        # Build alert message
        if projection["will_exceed"]:
            over = round(projection["projected_total"] - budget, 2)
            alert = (
                f"⚠ Al ritmo attuale supererai il budget di €{over:.0f} "
                f"entro fine mese (proiezione: €{projection['projected_total']:.0f}/€{budget:.0f})"
            )
        elif empty_info["urgency"] == "HIGH":
            alert = (
                f"⚠ Attenzione: budget quasi esaurito. "
                f"Rimangono circa {empty_info['days_remaining']} giorni di spesa."
            )
        else:
            alert = (
                f"Burn rate: €{daily_avg:.2f}/giorno. "
                f"Proiezione fine mese: €{projection['projected_total']:.0f}."
            )

        return {
            "daily_average":      daily_avg,
            "projected_monthly":  projection["projected_total"],
            "burn_rate":          daily_avg,
            "days_until_empty":   empty_info["days_remaining"],
            "date_empty":         empty_info["date_empty"],
            "urgency":            empty_info["urgency"],
            "alert":              alert,
            "suggestions":        suggestions,
            "will_exceed_budget": projection["will_exceed"],
        }
