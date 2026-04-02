"""
jarvis_tension_analyzer.py — Geopolitical tension scoring from news articles.
Produces tension events with numeric scores, trends, and duration estimates.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("jarvis.tension")

# ── Keyword score tables ──────────────────────────────────────────────────────

_TENSION_KEYWORDS: dict[str, list[tuple[str, float]]] = {
    "military": [
        ("war", 3.0), ("nuclear", 3.5), ("invasion", 3.0), ("troops deployed", 2.5),
        ("military", 1.5), ("missile", 2.0), ("airstrike", 2.5), ("battle", 2.0),
        ("offensive", 2.0), ("bombardment", 2.5), ("attack", 1.5), ("warship", 2.0),
        ("carrier group", 2.0), ("troops", 1.0), ("combat", 1.5), ("casualties", 2.0),
        ("siege", 2.5), ("blockade", 2.0), ("proxy war", 2.0),
    ],
    "trade": [
        ("trade war", 3.0), ("tariff", 2.0), ("sanction", 2.5), ("embargo", 2.5),
        ("export ban", 2.0), ("import restriction", 1.5), ("trade dispute", 2.0),
        ("economic coercion", 2.5), ("decoupling", 2.0), ("supply chain", 1.0),
        ("wto", 1.5), ("trade deficit", 1.0), ("retaliatory", 2.0),
    ],
    "diplomatic": [
        ("expelled", 2.5), ("ambassador recalled", 3.0), ("diplomatic crisis", 3.0),
        ("broke off relations", 3.0), ("espionage", 2.0), ("spy", 1.5),
        ("diplomatic incident", 2.0), ("protest", 1.0), ("strongly condemns", 1.5),
        ("hostile", 1.5), ("provocation", 2.0), ("ultimatum", 3.0),
    ],
    "economic_sanctions": [
        ("sanctions", 2.5), ("financial sanctions", 3.0), ("swift", 2.0),
        ("asset freeze", 2.5), ("travel ban", 1.5), ("arms embargo", 2.5),
        ("oil embargo", 3.0), ("cut off", 2.0), ("isolated", 1.5),
    ],
}

_APPEASEMENT_KEYWORDS: list[tuple[str, float]] = [
    ("ceasefire", 3.0), ("peace agreement", 3.5), ("peace deal", 3.5),
    ("peace talks", 2.5), ("negotiation", 2.0), ("diplomatic breakthrough", 3.0),
    ("withdraw troops", 2.5), ("summit", 2.0), ("agreement signed", 3.0),
    ("de-escalation", 3.0), ("truce", 3.0), ("reconciliation", 2.5),
    ("normalization", 2.5), ("joint statement", 1.5), ("goodwill", 1.5),
    ("prisoner exchange", 2.0), ("humanitarian corridor", 2.0),
]

# country → region mapping for impact assessment
REGION_MAP = {
    "middle east": ["israel", "iran", "saudi", "lebanon", "yemen", "iraq", "syria"],
    "east asia":   ["china", "taiwan", "north korea", "south korea", "japan"],
    "europe":      ["russia", "ukraine", "nato", "eu", "germany", "france", "poland", "uk", "britain"],
    "south asia":  ["india", "pakistan", "afghanistan"],
    "americas":    ["usa", "united states", "america"],
}


def _score_text(text: str, keyword_table: list[tuple[str, float]]) -> float:
    """Sum weights of matched keywords in text (capped at 10)."""
    text = text.lower()
    total = sum(w for kw, w in keyword_table if kw in text)
    return min(total, 10.0)


def _tension_type_scores(text: str) -> dict[str, float]:
    """Return per-type raw scores for a piece of text."""
    return {
        t: _score_text(text, kws)
        for t, kws in _TENSION_KEYWORDS.items()
    }


class TensionAnalyzer:
    """
    Analyses a list of news articles to detect geopolitical tensions,
    score them (0-10), and predict their trajectory.
    """

    def detect_geopolitical_tensions(self, articles: list[dict]) -> list[dict]:
        """
        Cluster articles into tension events and score each.

        Returns list of tension dicts:
        {
            tension_type, countries_involved, tension_score,
            appeasement_score, trend, duration_estimate_days,
            impact_assessment, articles (titles), created_at
        }
        """
        if not articles:
            return []

        # Group articles by dominant tension type and country cluster
        clusters: dict[str, list[dict]] = {}
        for art in articles:
            raw = f"{art.get('title','')} {art.get('content','')}".lower()
            t_scores = _tension_type_scores(raw)
            dominant = max(t_scores, key=t_scores.get)
            if t_scores[dominant] < 0.5:
                dominant = "diplomatic"  # default bucket
            # Bucket key: type + first mentioned country
            countries = art.get("countries", [])
            bucket = f"{dominant}:{countries[0] if countries else 'global'}"
            clusters.setdefault(bucket, []).append(art)

        tensions = []
        for bucket, arts in clusters.items():
            tension_type = bucket.split(":")[0]
            combined_text = " ".join(
                f"{a.get('title','')} {a.get('content','')}" for a in arts
            )
            all_countries = list({c for a in arts for c in a.get("countries", [])})

            t_score = min(
                _score_text(combined_text,
                            [kw for kws in _TENSION_KEYWORDS.values() for kw in kws]),
                10.0,
            )
            a_score = min(_score_text(combined_text, _APPEASEMENT_KEYWORDS), 10.0)

            trend_data = self.predict_tension_trajectory({
                "tension_score": t_score,
                "appeasement_score": a_score,
                "tension_type": tension_type,
                "text": combined_text,
            })

            tensions.append({
                "tension_type": tension_type,
                "countries_involved": all_countries[:6],
                "tension_score": round(t_score, 2),
                "appeasement_score": round(a_score, 2),
                "trend": trend_data["trend"],
                "duration_estimate_days": trend_data["duration_estimate_days"],
                "impact_assessment": self._summarize_impact(
                    tension_type, t_score, all_countries
                ),
                "articles": [a.get("title", "") for a in arts[:3]],
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

        tensions.sort(key=lambda t: t["tension_score"], reverse=True)
        return tensions

    def assess_appeasement_trends(self, articles: list[dict]) -> list[dict]:
        """
        Identify positive/appeasement signals in articles.
        Returns list of appeasement events with score and description.
        """
        results = []
        for art in articles:
            raw = f"{art.get('title','')} {art.get('content','')}".lower()
            score = _score_text(raw, _APPEASEMENT_KEYWORDS)
            if score >= 2.0:
                results.append({
                    "title": art.get("title", ""),
                    "source": art.get("source", ""),
                    "appeasement_score": round(score, 2),
                    "countries": art.get("countries", []),
                    "published_at": art.get("published_at"),
                })
        results.sort(key=lambda r: r["appeasement_score"], reverse=True)
        return results

    def predict_tension_trajectory(self, tension_data: dict) -> dict:
        """
        Predict trend and duration from tension + appeasement scores.
        """
        t = tension_data.get("tension_score", 0)
        a = tension_data.get("appeasement_score", 0)
        text = tension_data.get("text", "").lower()

        # Trend
        if a >= t * 0.7:
            trend = "de-escalating"
        elif t >= 7 or (t > a + 3):
            trend = "escalating"
        else:
            trend = "stable"

        # Duration estimate
        t_type = tension_data.get("tension_type", "diplomatic")
        base_duration = {"military": 90, "trade": 180, "diplomatic": 30, "economic_sanctions": 120}
        duration = base_duration.get(t_type, 60)
        if trend == "escalating":
            duration = int(duration * 1.5)
        elif trend == "de-escalating":
            duration = int(duration * 0.5)

        # Historical precedents
        precedents = self._find_precedents(t_type, t)

        return {
            "trend": trend,
            "duration_estimate_days": duration,
            "precedents": precedents,
        }

    def quantify_global_risk(self, tensions: list[dict]) -> dict:
        """
        Aggregate tension index (0-100), major hotspots, contagion risk.
        """
        if not tensions:
            return {
                "global_tension_index": 0,
                "hotspots": [],
                "contagion_risk": 0.0,
                "assessment": "Situazione globale stabile.",
            }

        scores = [t["tension_score"] for t in tensions]
        avg = sum(scores) / len(scores)
        global_index = min(int(avg * 10), 100)

        hotspots = [
            {"countries": t["countries_involved"], "score": t["tension_score"],
             "type": t["tension_type"]}
            for t in tensions[:3]
        ]

        # Contagion: high if multiple high-tension events near same region
        high_tension = [t for t in tensions if t["tension_score"] >= 6]
        contagion = min(len(high_tension) * 0.15, 1.0)

        if global_index >= 70:
            assessment = "Rischio geopolitico ALTO. Mercati sotto pressione."
        elif global_index >= 40:
            assessment = "Rischio moderato. Monitorare sviluppi."
        else:
            assessment = "Rischio basso. Situazione relativamente stabile."

        return {
            "global_tension_index": global_index,
            "hotspots": hotspots,
            "contagion_risk": round(contagion, 2),
            "assessment": assessment,
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _summarize_impact(
        self, tension_type: str, score: float, countries: list[str]
    ) -> str:
        country_str = ", ".join(countries[:3]) if countries else "regione interessata"
        level = "bassa" if score < 4 else "moderata" if score < 7 else "alta"
        type_labels = {
            "military": "conflitto militare",
            "trade": "guerra commerciale",
            "diplomatic": "crisi diplomatica",
            "economic_sanctions": "sanzioni economiche",
        }
        label = type_labels.get(tension_type, "tensione geopolitica")
        return (
            f"Tensione {level} ({label}) tra {country_str}. "
            f"Score: {score:.1f}/10."
        )

    def _find_precedents(self, tension_type: str, score: float) -> list[str]:
        _PRECEDENTS = {
            "military": [
                ("2022 Russian invasion of Ukraine", 9.0),
                ("2003 Iraq War", 8.0),
                ("2008 Russia-Georgia war", 7.0),
                ("2006 Israel-Lebanon conflict", 6.0),
            ],
            "trade": [
                ("2018-2020 US-China trade war", 7.0),
                ("2002 US steel tariffs", 4.0),
                ("1930 Smoot-Hawley Tariff Act", 8.0),
            ],
            "diplomatic": [
                ("2022 Russia-West relations breakdown", 8.0),
                ("2001 US-China spy plane incident", 5.0),
                ("2018 Salisbury poisoning crisis", 6.0),
            ],
            "economic_sanctions": [
                ("2022 Russia SWIFT exclusion", 9.0),
                ("2012 Iran nuclear sanctions", 7.0),
                ("2014 Crimea annexation sanctions", 6.0),
            ],
        }
        candidates = _PRECEDENTS.get(tension_type, [])
        # Return closest matches by score proximity
        ranked = sorted(candidates, key=lambda p: abs(p[1] - score))
        return [p[0] for p in ranked[:2]]
