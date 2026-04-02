"""
jarvis_social_impact_analyzer.py — Social and economic impact assessment
from geopolitical tension events.
"""
import logging
from datetime import datetime, timezone

logger = logging.getLogger("jarvis.social")

# ── Impact tables ─────────────────────────────────────────────────────────────

_EMPLOYMENT_TABLE: dict[str, dict] = {
    "military": {
        "direction": "mixed",
        "magnitude_pct": 0.8,
        "positive_sectors": ["Defense", "Manufacturing (arms)", "Government"],
        "negative_sectors": ["Tourism", "Airlines", "Hospitality"],
        "duration_months": 12,
        "recovery_likelihood": 0.6,
        "note": "Defense hiring offsets civilian job losses",
    },
    "trade": {
        "direction": "negative",
        "magnitude_pct": 1.5,
        "positive_sectors": [],
        "negative_sectors": ["Agriculture", "Manufacturing", "Tech"],
        "duration_months": 18,
        "recovery_likelihood": 0.7,
        "note": "Export sector job losses; retaliatory tariff impact",
    },
    "diplomatic": {
        "direction": "neutral",
        "magnitude_pct": 0.2,
        "positive_sectors": [],
        "negative_sectors": [],
        "duration_months": 3,
        "recovery_likelihood": 0.9,
        "note": "Minimal direct employment impact unless escalates",
    },
    "economic_sanctions": {
        "direction": "negative",
        "magnitude_pct": 2.0,
        "positive_sectors": ["Defense", "Domestic substitutes"],
        "negative_sectors": ["Energy", "Finance", "Import-dependent sectors"],
        "duration_months": 24,
        "recovery_likelihood": 0.5,
        "note": "Target economy severely impacted; secondary effects on others",
    },
}

_INFLATION_TABLE: dict[str, dict] = {
    "military": {
        "direction": "accelerating",
        "magnitude_pct": 1.8,
        "sectors_hit": ["Energy", "Food", "Defense goods"],
        "duration_months": 9,
        "wage_pressure": True,
        "note": "Energy supply shock; food supply disruption if in grain region",
    },
    "trade": {
        "direction": "accelerating",
        "magnitude_pct": 1.2,
        "sectors_hit": ["Consumer goods", "Semiconductors", "Autos"],
        "duration_months": 12,
        "wage_pressure": False,
        "note": "Tariff pass-through to consumer prices; goods shortage",
    },
    "diplomatic": {
        "direction": "stable",
        "magnitude_pct": 0.2,
        "sectors_hit": [],
        "duration_months": 2,
        "wage_pressure": False,
        "note": "Minimal inflation impact unless escalates",
    },
    "economic_sanctions": {
        "direction": "accelerating",
        "magnitude_pct": 2.5,
        "sectors_hit": ["Energy", "Food", "Raw materials"],
        "duration_months": 18,
        "wage_pressure": True,
        "note": "Commodity supply reduction drives broad inflation",
    },
}

_MIGRATION_RISK_TABLE: dict[str, dict] = {
    "military": {
        "risk_level": 0.8,
        "estimated_displaced": "hundreds of thousands to millions",
        "destination_regions": ["Europe", "Neighboring countries", "USA"],
        "note": "Direct displacement from conflict zones",
    },
    "trade": {
        "risk_level": 0.2,
        "estimated_displaced": "minimal",
        "destination_regions": [],
        "note": "Low direct migration; possible economic migration long-term",
    },
    "diplomatic": {
        "risk_level": 0.1,
        "estimated_displaced": "negligible",
        "destination_regions": [],
        "note": "Visa restrictions possible; no mass migration",
    },
    "economic_sanctions": {
        "risk_level": 0.5,
        "estimated_displaced": "tens of thousands",
        "destination_regions": ["Europe", "Neighboring countries"],
        "note": "Economic hardship drives emigration from sanctioned country",
    },
}

_SUPPLY_CHAIN_TABLE: dict[str, dict] = {
    "military": {
        "disruption_risk": 0.8,
        "critical_routes": ["Suez Canal", "Strait of Hormuz", "Taiwan Strait"],
        "affected_goods": ["Energy", "Semiconductors", "Agricultural products"],
        "severity": "high",
        "recovery_timeline_months": 6,
    },
    "trade": {
        "disruption_risk": 0.6,
        "critical_routes": ["Trans-Pacific", "Trans-Atlantic"],
        "affected_goods": ["Manufactured goods", "Tech components", "Autos"],
        "severity": "medium",
        "recovery_timeline_months": 12,
    },
    "diplomatic": {
        "disruption_risk": 0.2,
        "critical_routes": [],
        "affected_goods": [],
        "severity": "low",
        "recovery_timeline_months": 2,
    },
    "economic_sanctions": {
        "disruption_risk": 0.7,
        "critical_routes": ["Energy pipelines", "Shipping lanes"],
        "affected_goods": ["Oil & gas", "Wheat", "Fertilizers"],
        "severity": "high",
        "recovery_timeline_months": 18,
    },
}


class SocialImpactAnalyzer:
    """Assesses social, employment, inflation, migration, and supply chain
    effects from geopolitical tension events."""

    def assess_employment_impact(self, tension_event: dict) -> dict:
        t_type = tension_event.get("tension_type", "diplomatic")
        t_score = tension_event.get("tension_score", 5.0)
        base = _EMPLOYMENT_TABLE.get(t_type, _EMPLOYMENT_TABLE["diplomatic"])

        scale = t_score / 10.0
        magnitude = round(base["magnitude_pct"] * scale, 2)

        return {
            "direction": base["direction"],
            "magnitude_pct_unemployment_change": magnitude,
            "positive_sectors": base["positive_sectors"],
            "negative_sectors": base["negative_sectors"],
            "affected_sectors": base["negative_sectors"],
            "duration_months": base["duration_months"],
            "recovery_likelihood": base["recovery_likelihood"],
            "note": base["note"],
        }

    def assess_inflation_impact(self, tension_event: dict) -> dict:
        t_type = tension_event.get("tension_type", "diplomatic")
        t_score = tension_event.get("tension_score", 5.0)
        base = _INFLATION_TABLE.get(t_type, _INFLATION_TABLE["diplomatic"])

        scale = t_score / 10.0
        magnitude = round(base["magnitude_pct"] * scale, 2)

        return {
            "direction": base["direction"],
            "magnitude_pct": magnitude,
            "sectors_hit": base["sectors_hit"],
            "duration_months": base["duration_months"],
            "wage_pressure": base["wage_pressure"],
            "note": base["note"],
        }

    def assess_migration_risk(self, tension_event: dict) -> dict:
        t_type = tension_event.get("tension_type", "diplomatic")
        t_score = tension_event.get("tension_score", 5.0)
        base = _MIGRATION_RISK_TABLE.get(t_type, _MIGRATION_RISK_TABLE["diplomatic"])
        countries = tension_event.get("countries_involved", [])

        scale = t_score / 10.0
        risk_level = round(min(base["risk_level"] * (0.5 + scale), 1.0), 2)

        return {
            "risk_level": risk_level,
            "origin_countries": countries[:3],
            "destination_regions": base["destination_regions"],
            "estimated_displaced": base["estimated_displaced"],
            "note": base["note"],
        }

    def assess_supply_chain_disruption(self, tension_event: dict) -> dict:
        t_type = tension_event.get("tension_type", "diplomatic")
        t_score = tension_event.get("tension_score", 5.0)
        base = _SUPPLY_CHAIN_TABLE.get(t_type, _SUPPLY_CHAIN_TABLE["diplomatic"])
        countries = tension_event.get("countries_involved", [])

        scale = t_score / 10.0
        disruption_risk = round(min(base["disruption_risk"] * (0.5 + scale), 1.0), 2)

        return {
            "disruption_risk": disruption_risk,
            "severity": base["severity"],
            "critical_routes": base["critical_routes"],
            "affected_goods": base["affected_goods"],
            "recovery_timeline_months": base["recovery_timeline_months"],
            "countries_involved": countries[:3],
        }

    def full_assessment(self, tension_event: dict) -> dict:
        """Run all four assessments and return a combined dict."""
        return {
            "employment":    self.assess_employment_impact(tension_event),
            "inflation":     self.assess_inflation_impact(tension_event),
            "migration":     self.assess_migration_risk(tension_event),
            "supply_chain":  self.assess_supply_chain_disruption(tension_event),
            "assessed_at":   datetime.now(timezone.utc).isoformat(),
        }
