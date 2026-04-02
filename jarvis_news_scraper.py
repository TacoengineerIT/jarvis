"""
jarvis_news_scraper.py — News fetcher via RSS feeds.
Sources: Reuters, BBC World, AP News, Al Jazeera, FT.
feedparser is used when available; falls back to requests + regex.
"""
import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional

_EXCLUDE_WHOLE_WORD_RE: re.Pattern | None = None  # compiled lazily

import requests

logger = logging.getLogger("jarvis.news_scraper")

# ── RSS sources ───────────────────────────────────────────────────────────────

RSS_SOURCES = [
    {"name": "Reuters",      "url": "https://feeds.reuters.com/reuters/worldNews"},
    {"name": "BBC World",    "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name": "AP News",      "url": "https://rsshub.app/apnews/topics/apf-intlnews"},
    {"name": "Al Jazeera",   "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"name": "FT",           "url": "https://www.ft.com/world?format=rss"},
]

# ── Keyword lists ─────────────────────────────────────────────────────────────

GEOPOLITICAL_KEYWORDS = [
    "war", "conflict", "military", "troops", "invasion", "attack", "missile",
    "sanction", "tariff", "trade war", "treaty", "summit", "diplomacy",
    "ceasefire", "peace talks", "nato", "un security council", "nuclear",
    "tension", "crisis", "agreement", "embargo", "dispute", "territorial",
    "coup", "uprising", "election", "alliance", "withdrawal", "deployment",
    "government", "minister", "president",
]

EXCLUDE_KEYWORDS = [
    "celebrity", "soccer", "football", "nba", "nfl", "grammy",
    "entertainment", "box office", "tv show", "fashion", "horoscope", "recipe",
    "oscar ceremony", "oscar award",
]

# Exclude keywords that require whole-word matching (short abbrevs)
_EXCLUDE_WHOLE_WORD = {"nba", "nfl"}

COUNTRY_MENTIONS = [
    "usa", "united states", "america", "china", "russia", "ukraine", "europe",
    "eu", "nato", "uk", "britain", "france", "germany", "israel", "iran",
    "saudi", "north korea", "taiwan", "india", "pakistan", "japan",
    "south korea", "turkey", "poland", "syria", "lebanon", "yemen",
    "iraq", "afghanistan", "middle east", "africa", "asia",
]

_CATEGORY_MAP = {
    # Trade checked before conflict to correctly handle "trade war" (contains "war")
    "trade":      ["trade war", "sanction", "tariff", "embargo", "export ban", "import duty"],
    "conflict":   ["invasion", "military attack", "troops deployed", "missile strike",
                   "airstrike", "bomb", "weapon", "combat", "troops", "military"],
    "diplomacy":  ["summit", "treaty", "diplomat", "ceasefire", "peace talks", "agreement"],
    "economics":  ["economy", "gdp", "inflation", "recession", "stock market", "currency"],
}


def _clean_html(text: str) -> str:
    text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_rss_feedparser(feed_url: str, source_name: str) -> list[dict]:
    """Parse via feedparser (preferred)."""
    import feedparser  # type: ignore
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries[:20]:
        title = entry.get("title", "")
        summary = _clean_html(entry.get("summary", "") or entry.get("description", ""))
        link = entry.get("link", "")
        published = datetime.now(timezone.utc).isoformat()
        if getattr(entry, "published_parsed", None):
            try:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
        if title:
            articles.append({
                "source": source_name, "title": title, "content": summary,
                "url": link, "published_at": published,
                "raw_text": f"{title} {summary}".lower(),
            })
    return articles


def _parse_rss_requests(feed_url: str, source_name: str, timeout: int = 8) -> list[dict]:
    """Fallback: parse RSS with requests + regex."""
    resp = requests.get(feed_url, timeout=timeout, headers={"User-Agent": "JARVIS/4.0"})
    resp.raise_for_status()
    items = re.findall(r"<item>(.*?)</item>", resp.text, re.DOTALL)
    articles = []
    for item in items[:20]:
        def _extract(tag):
            m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", item, re.DOTALL)
            return _clean_html(m.group(1)) if m else ""
        title = _extract("title")
        content = _extract("description")
        link = _extract("link")
        pub = _extract("pubDate") or datetime.now(timezone.utc).isoformat()
        if title:
            articles.append({
                "source": source_name, "title": title, "content": content,
                "url": link, "published_at": pub,
                "raw_text": f"{title} {content}".lower(),
            })
    return articles


def _fetch_rss(feed_url: str, source_name: str, timeout: int = 8) -> list[dict]:
    """Attempt feedparser first, fall back to requests."""
    try:
        import feedparser  # noqa
        return _parse_rss_feedparser(feed_url, source_name)
    except ImportError:
        pass
    except Exception as e:
        logger.debug("[NEWS] feedparser error for %s: %s", source_name, e)

    try:
        return _parse_rss_requests(feed_url, source_name, timeout)
    except Exception as e:
        logger.warning("[NEWS] Failed to fetch %s: %s", source_name, e)
        return []


class NewsScraper:
    """Fetches and filters geopolitically relevant news from RSS feeds."""

    def __init__(
        self,
        sources: Optional[list[dict]] = None,
        request_timeout: int = 8,
    ):
        self.sources = sources if sources is not None else RSS_SOURCES
        self.timeout = request_timeout

    # ── Public API ────────────────────────────────────────────────────────────

    def scrape_morning_news(self) -> list[dict]:
        """
        Fetch + filter news from all sources.
        Returns geopolitically relevant articles sorted by relevance_score desc.
        """
        all_articles: list[dict] = []
        for src in self.sources:
            logger.info("[NEWS] Fetching %s", src["name"])
            articles = _fetch_rss(src["url"], src["name"], self.timeout)
            all_articles.extend(articles)
        logger.info("[NEWS] %d raw articles fetched", len(all_articles))
        filtered = self.filter_relevant_news(all_articles)
        logger.info("[NEWS] %d relevant articles after filter", len(filtered))
        return filtered

    def filter_relevant_news(
        self,
        articles: list[dict],
        categories: Optional[list[str]] = None,
    ) -> list[dict]:
        """Keep geopolitically relevant articles; drop entertainment/sports."""
        relevant = []
        for art in articles:
            raw = art.get("raw_text", "").lower()
            # Check multi-word / long-form exclude keywords (substring match is safe)
            long_excludes = [kw for kw in EXCLUDE_KEYWORDS if kw not in _EXCLUDE_WHOLE_WORD]
            if any(kw in raw for kw in long_excludes):
                continue
            # Whole-word matching for short abbreviations (nba, nfl) to avoid
            # false positives like "conflict" containing "nfl"
            if any(re.search(r"\b" + re.escape(kw) + r"\b", raw)
                   for kw in _EXCLUDE_WHOLE_WORD):
                continue
            score = sum(1 for kw in GEOPOLITICAL_KEYWORDS if kw in raw)
            if score == 0:
                continue
            category = self._classify_category(raw)
            if categories and category not in categories:
                continue
            countries = list({c for c in COUNTRY_MENTIONS if c in raw})
            relevant.append({
                "source": art["source"],
                "title": art["title"],
                "content": art["content"],
                "url": art["url"],
                "published_at": art["published_at"],
                "category": category,
                "countries": countries,
                "relevance_score": min(score / 10.0, 1.0),
            })
        relevant.sort(key=lambda a: a["relevance_score"], reverse=True)
        return relevant

    def extract_key_facts(self, article: dict) -> dict:
        """Extract structured facts: actors, trend, timeline from article."""
        raw = (article.get("raw_text") or
               f"{article.get('title','')} {article.get('content','')}").lower()

        countries = list({c.title() for c in COUNTRY_MENTIONS if c in raw})[:5]

        # Timeline
        timeline = "unclear"
        if any(kw in raw for kw in ["breaking", "today", "overnight", "hours ago", "yesterday"]):
            timeline = "immediate"
        elif any(kw in raw for kw in ["this week", "days", "upcoming"]):
            timeline = "short-term"
        elif any(kw in raw for kw in ["this month", "weeks ahead", "next month"]):
            timeline = "medium-term"

        # Trend
        is_esc = any(kw in raw for kw in [
            "escalat", "intensif", "worsen", "expan", "seize", "captur",
            "invad", "launch", "attack", "advanc",
        ])
        is_res = any(kw in raw for kw in [
            "ceasefire", "peace", "agreement", "deal", "withdraw",
            "de-escalat", "negotiat", "resolv",
        ])
        if is_esc and not is_res:
            trend = "escalating"
        elif is_res and not is_esc:
            trend = "de-escalating"
        elif is_esc and is_res:
            trend = "mixed"
        else:
            trend = "neutral"

        return {
            "main_event": article.get("title", ""),
            "countries_involved": countries,
            "category": article.get("category", "geopolitics"),
            "trend": trend,
            "timeline": timeline,
            "source": article.get("source"),
            "relevance_score": article.get("relevance_score", 0.5),
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _classify_category(self, text: str) -> str:
        for cat, kws in _CATEGORY_MAP.items():
            if any(kw in text for kw in kws):
                return cat
        return "geopolitics"
