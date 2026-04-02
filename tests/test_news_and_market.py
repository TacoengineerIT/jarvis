"""
tests/test_news_and_market.py — Phase 4: News scraper + market/social analysis.
All HTTP calls mocked. No real network access.
"""
import json
import pytest
from datetime import date
from unittest.mock import MagicMock, patch

# ── Fixtures ──────────────────────────────────────────────────────────────────

MOCK_ARTICLES = [
    {
        "source": "Reuters",
        "title": "US-China military tensions escalate over Taiwan strait",
        "content": "US Navy deployed carrier group near Taiwan as China launched military exercises.",
        "url": "https://reuters.com/1",
        "published_at": "2026-04-02T08:00:00+00:00",
        "category": "conflict",
        "countries": ["usa", "china", "taiwan"],
        "relevance_score": 0.9,
        "raw_text": "us-china military tensions escalate over taiwan strait us navy deployed carrier group near taiwan as china launched military exercises.",
    },
    {
        "source": "BBC",
        "title": "EU imposes new trade sanctions on Russia",
        "content": "European Union agreed on new package of economic sanctions targeting Russian energy exports.",
        "url": "https://bbc.com/1",
        "published_at": "2026-04-02T06:00:00+00:00",
        "category": "economic_sanctions",
        "countries": ["eu", "russia", "europe"],
        "relevance_score": 0.8,
        "raw_text": "eu imposes new trade sanctions on russia european union agreed on new package of economic sanctions targeting russian energy exports.",
    },
    {
        "source": "AP News",
        "title": "Saudi-Iran peace talks show progress",
        "content": "Ceasefire negotiations between Saudi Arabia and Iran yielded a diplomatic agreement.",
        "url": "https://apnews.com/1",
        "published_at": "2026-04-02T05:30:00+00:00",
        "category": "diplomacy",
        "countries": ["saudi", "iran", "middle east"],
        "relevance_score": 0.7,
        "raw_text": "saudi-iran peace talks show progress ceasefire negotiations between saudi arabia and iran yielded a diplomatic agreement.",
    },
]

MOCK_TENSIONS = [
    {
        "tension_type": "military",
        "countries_involved": ["usa", "china", "taiwan"],
        "tension_score": 7.5,
        "appeasement_score": 1.0,
        "trend": "escalating",
        "duration_estimate_days": 45,
        "impact_assessment": "Tensione alta (conflitto militare) tra Usa, China, Taiwan. Score: 7.5/10.",
        "articles": ["US-China military tensions escalate over Taiwan strait"],
        "created_at": "2026-04-02T08:00:00+00:00",
    },
    {
        "tension_type": "economic_sanctions",
        "countries_involved": ["eu", "russia"],
        "tension_score": 6.0,
        "appeasement_score": 0.5,
        "trend": "stable",
        "duration_estimate_days": 120,
        "impact_assessment": "Tensione moderata (sanzioni economiche) tra Eu, Russia. Score: 6.0/10.",
        "articles": ["EU imposes new trade sanctions on Russia"],
        "created_at": "2026-04-02T08:00:00+00:00",
    },
]


# ═══════════════════════════════════════════════════════════════════
# 1. NewsScraper
# ═══════════════════════════════════════════════════════════════════

class TestNewsScraperFilter:
    def _scraper(self):
        from jarvis_news_scraper import NewsScraper
        return NewsScraper(sources=[])

    def test_filter_keeps_geopolitical_articles(self):
        sc = self._scraper()
        raw = [
            {
                "source": "Reuters", "title": "War escalates in region",
                "content": "Military troops deployed.", "url": "http://a",
                "published_at": "2026-04-02", "raw_text": "war escalates military troops deployed",
            }
        ]
        result = sc.filter_relevant_news(raw)
        assert len(result) == 1
        assert result[0]["category"] in ("conflict", "geopolitics", "diplomacy", "trade", "economics")

    def test_filter_drops_entertainment(self):
        sc = self._scraper()
        raw = [
            {
                "source": "TMZ", "title": "Celebrity Oscar party",
                "content": "Fashion and entertainment.", "url": "http://b",
                "published_at": "2026-04-02", "raw_text": "celebrity oscar party fashion entertainment",
            }
        ]
        result = sc.filter_relevant_news(raw)
        assert len(result) == 0

    def test_filter_drops_sports(self):
        sc = self._scraper()
        raw = [
            {
                "source": "ESPN", "title": "Football match results",
                "content": "Soccer scores from weekend.", "url": "http://c",
                "published_at": "2026-04-02", "raw_text": "football soccer match results scores weekend",
            }
        ]
        assert sc.filter_relevant_news(raw) == []

    def test_filter_assigns_relevance_score(self):
        sc = self._scraper()
        raw = [
            {
                "source": "BBC", "title": "Sanctions and military conflict",
                "content": "NATO troops deployed. Trade war announced. Tariff missile crisis.",
                "url": "http://d", "published_at": "2026-04-02",
                "raw_text": "sanctions military conflict nato troops deployed trade war tariff missile crisis",
            }
        ]
        result = sc.filter_relevant_news(raw)
        assert len(result) == 1
        assert 0 < result[0]["relevance_score"] <= 1.0

    def test_filter_extracts_countries(self):
        sc = self._scraper()
        raw = [
            {
                "source": "AP", "title": "US and China trade war",
                "content": "Tariff sanctions between USA and China.", "url": "http://e",
                "published_at": "2026-04-02",
                "raw_text": "usa and china trade war tariff sanctions between usa and china",
            }
        ]
        result = sc.filter_relevant_news(raw)
        assert "usa" in result[0]["countries"] or "china" in result[0]["countries"]

    def test_filter_category_conflict(self):
        sc = self._scraper()
        raw = [{"source": "R", "title": "War", "content": "Military invasion attack",
                "url": "http://f", "published_at": "2026-04-02",
                "raw_text": "war military invasion attack troops"}]
        result = sc.filter_relevant_news(raw)
        assert result[0]["category"] == "conflict"

    def test_filter_category_trade(self):
        sc = self._scraper()
        raw = [{"source": "R", "title": "Trade war tariffs", "content": "Sanction embargo",
                "url": "http://g", "published_at": "2026-04-02",
                "raw_text": "trade war tariffs sanction embargo"}]
        result = sc.filter_relevant_news(raw)
        assert result[0]["category"] == "trade"

    def test_filter_sorts_by_relevance_desc(self):
        sc = self._scraper()
        raw = [
            {"source": "A", "title": "Minor diplomatic note", "content": "diplomacy",
             "url": "http://h1", "published_at": "2026-04-02", "raw_text": "diplomacy tension"},
            {"source": "B", "title": "Major war conflict military missile attack troops invasion",
             "content": "war conflict military missile", "url": "http://h2",
             "published_at": "2026-04-02",
             "raw_text": "major war conflict military missile attack troops invasion"},
        ]
        result = sc.filter_relevant_news(raw)
        if len(result) >= 2:
            assert result[0]["relevance_score"] >= result[1]["relevance_score"]


class TestNewsScraperExtractFacts:
    def _scraper(self):
        from jarvis_news_scraper import NewsScraper
        return NewsScraper(sources=[])

    def test_extract_facts_returns_required_keys(self):
        sc = self._scraper()
        article = MOCK_ARTICLES[0]
        facts = sc.extract_key_facts(article)
        for key in ("main_event", "countries_involved", "category", "trend", "timeline"):
            assert key in facts

    def test_extract_escalation_trend(self):
        sc = self._scraper()
        art = {
            "title": "War escalates, troops advance", "content": "Invasion launched.",
            "url": "http://x", "raw_text": "war escalates troops advance invasion launched attack",
        }
        facts = sc.extract_key_facts(art)
        assert facts["trend"] == "escalating"

    def test_extract_deescalation_trend(self):
        sc = self._scraper()
        art = {
            "title": "Ceasefire agreement signed", "content": "Peace deal resolves conflict.",
            "url": "http://y", "raw_text": "ceasefire agreement signed peace deal resolves conflict withdraw",
        }
        facts = sc.extract_key_facts(art)
        assert facts["trend"] == "de-escalating"

    def test_extract_immediate_timeline(self):
        sc = self._scraper()
        art = {"title": "Breaking: attack today", "content": "Overnight attack.",
               "url": "http://z", "raw_text": "breaking attack today overnight hours ago"}
        facts = sc.extract_key_facts(art)
        assert facts["timeline"] == "immediate"

    def test_scrape_morning_news_mocked(self):
        from jarvis_news_scraper import NewsScraper
        sc = NewsScraper(sources=[{"name": "Test", "url": "http://fake"}])
        with patch("jarvis_news_scraper._fetch_rss", return_value=MOCK_ARTICLES):
            result = sc.scrape_morning_news()
        assert isinstance(result, list)


# ═══════════════════════════════════════════════════════════════════
# 2. TensionAnalyzer
# ═══════════════════════════════════════════════════════════════════

class TestTensionAnalyzer:
    def _analyzer(self):
        from jarvis_tension_analyzer import TensionAnalyzer
        return TensionAnalyzer()

    def test_detect_returns_list(self):
        ta = self._analyzer()
        result = ta.detect_geopolitical_tensions(MOCK_ARTICLES)
        assert isinstance(result, list)

    def test_detect_finds_tensions(self):
        ta = self._analyzer()
        result = ta.detect_geopolitical_tensions(MOCK_ARTICLES)
        assert len(result) > 0

    def test_tension_score_in_range(self):
        ta = self._analyzer()
        for t in ta.detect_geopolitical_tensions(MOCK_ARTICLES):
            assert 0 <= t["tension_score"] <= 10

    def test_appeasement_score_in_range(self):
        ta = self._analyzer()
        for t in ta.detect_geopolitical_tensions(MOCK_ARTICLES):
            assert 0 <= t["appeasement_score"] <= 10

    def test_tension_has_required_keys(self):
        ta = self._analyzer()
        tensions = ta.detect_geopolitical_tensions(MOCK_ARTICLES)
        required = {"tension_type", "countries_involved", "tension_score",
                    "appeasement_score", "trend", "duration_estimate_days",
                    "impact_assessment", "articles"}
        for t in tensions:
            assert required.issubset(t.keys())

    def test_detect_empty_articles(self):
        ta = self._analyzer()
        assert ta.detect_geopolitical_tensions([]) == []

    def test_assess_appeasement_finds_peace_articles(self):
        ta = self._analyzer()
        result = ta.assess_appeasement_trends(MOCK_ARTICLES)
        # The Saudi-Iran article should show high appeasement
        assert any(r["appeasement_score"] > 0 for r in result)

    def test_predict_trajectory_escalating(self):
        ta = self._analyzer()
        data = {"tension_score": 8.0, "appeasement_score": 1.0,
                "tension_type": "military", "text": ""}
        result = ta.predict_tension_trajectory(data)
        assert result["trend"] == "escalating"
        assert result["duration_estimate_days"] > 0

    def test_predict_trajectory_deescalating(self):
        ta = self._analyzer()
        data = {"tension_score": 3.0, "appeasement_score": 6.0,
                "tension_type": "diplomatic", "text": ""}
        result = ta.predict_tension_trajectory(data)
        assert result["trend"] == "de-escalating"

    def test_quantify_global_risk_no_tensions(self):
        ta = self._analyzer()
        risk = ta.quantify_global_risk([])
        assert risk["global_tension_index"] == 0

    def test_quantify_global_risk_high_tension(self):
        ta = self._analyzer()
        risk = ta.quantify_global_risk(MOCK_TENSIONS)
        assert risk["global_tension_index"] > 0
        assert "hotspots" in risk
        assert "contagion_risk" in risk

    def test_precedents_returned(self):
        ta = self._analyzer()
        result = ta.predict_tension_trajectory(
            {"tension_score": 8.0, "appeasement_score": 0.5,
             "tension_type": "military", "text": ""}
        )
        assert isinstance(result["precedents"], list)


# ═══════════════════════════════════════════════════════════════════
# 3. MarketImpactPredictor
# ═══════════════════════════════════════════════════════════════════

class TestMarketImpactPredictor:
    def _predictor(self):
        from jarvis_market_impact_predictor import MarketImpactPredictor
        return MarketImpactPredictor()

    def test_predict_returns_required_keys(self):
        p = self._predictor()
        result = p.predict_market_moves(MOCK_TENSIONS[0])
        for key in ("stocks", "commodities", "forex", "vix_range",
                    "impact_direction", "confidence", "timeline"):
            assert key in result

    def test_stocks_populated(self):
        p = self._predictor()
        result = p.predict_market_moves(MOCK_TENSIONS[0])
        assert len(result["stocks"]) > 0

    def test_commodities_populated(self):
        p = self._predictor()
        result = p.predict_market_moves(MOCK_TENSIONS[0])
        assert len(result["commodities"]) > 0

    def test_forex_populated(self):
        p = self._predictor()
        result = p.predict_market_moves(MOCK_TENSIONS[0])
        assert len(result["forex"]) > 0

    def test_military_tension_bearish_stocks(self):
        p = self._predictor()
        result = p.predict_market_moves(MOCK_TENSIONS[0])
        # Military should be bearish overall
        assert result["impact_direction"] == "bearish"

    def test_confidence_in_range(self):
        p = self._predictor()
        result = p.predict_market_moves(MOCK_TENSIONS[0])
        assert 0 < result["confidence"] <= 1.0

    def test_vix_range_tuple(self):
        p = self._predictor()
        result = p.predict_market_moves(MOCK_TENSIONS[0])
        vix = result["vix_range"]
        assert isinstance(vix, (tuple, list))
        assert vix[0] < vix[1]

    def test_map_sector_impact_military(self):
        p = self._predictor()
        sectors = p.map_sector_impact("military")
        assert any(s["sector"] == "Defense" for s in sectors)
        assert any(s["impact"] == "bullish" for s in sectors)

    def test_map_sector_impact_trade(self):
        p = self._predictor()
        sectors = p.map_sector_impact("trade")
        assert any(s["sector"] == "Tech" for s in sectors)

    def test_estimate_timeline_has_keys(self):
        p = self._predictor()
        tl = p.estimate_timeline("military")
        assert "immediate" in tl
        assert "short_term" in tl

    def test_rank_affected_sectors_sorted(self):
        p = self._predictor()
        sectors = p.rank_affected_sectors(MOCK_TENSIONS[0])
        mags = [s["magnitude"] for s in sectors]
        assert mags == sorted(mags, reverse=True)

    def test_higher_tension_score_larger_range(self):
        p = self._predictor()
        low_t = {**MOCK_TENSIONS[0], "tension_score": 2.0}
        high_t = {**MOCK_TENSIONS[0], "tension_score": 9.0}
        low_r = p.predict_market_moves(low_t)
        high_r = p.predict_market_moves(high_t)
        # High tension → larger stock drop magnitude
        sp_low = low_r["stocks"].get("S&P 500", {}).get("range_pct", (0, 0))
        sp_high = high_r["stocks"].get("S&P 500", {}).get("range_pct", (0, 0))
        assert abs(sp_high[1]) >= abs(sp_low[1])


# ═══════════════════════════════════════════════════════════════════
# 4. SocialImpactAnalyzer
# ═══════════════════════════════════════════════════════════════════

class TestSocialImpactAnalyzer:
    def _analyzer(self):
        from jarvis_social_impact_analyzer import SocialImpactAnalyzer
        return SocialImpactAnalyzer()

    def test_employment_impact_keys(self):
        sa = self._analyzer()
        result = sa.assess_employment_impact(MOCK_TENSIONS[0])
        for key in ("direction", "magnitude_pct_unemployment_change",
                    "duration_months", "recovery_likelihood"):
            assert key in result

    def test_inflation_impact_keys(self):
        sa = self._analyzer()
        result = sa.assess_inflation_impact(MOCK_TENSIONS[0])
        for key in ("direction", "magnitude_pct", "sectors_hit", "duration_months"):
            assert key in result

    def test_migration_risk_in_range(self):
        sa = self._analyzer()
        result = sa.assess_migration_risk(MOCK_TENSIONS[0])
        assert 0 <= result["risk_level"] <= 1.0

    def test_supply_chain_keys(self):
        sa = self._analyzer()
        result = sa.assess_supply_chain_disruption(MOCK_TENSIONS[0])
        for key in ("disruption_risk", "severity", "affected_goods"):
            assert key in result

    def test_military_high_migration_risk(self):
        sa = self._analyzer()
        result = sa.assess_migration_risk(MOCK_TENSIONS[0])  # military, score 7.5
        assert result["risk_level"] > 0.4

    def test_diplomatic_low_inflation(self):
        sa = self._analyzer()
        t = {**MOCK_TENSIONS[0], "tension_type": "diplomatic", "tension_score": 3.0}
        result = sa.assess_inflation_impact(t)
        assert result["direction"] == "stable"

    def test_full_assessment_has_all_sections(self):
        sa = self._analyzer()
        result = sa.full_assessment(MOCK_TENSIONS[0])
        for key in ("employment", "inflation", "migration", "supply_chain"):
            assert key in result

    def test_higher_score_higher_disruption_risk(self):
        sa = self._analyzer()
        low_t = {**MOCK_TENSIONS[0], "tension_score": 2.0}
        high_t = {**MOCK_TENSIONS[0], "tension_score": 9.0}
        low_r = sa.assess_supply_chain_disruption(low_t)["disruption_risk"]
        high_r = sa.assess_supply_chain_disruption(high_t)["disruption_risk"]
        assert high_r >= low_r


# ═══════════════════════════════════════════════════════════════════
# 5. MorningBriefingGenerator
# ═══════════════════════════════════════════════════════════════════

class TestMorningBriefingGenerator:
    def _make_generator(self):
        from jarvis_morning_briefing import MorningBriefingGenerator
        from jarvis_tension_analyzer import TensionAnalyzer
        from jarvis_market_impact_predictor import MarketImpactPredictor
        from jarvis_social_impact_analyzer import SocialImpactAnalyzer
        from jarvis_memory import JarvisMemory
        from pathlib import Path
        import tempfile

        tmp = tempfile.mktemp(suffix=".db")
        mem = JarvisMemory(db_path=Path(tmp))

        mock_scraper = MagicMock()
        mock_scraper.scrape_morning_news.return_value = MOCK_ARTICLES

        return MorningBriefingGenerator(
            news_scraper=mock_scraper,
            tension_analyzer=TensionAnalyzer(),
            market_predictor=MarketImpactPredictor(),
            social_analyzer=SocialImpactAnalyzer(),
            memory=mem,
        )

    def test_generate_returns_required_keys(self):
        gen = self._make_generator()
        result = gen.generate_daily_briefing()
        for key in ("date", "briefing_text", "key_tensions",
                    "market_impacts", "social_impacts",
                    "actionable_items", "confidence"):
            assert key in result

    def test_generate_briefing_text_not_empty(self):
        gen = self._make_generator()
        result = gen.generate_daily_briefing()
        assert len(result["briefing_text"]) > 100

    def test_generate_includes_today_date(self):
        gen = self._make_generator()
        result = gen.generate_daily_briefing()
        assert result["date"] == date.today().isoformat()

    def test_confidence_in_range(self):
        gen = self._make_generator()
        result = gen.generate_daily_briefing()
        assert 0 < result["confidence"] <= 1.0

    def test_get_today_briefing_returns_saved(self):
        gen = self._make_generator()
        first = gen.generate_daily_briefing()
        second = gen.get_today_briefing()
        assert second["date"] == first["date"]

    def test_briefing_contains_tensions_section(self):
        gen = self._make_generator()
        result = gen.generate_daily_briefing()
        assert "GEOPOLITIC" in result["briefing_text"].upper() or "TENSIONI" in result["briefing_text"].upper()

    def test_briefing_contains_market_section(self):
        gen = self._make_generator()
        result = gen.generate_daily_briefing()
        assert "MERCATI" in result["briefing_text"].upper() or "MARKET" in result["briefing_text"].upper()

    def test_briefing_contains_social_section(self):
        gen = self._make_generator()
        result = gen.generate_daily_briefing()
        assert "SOCIAL" in result["briefing_text"].upper() or "OCCUPAZIONE" in result["briefing_text"].upper()

    def test_empty_news_still_generates_briefing(self):
        from jarvis_morning_briefing import MorningBriefingGenerator
        from jarvis_memory import JarvisMemory
        from pathlib import Path
        import tempfile

        mock_scraper = MagicMock()
        mock_scraper.scrape_morning_news.return_value = []
        mem = JarvisMemory(db_path=Path(tempfile.mktemp(suffix=".db")))
        gen = MorningBriefingGenerator(news_scraper=mock_scraper, memory=mem)
        result = gen.generate_daily_briefing()
        assert "briefing_text" in result
        assert result["key_tensions"] == []

    def test_get_market_impacts_text(self):
        gen = self._make_generator()
        gen.generate_daily_briefing()
        text = gen.get_market_impacts()
        assert isinstance(text, str)
        assert len(text) > 0


# ═══════════════════════════════════════════════════════════════════
# 6. JarvisMemory news tables
# ═══════════════════════════════════════════════════════════════════

class TestMemoryNewsTables:
    def _memory(self, tmp_path):
        from jarvis_memory import JarvisMemory
        return JarvisMemory(db_path=tmp_path / "test.db")

    def test_save_news_articles(self, tmp_path):
        mem = self._memory(tmp_path)
        mem.save_news_articles(MOCK_ARTICLES)
        recent = mem.get_recent_news(limit=10)
        assert len(recent) == len(MOCK_ARTICLES)

    def test_save_news_ignores_duplicates(self, tmp_path):
        mem = self._memory(tmp_path)
        mem.save_news_articles(MOCK_ARTICLES)
        mem.save_news_articles(MOCK_ARTICLES)  # second insert
        recent = mem.get_recent_news(limit=20)
        assert len(recent) == len(MOCK_ARTICLES)  # no duplicates

    def test_save_and_get_morning_briefing(self, tmp_path):
        mem = self._memory(tmp_path)
        today = date.today().isoformat()
        briefing = {
            "date": today,
            "generated_at": "2026-04-02T06:00:00",
            "briefing_text": "Test briefing",
            "key_tensions": MOCK_TENSIONS,
            "market_impacts": [],
            "social_impacts": [],
            "actionable_items": "Watch markets",
            "confidence": 0.75,
        }
        mem.save_morning_briefing(briefing)
        result = mem.get_morning_briefing(today)
        assert result is not None
        assert result["date"] == today
        assert result["briefing_text"] == "Test briefing"
        assert result["confidence"] == 0.75

    def test_get_morning_briefing_missing_returns_none(self, tmp_path):
        mem = self._memory(tmp_path)
        result = mem.get_morning_briefing("1900-01-01")
        assert result is None

    def test_briefing_upsert(self, tmp_path):
        mem = self._memory(tmp_path)
        today = date.today().isoformat()
        b1 = {"date": today, "generated_at": "T1", "briefing_text": "First",
              "key_tensions": [], "market_impacts": [], "social_impacts": [],
              "actionable_items": "", "confidence": 0.5}
        b2 = {**b1, "briefing_text": "Updated", "confidence": 0.9}
        mem.save_morning_briefing(b1)
        mem.save_morning_briefing(b2)
        result = mem.get_morning_briefing(today)
        assert result["briefing_text"] == "Updated"
        assert result["confidence"] == 0.9
