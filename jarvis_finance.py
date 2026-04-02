"""
jarvis_finance.py — JARVIS v4.0 Financial Tracking

Handles:
  - Expense logging with natural language parsing
  - Category detection from Italian/English descriptions
  - Monthly budget tracking with alerts
  - Spending insights and summaries
"""

import json
import logging
import re
from datetime import date, datetime
from typing import Optional

logger = logging.getLogger("jarvis.finance")

# ── Default budgets ────────────────────────────────────────────────────────────

DEFAULT_MONTHLY_BUDGET = 2000.0

DEFAULT_CATEGORY_BUDGETS: dict[str, float] = {
    "food":          400.0,
    "transport":     200.0,
    "entertainment": 500.0,
    "utilities":     300.0,
    "emergency":     200.0,
    "other":         400.0,
}

WARNING_THRESHOLD = 0.70  # 70%

# ── Category keyword map ───────────────────────────────────────────────────────

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "food": [
        "caffè", "caffe", "coffee", "pranzo", "cena", "colazione", "pizza",
        "pasta", "supermercato", "grocery", "spesa", "ristorante", "restaurant",
        "bar", "gelato", "panino", "kebab", "sushi", "mcdonald", "burger",
        "starbucks", "bakery", "pasticceria", "trattoria", "osteria",
        "aperitivo", "spritz", "birra", "vino", "wine", "cibo", "food",
        "takeaway", "delivery", "just eat", "glovo",
    ],
    "transport": [
        "bus", "metro", "taxi", "treno", "train", "tram", "benzina", "gasolio",
        "parcheggio", "parking", "autobus", "uber", "lyft", "bolt", "cabify",
        "biglietto", "ticket", "trenitalia", "italo", "atm",
        "autostrada", "toll", "traghetto", "ferry", "volo", "ryanair", "easyjet",
    ],
    "entertainment": [
        "cinema", "netflix", "spotify", "amazon prime", "disney", "hbo",
        "concert", "concerto", "teatro", "museum", "museo", "libro", "book",
        "gioco", "game", "steam", "playstation", "xbox", "nintendo",
        "palestra", "gym", "fitness", "sport", "calcio", "biglietto",
        "festival", "evento", "event", "abbonamento",
    ],
    "utilities": [
        "luce", "electricity", "gas", "internet", "telefono", "phone",
        "affitto", "rent", "acqua", "water", "bolletta", "bill",
        "assicurazione", "insurance", "canone", "subscription",
    ],
    "emergency": [
        "ospedale", "hospital", "medico", "doctor", "farmacia", "pharmacy",
        "ambulanza", "pronto soccorso", "dentista", "dentist", "visita",
        "riparazione", "repair", "rottura", "broken", "urgente", "urgent",
        "avvocato", "lawyer",
    ],
}

# ── Amount regex patterns ──────────────────────────────────────────────────────

_AMOUNT_PATTERNS = [
    # "€5", "€5.50", "€ 5", "€5,50"
    re.compile(r"€\s*(\d+(?:[.,]\d{1,2})?)", re.IGNORECASE),
    # "5 euro", "5 EUR", "5€"
    re.compile(r"(\d+(?:[.,]\d{1,2})?)\s*(?:€|euro|eur)\b", re.IGNORECASE),
    # "5 dollari", "5 USD"
    re.compile(r"(\d+(?:[.,]\d{1,2})?)\s*(?:dollari?|usd|\$)\b", re.IGNORECASE),
    # bare number as last resort: "ho speso 5 per"
    re.compile(r"\b(\d+(?:[.,]\d{1,2})?)\b"),
]


def _parse_amount(text: str) -> Optional[float]:
    """Extract the first monetary amount from text. Returns None if not found."""
    for pattern in _AMOUNT_PATTERNS[:-1]:  # try specific patterns first
        m = pattern.search(text)
        if m:
            return float(m.group(1).replace(",", "."))
    # Bare number fallback — only use if text has a financial verb
    financial_verbs = ["speso", "comprato", "pagato", "costato", "costa", "spendo"]
    if any(v in text.lower() for v in financial_verbs):
        m = _AMOUNT_PATTERNS[-1].search(text)
        if m:
            return float(m.group(1).replace(",", "."))
    return None


def _parse_merchant(text: str) -> str:
    """Extract merchant name from 'a/da/at <merchant>' patterns."""
    m = re.search(r"(?:a|da|at|in|presso)\s+([A-Z][a-zA-Z'&\s]{2,20})", text)
    if m:
        return m.group(1).strip()
    return ""


class FinanceManager:
    """Local financial tracking — no cloud API calls."""

    def __init__(
        self,
        memory=None,
        monthly_budget: float = DEFAULT_MONTHLY_BUDGET,
        category_budgets: Optional[dict] = None,
        warning_threshold: float = WARNING_THRESHOLD,
    ):
        if memory is None:
            from jarvis_memory import JarvisMemory
            memory = JarvisMemory()
        self.memory = memory
        self.monthly_budget = monthly_budget
        self.category_budgets = dict(category_budgets or DEFAULT_CATEGORY_BUDGETS)
        self.warning_threshold = warning_threshold

    # ── Expense logging ──────────────────────────────────────────────────────

    def log_expense(
        self,
        amount: float,
        category: str,
        description: str = "",
        merchant: str = "",
        currency: str = "EUR",
        date_str: Optional[str] = None,
        tags: Optional[list] = None,
    ) -> dict:
        """
        Log an expense. Returns a summary dict with budget status.

        Example:
          finance.log_expense(5.0, "food", "caffè", "Starbucks")
          → {"logged": True, "amount": 5.0, "category": "food",
             "budget_status": {"food": {"spent": 360, "limit": 400, "pct": 90.0}}}
        """
        if amount <= 0:
            raise ValueError(f"Amount must be positive, got {amount}")
        category = category.lower().strip()
        txn_date = date_str or date.today().isoformat()
        month = txn_date[:7]  # "YYYY-MM"

        self.memory.save_transaction(
            amount=amount,
            category=category,
            description=description,
            merchant=merchant,
            currency=currency,
            date=txn_date,
            tags=tags or [],
        )

        # Refresh category spent
        spent = self._get_category_spent(category, month)
        limit = self.category_budgets.get(category, self.monthly_budget)
        pct = (spent / limit * 100) if limit > 0 else 0.0

        result = {
            "logged":   True,
            "amount":   amount,
            "category": category,
            "merchant": merchant,
            "budget_status": {
                category: {
                    "spent": round(spent, 2),
                    "limit": limit,
                    "pct":   round(pct, 1),
                    "over":  spent > limit,
                }
            },
        }
        logger.info(
            "[FINANCE] Logged €%.2f %s (%s) | budget %s: %.0f%%",
            amount, category, description, category, pct
        )
        return result

    def parse_and_log(self, text: str) -> Optional[dict]:
        """
        Parse natural language expense and log it.

        "Ho speso €5 per un caffè a Starbucks"
        → logs amount=5.0, category="food", description="caffè", merchant="Starbucks"
        """
        amount = _parse_amount(text)
        if amount is None:
            return None
        description, category = self._extract_description_and_category(text)
        merchant = _parse_merchant(text)
        return self.log_expense(amount, category, description, merchant)

    def _extract_description_and_category(self, text: str) -> tuple[str, str]:
        """Return (description, category) from raw text."""
        # Strip amount tokens
        cleaned = re.sub(r"€\s*\d+(?:[.,]\d{1,2})?", "", text)
        cleaned = re.sub(r"\d+(?:[.,]\d{1,2})?\s*(?:€|euro|eur)\b", "", cleaned, flags=re.I)
        # Strip filler verbs
        fillers = r"\b(ho speso|ho comprato|ho pagato|comprato|pagato|speso|per un|per una|per|a|da|in)\b"
        cleaned = re.sub(fillers, " ", cleaned, flags=re.I).strip()
        description = re.sub(r"\s{2,}", " ", cleaned).strip()
        category = self.categorize_expense(description or text)
        return description, category

    # ── Categorization ───────────────────────────────────────────────────────

    def categorize_expense(self, description: str) -> str:
        """Map description to a spending category using keyword matching."""
        text = description.lower()
        for cat, keywords in _CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                return cat
        return "other"

    # ── Queries ──────────────────────────────────────────────────────────────

    def get_daily_spending(self, date_str: Optional[str] = None) -> float:
        """Return total amount spent on a given date (default: today)."""
        target = date_str or date.today().isoformat()
        txns = self.memory.get_transactions(target, target)
        return sum(t["amount"] for t in txns)

    def get_monthly_summary(self, month: Optional[str] = None) -> dict:
        """
        Return monthly spending summary.

        Returns:
          {
            "month": "2026-04",
            "total_spent": 1150.0,
            "by_category": {"food": 350, ...},
            "budget_limit": 2000.0,
            "remaining": 850.0,
            "percentage_used": 57.5,
            "days_left_in_month": 15,
          }
        """
        month = month or date.today().strftime("%Y-%m")
        txns = self.memory.get_transactions_for_month(month)

        by_category: dict[str, float] = {}
        total = 0.0
        for t in txns:
            cat = t["category"]
            by_category[cat] = round(by_category.get(cat, 0.0) + t["amount"], 2)
            total += t["amount"]
        total = round(total, 2)

        remaining = round(self.monthly_budget - total, 2)
        pct = round(total / self.monthly_budget * 100, 1) if self.monthly_budget > 0 else 0.0

        # Days left in month
        year, mon = int(month[:4]), int(month[5:7])
        import calendar
        _, days_in_month = calendar.monthrange(year, mon)
        today = date.today()
        if today.year == year and today.month == mon:
            days_left = days_in_month - today.day
        else:
            days_left = 0

        return {
            "month":              month,
            "total_spent":        total,
            "by_category":        by_category,
            "budget_limit":       self.monthly_budget,
            "remaining":          remaining,
            "percentage_used":    pct,
            "days_left_in_month": days_left,
        }

    def _get_category_spent(self, category: str, month: str) -> float:
        """Sum transactions for category in month."""
        txns = self.memory.get_transactions_for_month(month)
        return sum(t["amount"] for t in txns if t["category"] == category)

    # ── Budget alerts ─────────────────────────────────────────────────────────

    def check_budget_alerts(self, month: Optional[str] = None) -> list[dict]:
        """
        Return list of alert dicts for categories near or over budget.

        Alert levels: "warning" (≥70%), "danger" (≥90%), "over" (>100%)
        """
        month = month or date.today().strftime("%Y-%m")
        txns = self.memory.get_transactions_for_month(month)

        spent_by_cat: dict[str, float] = {}
        for t in txns:
            cat = t["category"]
            spent_by_cat[cat] = spent_by_cat.get(cat, 0.0) + t["amount"]

        alerts = []
        for cat, limit in self.category_budgets.items():
            if limit <= 0:
                continue
            spent = spent_by_cat.get(cat, 0.0)
            pct = spent / limit
            if pct > 1.0:
                level = "over"
            elif pct >= 0.90:
                level = "danger"
            elif pct >= self.warning_threshold:
                level = "warning"
            else:
                continue
            alerts.append({
                "category":   cat,
                "spent":      round(spent, 2),
                "limit":      limit,
                "percentage": round(pct * 100, 1),
                "level":      level,
                "message":    self._alert_message(cat, spent, limit, level),
            })
        return sorted(alerts, key=lambda a: a["percentage"], reverse=True)

    def _alert_message(self, cat: str, spent: float, limit: float, level: str) -> str:
        if level == "over":
            return f"BUDGET {cat.upper()} SUPERATO: €{spent:.0f}/€{limit:.0f} (+€{spent-limit:.0f})"
        elif level == "danger":
            return f"Budget {cat} quasi esaurito: €{spent:.0f}/€{limit:.0f} ({spent/limit*100:.0f}%)"
        else:
            return f"Attenzione budget {cat}: €{spent:.0f}/€{limit:.0f} ({spent/limit*100:.0f}%)"

    # ── Insights ─────────────────────────────────────────────────────────────

    def get_spending_insights(self, month: Optional[str] = None) -> str:
        """Return a natural-language analysis of spending patterns."""
        summary = self.get_monthly_summary(month)
        alerts = self.check_budget_alerts(month or date.today().strftime("%Y-%m"))
        lines = [f"Analisi spese {summary['month']}:"]

        # Top spending category
        by_cat = summary["by_category"]
        if by_cat:
            top_cat = max(by_cat, key=by_cat.get)
            lines.append(
                f"• Categoria principale: {top_cat} (€{by_cat[top_cat]:.0f})"
            )

        # Overall budget
        lines.append(
            f"• Totale: €{summary['total_spent']:.0f}/€{summary['budget_limit']:.0f} "
            f"({summary['percentage_used']:.0f}%) — rimangono €{summary['remaining']:.0f}"
        )

        # Days left projection
        days_left = summary["days_left_in_month"]
        if days_left > 0 and summary["total_spent"] > 0:
            today_day = date.today().day
            daily_avg = summary["total_spent"] / today_day if today_day > 0 else 0
            projected = summary["total_spent"] + daily_avg * days_left
            lines.append(
                f"• Proiezione fine mese: €{projected:.0f} "
                f"({'SOPRA' if projected > summary['budget_limit'] else 'sotto'} budget)"
            )

        # Alerts
        for a in alerts[:2]:
            lines.append(f"• ⚠ {a['message']}")

        return "\n".join(lines)
