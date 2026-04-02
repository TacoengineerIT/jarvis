"""
jarvis_market_impact_predictor.py — Rule-based market impact predictions
from geopolitical tension events.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("jarvis.market")

# ── Impact tables ─────────────────────────────────────────────────────────────
# Each entry: (direction, low_pct, high_pct, note)

_STOCK_INDEX_IMPACTS: dict[str, dict] = {
    "military": {
        "S&P 500":  ("bearish", -3.0, -5.0),
        "DAX":      ("bearish", -2.0, -4.0),
        "FTSE 100": ("bearish", -1.5, -3.0),
        "Shanghai": ("bearish", -2.0, -4.0),
        "Nikkei":   ("bearish", -2.5, -4.5),
    },
    "trade": {
        "S&P 500":  ("bearish", -1.5, -3.0),
        "DAX":      ("bearish", -2.0, -3.5),
        "FTSE 100": ("bearish", -1.0, -2.0),
        "Shanghai": ("bearish", -3.0, -5.0),
        "Nikkei":   ("bearish", -1.5, -3.0),
    },
    "diplomatic": {
        "S&P 500":  ("bearish", -0.5, -1.5),
        "DAX":      ("bearish", -0.5, -1.5),
        "FTSE 100": ("bearish", -0.5, -1.0),
        "Shanghai": ("bearish", -1.0, -2.0),
        "Nikkei":   ("bearish", -0.5, -1.5),
    },
    "economic_sanctions": {
        "S&P 500":  ("mixed",   -1.0, -2.0),
        "DAX":      ("bearish", -1.5, -3.0),
        "FTSE 100": ("bearish", -0.5, -1.5),
        "Shanghai": ("bearish", -1.0, -2.5),
        "Nikkei":   ("mixed",   -0.5, -1.5),
    },
}

_COMMODITY_IMPACTS: dict[str, dict] = {
    "military": {
        "Oil (WTI)": ("bullish", +2.0, +6.0),
        "Gold":      ("bullish", +1.5, +3.0),
        "Wheat":     ("bullish", +1.0, +3.0),
        "Copper":    ("bearish", -1.0, -2.5),
    },
    "trade": {
        "Oil (WTI)": ("mixed",   -1.0, +1.0),
        "Gold":      ("bullish", +0.5, +1.5),
        "Wheat":     ("bearish", -0.5, -1.5),
        "Copper":    ("bearish", -2.0, -4.0),
    },
    "diplomatic": {
        "Oil (WTI)": ("bullish", +0.5, +1.5),
        "Gold":      ("bullish", +0.5, +1.0),
        "Wheat":     ("neutral", 0.0,  +0.5),
        "Copper":    ("bearish", -0.5, -1.0),
    },
    "economic_sanctions": {
        "Oil (WTI)": ("bullish", +3.0, +8.0),
        "Gold":      ("bullish", +1.5, +3.0),
        "Wheat":     ("bullish", +2.0, +5.0),
        "Copper":    ("mixed",   -1.0, +1.0),
    },
}

_FOREX_IMPACTS: dict[str, dict] = {
    "military": {
        "USD":    ("bullish", +0.3, +1.0),
        "EUR":    ("bearish", -0.5, -1.5),
        "JPY":    ("bullish", +0.5, +1.5),  # safe haven
        "CHF":    ("bullish", +0.5, +1.5),  # safe haven
        "GBP":    ("bearish", -0.3, -1.0),
        "CNY":    ("bearish", -0.5, -1.5),
    },
    "trade": {
        "USD":    ("bullish", +0.2, +0.8),
        "EUR":    ("bearish", -0.3, -1.0),
        "JPY":    ("bullish", +0.2, +0.8),
        "CNY":    ("bearish", -0.5, -2.0),
        "GBP":    ("bearish", -0.2, -0.8),
    },
    "diplomatic": {
        "USD":    ("bullish", +0.1, +0.5),
        "EUR":    ("bearish", -0.2, -0.5),
        "JPY":    ("bullish", +0.1, +0.5),
    },
    "economic_sanctions": {
        "USD":    ("bullish", +0.3, +1.0),
        "EUR":    ("bearish", -0.5, -1.5),
        "RUB":    ("bearish", -3.0, -10.0),
        "CNY":    ("mixed",   -0.5, +0.2),
    },
}

_SECTOR_IMPACTS: dict[str, list[dict]] = {
    "military": [
        {"sector": "Defense",    "impact": "bullish",  "magnitude": 12, "trigger": "increased spending"},
        {"sector": "Energy",     "impact": "bullish",  "magnitude":  6, "trigger": "supply risk premium"},
        {"sector": "Tech",       "impact": "bearish",  "magnitude":  5, "trigger": "supply chain risk"},
        {"sector": "Airlines",   "impact": "bearish",  "magnitude":  8, "trigger": "fuel costs + demand"},
        {"sector": "Tourism",    "impact": "bearish",  "magnitude": 10, "trigger": "safety concerns"},
        {"sector": "Financials", "impact": "bearish",  "magnitude":  4, "trigger": "volatility premium"},
    ],
    "trade": [
        {"sector": "Tech",        "impact": "bearish", "magnitude": 10, "trigger": "supply chain disruption"},
        {"sector": "Autos",       "impact": "bearish", "magnitude": 12, "trigger": "tariffs on parts"},
        {"sector": "Agriculture", "impact": "bearish", "magnitude":  8, "trigger": "export restrictions"},
        {"sector": "Consumer",    "impact": "bearish", "magnitude":  5, "trigger": "price inflation"},
        {"sector": "Financials",  "impact": "bearish", "magnitude":  3, "trigger": "volatility headwind"},
        {"sector": "Industrials", "impact": "bearish", "magnitude":  6, "trigger": "supply chain costs"},
    ],
    "diplomatic": [
        {"sector": "Financials", "impact": "bearish", "magnitude": 3, "trigger": "uncertainty premium"},
        {"sector": "Tech",       "impact": "bearish", "magnitude": 2, "trigger": "regulatory risk"},
    ],
    "economic_sanctions": [
        {"sector": "Energy",     "impact": "bullish", "magnitude":  8, "trigger": "supply reduction"},
        {"sector": "Defense",    "impact": "bullish", "magnitude":  5, "trigger": "military support"},
        {"sector": "Tech",       "impact": "bearish", "magnitude":  6, "trigger": "export restrictions"},
        {"sector": "Banks",      "impact": "bearish", "magnitude":  4, "trigger": "exposure risk"},
    ],
}

_VOLATILITY_VIX: dict[str, tuple[int, int]] = {
    "military":           (22, 40),
    "trade":              (18, 28),
    "diplomatic":         (15, 22),
    "economic_sanctions": (18, 30),
}

_TIMELINE_TEMPLATES: dict[str, dict] = {
    "military": {
        "immediate":   "Stocks -2 to -5% at open; Oil +3-6%",
        "short_term":  "Continued pressure if escalation; Defense +10-15%",
        "medium_term": "Supply chain disruptions; inflation rising",
        "long_term":   "Structural realignment; defense budgets raised",
    },
    "trade": {
        "immediate":   "Affected sectors -2 to -4% at open",
        "short_term":  "Corporate guidance warnings; earnings revisions",
        "medium_term": "Supply chain relocation costs; consumer price rises",
        "long_term":   "Structural trade route changes; reduced global growth",
    },
    "diplomatic": {
        "immediate":   "Market wobble -0.5 to -1.5%",
        "short_term":  "Watch for escalation to sanctions or military",
        "medium_term": "Bilateral trade chill; visa restrictions",
        "long_term":   "Rebalancing of alliances",
    },
    "economic_sanctions": {
        "immediate":   "Energy +3-8%; target country currency -5 to -15%",
        "short_term":  "Commodity supply squeeze; inflation in affected region",
        "medium_term": "Global supply chain rerouting; stagflation risk",
        "long_term":   "Dollar weaponization accelerates de-dollarization",
    },
}


def _confidence(tension_score: float, n_articles: int) -> float:
    """Higher score + more corroborating articles → higher confidence."""
    base = min(tension_score / 10.0, 1.0)
    article_boost = min(n_articles * 0.05, 0.25)
    return round(min(base + article_boost, 0.95), 2)


class MarketImpactPredictor:
    """Rule-based market impact predictions from tension events."""

    def predict_market_moves(self, tension_event: dict) -> dict:
        """
        Full market prediction for a tension event.

        Returns:
        {
            stocks, commodities, forex, vix_range,
            impact_direction, confidence, timeline, created_at
        }
        """
        t_type = tension_event.get("tension_type", "diplomatic")
        t_score = tension_event.get("tension_score", 5.0)
        n_arts = len(tension_event.get("articles", []))

        # Scale magnitudes by tension score (0-10 → factor 0.5-1.5)
        scale = 0.5 + (t_score / 10.0)

        stocks = {
            idx: {
                "direction": d,
                "range_pct": (round(lo * scale, 1), round(hi * scale, 1)),
            }
            for idx, (d, lo, hi) in _STOCK_INDEX_IMPACTS.get(t_type, {}).items()
        }
        commodities = {
            c: {
                "direction": d,
                "range_pct": (round(lo * scale, 1), round(hi * scale, 1)),
            }
            for c, (d, lo, hi) in _COMMODITY_IMPACTS.get(t_type, {}).items()
        }
        forex = {
            pair: {
                "direction": d,
                "range_pct": (round(lo * scale, 1), round(hi * scale, 1)),
            }
            for pair, (d, lo, hi) in _FOREX_IMPACTS.get(t_type, {}).items()
        }

        vix_lo, vix_hi = _VOLATILITY_VIX.get(t_type, (15, 20))
        vix_range = (
            int(vix_lo + (t_score / 10) * 5),
            int(vix_hi + (t_score / 10) * 10),
        )

        # Overall direction: bearish if any stock index is bearish
        stock_dirs = [v["direction"] for v in stocks.values()]
        if stock_dirs.count("bearish") >= len(stock_dirs) // 2:
            overall = "bearish"
        elif stock_dirs.count("bullish") > len(stock_dirs) // 2:
            overall = "bullish"
        else:
            overall = "mixed"

        return {
            "stocks":           stocks,
            "commodities":      commodities,
            "forex":            forex,
            "vix_range":        vix_range,
            "impact_direction": overall,
            "confidence":       _confidence(t_score, n_arts),
            "timeline":         _TIMELINE_TEMPLATES.get(t_type, {}),
            "created_at":       datetime.now(timezone.utc).isoformat(),
        }

    def map_sector_impact(self, tension_type: str) -> list[dict]:
        """Return ordered list of affected sectors for a tension type."""
        sectors = _SECTOR_IMPACTS.get(tension_type, [])
        return sorted(sectors, key=lambda s: s["magnitude"], reverse=True)

    def estimate_timeline(self, tension_type: str) -> dict:
        """Return timeline template for tension type."""
        return _TIMELINE_TEMPLATES.get(tension_type, {
            "immediate":   "Market reaction within hours",
            "short_term":  "Monitor over 1-2 weeks",
            "medium_term": "Watch for 1-3 months",
            "long_term":   "Structural changes over 6-12 months",
        })

    def rank_affected_sectors(self, tension_event: dict) -> list[dict]:
        """
        Priority-ordered affected sectors for a tension event.
        Filters by direction if tension is bearish vs escalating.
        """
        t_type = tension_event.get("tension_type", "diplomatic")
        sectors = self.map_sector_impact(t_type)
        t_score = tension_event.get("tension_score", 5.0)
        # Scale magnitude
        scale = 0.5 + t_score / 10.0
        return [
            {**s, "magnitude": round(s["magnitude"] * scale, 1)}
            for s in sectors
        ]
