"""
jarvis_morning_briefing.py — Daily geopolitical + market briefing generator.

Flow:
  1. Scrape overnight news (NewsScraper)
  2. Detect tensions (TensionAnalyzer)
  3. Predict market impact (MarketImpactPredictor)
  4. Assess social impact (SocialImpactAnalyzer)
  5. Format natural-language briefing
  6. Save to DB (JarvisMemory)
"""
import json
import logging
from datetime import date, datetime, timezone
from typing import Optional

logger = logging.getLogger("jarvis.briefing")

_RISK_EMOJI = {
    "escalating":    "🔴",
    "stable":        "🟡",
    "de-escalating": "🟢",
    "neutral":       "⚪",
    "mixed":         "🟠",
}

_TREND_IT = {
    "escalating":    "In escalation",
    "stable":        "Stabile",
    "de-escalating": "In de-escalazione",
    "neutral":       "Neutro",
    "mixed":         "Misto",
}


class MorningBriefingGenerator:
    """
    Orchestrates news scraping, tension analysis, market + social prediction,
    and formats a daily morning briefing for JARVIS.
    """

    def __init__(
        self,
        news_scraper=None,
        tension_analyzer=None,
        market_predictor=None,
        social_analyzer=None,
        memory=None,
    ):
        # Lazy imports to keep module importable even without optional deps
        if news_scraper is None:
            from jarvis_news_scraper import NewsScraper
            news_scraper = NewsScraper()
        if tension_analyzer is None:
            from jarvis_tension_analyzer import TensionAnalyzer
            tension_analyzer = TensionAnalyzer()
        if market_predictor is None:
            from jarvis_market_impact_predictor import MarketImpactPredictor
            market_predictor = MarketImpactPredictor()
        if social_analyzer is None:
            from jarvis_social_impact_analyzer import SocialImpactAnalyzer
            social_analyzer = SocialImpactAnalyzer()
        if memory is None:
            from jarvis_memory import JarvisMemory
            memory = JarvisMemory()

        self.news = news_scraper
        self.tension = tension_analyzer
        self.market = market_predictor
        self.social = social_analyzer
        self.memory = memory

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_daily_briefing(self) -> dict:
        """
        Full pipeline: scrape → analyse → predict → format → save.
        Returns briefing dict with keys:
          date, briefing_text, key_tensions, market_impacts,
          social_impacts, actionable_items, confidence
        """
        today = date.today().isoformat()
        logger.info("[BRIEFING] Generating daily briefing for %s", today)

        # 1. Scrape news
        try:
            articles = self.news.scrape_morning_news()
        except Exception as e:
            logger.error("[BRIEFING] News scrape failed: %s", e)
            articles = []

        # 2. Detect tensions
        tensions = self.tension.detect_geopolitical_tensions(articles)
        global_risk = self.tension.quantify_global_risk(tensions)

        # 3. Market + social predictions (top 3 tensions)
        market_impacts = []
        social_impacts = []
        for t in tensions[:3]:
            try:
                market_impacts.append({
                    "tension": t,
                    "market": self.market.predict_market_moves(t),
                    "sectors": self.market.rank_affected_sectors(t),
                })
            except Exception as e:
                logger.warning("[BRIEFING] Market prediction error: %s", e)

            try:
                social_impacts.append({
                    "tension": t,
                    "social": self.social.full_assessment(t),
                })
            except Exception as e:
                logger.warning("[BRIEFING] Social prediction error: %s", e)

        # 4. Format text
        briefing_text = self.format_briefing({
            "tensions":       tensions[:5],
            "global_risk":    global_risk,
            "market_impacts": market_impacts,
            "social_impacts": social_impacts,
            "n_articles":     len(articles),
        })

        # 5. Confidence
        confidence = self._overall_confidence(tensions, len(articles))

        # 6. Actionable items
        actionable = self._generate_actionable(tensions[:3], market_impacts)

        result = {
            "date":            today,
            "generated_at":    datetime.now(timezone.utc).isoformat(),
            "briefing_text":   briefing_text,
            "key_tensions":    tensions[:5],
            "market_impacts":  market_impacts,
            "social_impacts":  social_impacts,
            "actionable_items": actionable,
            "confidence":      confidence,
            "global_risk":     global_risk,
        }

        # 7. Persist
        try:
            self.memory.save_morning_briefing(result)
        except Exception as e:
            logger.warning("[BRIEFING] Could not save to DB: %s", e)

        logger.info("[BRIEFING] Done. %d tensions, confidence=%.2f", len(tensions), confidence)
        return result

    def get_today_briefing(self) -> Optional[dict]:
        """Return today's saved briefing from DB, or generate a new one."""
        try:
            existing = self.memory.get_morning_briefing(date.today().isoformat())
            if existing:
                return existing
        except Exception:
            pass
        return self.generate_daily_briefing()

    def get_market_impacts(self) -> str:
        """Short text summary of today's market impacts for Sonnet context."""
        briefing = self.get_today_briefing()
        if not briefing:
            return "Nessun dato di mercato disponibile."
        impacts = briefing.get("market_impacts", [])
        if not impacts:
            return "Nessun impatto di mercato rilevante oggi."
        lines = []
        for mi in impacts[:2]:
            t = mi["tension"]
            m = mi["market"]
            lines.append(
                f"• {t.get('impact_assessment','?')} → "
                f"Mercati: {m.get('impact_direction','?')} "
                f"(confidenza {m.get('confidence',0)*100:.0f}%)"
            )
        return "\n".join(lines)

    # ── Formatting ────────────────────────────────────────────────────────────

    def format_briefing(self, data: dict) -> str:
        tensions       = data.get("tensions", [])
        global_risk    = data.get("global_risk", {})
        market_impacts = data.get("market_impacts", [])
        social_impacts = data.get("social_impacts", [])
        n_articles     = data.get("n_articles", 0)
        today_str      = date.today().strftime("%A %d %B %Y")

        lines = [
            f"🌅 Briefing mattutino — {today_str}",
            f"📰 Articoli analizzati: {n_articles}",
            "",
            "━" * 42,
            "SVILUPPI GEOPOLITICI",
            "━" * 42,
        ]

        if not tensions:
            lines.append("Nessuna tensione significativa rilevata.")
        else:
            for t in tensions[:5]:
                emoji = _RISK_EMOJI.get(t.get("trend", "neutral"), "⚪")
                trend_it = _TREND_IT.get(t.get("trend", "neutral"), t.get("trend", "?"))
                countries = ", ".join(t.get("countries_involved", [])[:3]) or "N/D"
                lines += [
                    "",
                    f"{emoji} {t.get('tension_type','?').upper()} — {countries}",
                    f"  Score tensione: {t.get('tension_score', 0):.1f}/10  |  "
                    f"Appeasement: {t.get('appeasement_score', 0):.1f}/10",
                    f"  Trend: {trend_it}  |  "
                    f"Durata stimata: ~{t.get('duration_estimate_days', '?')} giorni",
                    f"  {t.get('impact_assessment', '')}",
                ]
                arts = t.get("articles", [])
                if arts:
                    lines.append(f"  → {arts[0]}")

        lines += [
            "",
            "━" * 42,
            "IMPATTO SUI MERCATI",
            "━" * 42,
        ]

        if not market_impacts:
            lines.append("Nessun impatto significativo previsto.")
        else:
            mi = market_impacts[0]
            m = mi["market"]
            t = mi["tension"]
            lines.append(f"\nPer {t.get('tension_type','?').upper()} "
                         f"(score {t.get('tension_score',0):.1f}/10):")

            stocks = m.get("stocks", {})
            if stocks:
                lines.append("\n📊 INDICI AZIONARI:")
                for idx, v in list(stocks.items())[:4]:
                    lo, hi = v.get("range_pct", (0, 0))
                    dir_arrow = "↑" if v["direction"] == "bullish" else "↓" if v["direction"] == "bearish" else "↔"
                    lines.append(f"  {dir_arrow} {idx}: {lo:+.1f}% / {hi:+.1f}%")

            comms = m.get("commodities", {})
            if comms:
                lines.append("\n⚫ MATERIE PRIME:")
                for c, v in comms.items():
                    lo, hi = v.get("range_pct", (0, 0))
                    dir_arrow = "↑" if v["direction"] == "bullish" else "↓" if v["direction"] == "bearish" else "↔"
                    lines.append(f"  {dir_arrow} {c}: {lo:+.1f}% / {hi:+.1f}%")

            forex = m.get("forex", {})
            if forex:
                lines.append("\n💱 VALUTE:")
                for pair, v in list(forex.items())[:4]:
                    lo, hi = v.get("range_pct", (0, 0))
                    dir_arrow = "↑" if v["direction"] == "bullish" else "↓" if v["direction"] == "bearish" else "↔"
                    lines.append(f"  {dir_arrow} {pair}: {lo:+.1f}% / {hi:+.1f}%")

            vix = m.get("vix_range", (15, 20))
            lines.append(f"\n📈 VIX atteso: {vix[0]}-{vix[1]}")

            sectors = mi.get("sectors", [])[:4]
            if sectors:
                lines.append("\n🏭 SETTORI:")
                for s in sectors:
                    arrow = "↑" if s["impact"] == "bullish" else "↓"
                    lines.append(
                        f"  {arrow} {s['sector']}: "
                        f"{'+' if s['impact']=='bullish' else '-'}{s['magnitude']:.0f}%"
                        f" ({s['trigger']})"
                    )

            tl = m.get("timeline", {})
            if tl:
                lines += [
                    "",
                    "⏱  TIMELINE:",
                    f"  Immediato:    {tl.get('immediate','')}",
                    f"  Breve termine: {tl.get('short_term','')}",
                    f"  Medio termine: {tl.get('medium_term','')}",
                ]

        lines += [
            "",
            "━" * 42,
            "IMPATTO SOCIALE",
            "━" * 42,
        ]

        if not social_impacts:
            lines.append("Nessun impatto sociale significativo.")
        else:
            si = social_impacts[0]["social"]
            emp = si.get("employment", {})
            inf = si.get("inflation", {})
            mig = si.get("migration", {})
            sc  = si.get("supply_chain", {})

            lines += [
                f"\n👨‍💼 OCCUPAZIONE: {emp.get('direction','?').upper()}"
                f" ({emp.get('magnitude_pct_unemployment_change',0):+.1f} pp)",
                f"   {emp.get('note','')}",
                f"\n💰 INFLAZIONE: {inf.get('direction','?').upper()}"
                f" (+{inf.get('magnitude_pct',0):.1f} pp CPI)",
                f"   Settori: {', '.join(inf.get('sectors_hit', [])[:3]) or 'N/D'}",
                f"\n🛫 MIGRAZIONE: rischio {mig.get('risk_level',0)*100:.0f}%",
                f"   {mig.get('note','')}",
                f"\n🚢 SUPPLY CHAIN: severità {sc.get('severity','?').upper()}"
                f" (rischio {sc.get('disruption_risk',0)*100:.0f}%)",
            ]

        # Global risk footer
        lines += [
            "",
            "━" * 42,
            f"🌍 INDICE RISCHIO GLOBALE: {global_risk.get('global_tension_index',0)}/100",
            f"   {global_risk.get('assessment','')}",
            "━" * 42,
        ]

        return "\n".join(lines)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _overall_confidence(self, tensions: list[dict], n_articles: int) -> float:
        if not tensions:
            return 0.3
        avg_score = sum(t.get("tension_score", 0) for t in tensions) / len(tensions)
        article_factor = min(n_articles / 20.0, 1.0)
        return round(min(0.4 + avg_score * 0.05 + article_factor * 0.2, 0.95), 2)

    def _generate_actionable(
        self, tensions: list[dict], market_impacts: list[dict]
    ) -> str:
        lines = ["📋 INTELLIGENCE OPERATIVA:"]
        if not tensions:
            lines.append("  ✅ Nessuna azione urgente consigliata.")
            return "\n".join(lines)

        top = tensions[0]
        t_type = top.get("tension_type", "")
        t_score = top.get("tension_score", 0)
        trend = top.get("trend", "stable")

        if t_score >= 7:
            lines.append("  ⚠️  Tensione ALTA — monitorare sviluppi quotidianamente")
        elif t_score >= 4:
            lines.append("  ℹ️  Tensione MODERATA — monitorare sviluppi settimanalmente")
        else:
            lines.append("  ✅ Tensione BASSA — nessuna azione immediata")

        if t_type == "military":
            lines += [
                "  ✅ Energia/Oro: posizionamento difensivo attraente",
                "  ✅ Defense contractors: possibile rialzo",
                "  ⚠️  Ridurre esposizione tech con supply chain in zona conflitto",
            ]
        elif t_type == "trade":
            lines += [
                "  ⚠️  Tech: attenzione a supply chain exposure",
                "  ✅ Mercato domestico: meno vulnerabile",
                "  ⚠️  Auto/Agri: verificare esposizione ai dazi",
            ]
        elif t_type == "economic_sanctions":
            lines += [
                "  ✅ Energia: pressione rialzista su oil/gas",
                "  ✅ Oro: safe haven in crescita",
                "  ⚠️  Evitare esposizione a banche con legami nella regione",
            ]

        if trend == "escalating":
            lines.append("  🔴 Trend in escalation — rivisitare allocazione entro 48h")
        elif trend == "de-escalating":
            lines.append("  🟢 Trend in de-escalazione — opportunità di rimbalzo")

        return "\n".join(lines)
