import re
import logging
from typing import List, Tuple
from .models import SearchDecision, SearchCategory

logger = logging.getLogger("search.detector")

# Keyword → (category, confidence) mapping
SEARCH_TRIGGERS: List[Tuple[str, SearchCategory, float]] = [
    # ── News / breaking ──────────────────────────────────────────────────────
    ("latest",        SearchCategory.NEWS,    0.95),
    ("breaking",      SearchCategory.NEWS,    0.95),
    ("breaking news", SearchCategory.NEWS,    0.98),
    ("news",          SearchCategory.NEWS,    0.90),
    ("trending",      SearchCategory.NEWS,    0.90),
    ("today",         SearchCategory.NEWS,    0.80),
    ("current",       SearchCategory.NEWS,    0.80),
    ("recent",        SearchCategory.NEWS,    0.80),
    ("live",          SearchCategory.NEWS,    0.85),
    ("update",        SearchCategory.NEWS,    0.75),
    ("announced",     SearchCategory.NEWS,    0.80),
    ("launched",      SearchCategory.NEWS,    0.80),
    ("released",      SearchCategory.NEWS,    0.80),
    ("what happened", SearchCategory.NEWS,    0.85),
    # ── Weather ───────────────────────────────────────────────────────────────
    ("weather",       SearchCategory.WEATHER, 1.00),
    ("forecast",      SearchCategory.WEATHER, 1.00),
    ("temperature",   SearchCategory.WEATHER, 0.90),
    ("rain",          SearchCategory.WEATHER, 0.75),
    ("humidity",      SearchCategory.WEATHER, 0.80),
    ("climate today", SearchCategory.WEATHER, 0.90),
    # ── Sports ────────────────────────────────────────────────────────────────
    ("score",         SearchCategory.SPORTS,  1.00),
    ("match",         SearchCategory.SPORTS,  0.80),
    ("standings",     SearchCategory.SPORTS,  0.90),
    ("points table",  SearchCategory.SPORTS,  0.95),
    ("ipl",           SearchCategory.SPORTS,  0.90),
    ("who won",       SearchCategory.SPORTS,  0.90),
    ("fixture",       SearchCategory.SPORTS,  0.85),
    ("result",        SearchCategory.SPORTS,  0.75),
    # ── General time-sensitive ────────────────────────────────────────────────
    ("price",         SearchCategory.GENERAL, 0.85),
    ("stock",         SearchCategory.GENERAL, 0.85),
    ("release",       SearchCategory.GENERAL, 0.80),
    ("new",           SearchCategory.GENERAL, 0.70),
    ("version",       SearchCategory.GENERAL, 0.75),
    ("this week",     SearchCategory.GENERAL, 0.80),
    ("this month",    SearchCategory.GENERAL, 0.80),
    ("this year",     SearchCategory.GENERAL, 0.75),
    ("date",          SearchCategory.GENERAL, 0.70),
    ("2024",          SearchCategory.GENERAL, 0.80),
    ("2025",          SearchCategory.GENERAL, 0.80),
    ("2026",          SearchCategory.GENERAL, 0.80),
]

# Intent values from Phase 4 that automatically trigger search
SEARCH_INTENTS = {"search_required"}


class SearchNecessityDetector:
    """
    Determines whether a query requires a live web search.
    Consumes the Phase 4 intent label and keyword-scans the query.
    """

    def detect(self, query: str, intent: str = "chat") -> SearchDecision:
        # Phase 4 intent short-circuits the keyword scan
        if intent in SEARCH_INTENTS:
            logger.info("Search required by intent", extra={"intent": intent})
            return SearchDecision(
                required=True,
                reason=f"Phase 4 intent classified as '{intent}'",
                confidence=1.0,
                category=SearchCategory.NEWS,
            )

        lowered = query.lower()
        for keyword, category, confidence in SEARCH_TRIGGERS:
            if re.search(r"\b" + re.escape(keyword) + r"\b", lowered):
                decision = SearchDecision(
                    required=True,
                    reason=f"Keyword '{keyword}' matched",
                    confidence=confidence,
                    category=category,
                )
                logger.info(
                    "Search required by keyword",
                    extra={"keyword": keyword, "confidence": confidence},
                )
                return decision

        return SearchDecision(
            required=False,
            reason="No time-sensitive keywords detected",
            confidence=1.0,
            category=SearchCategory.GENERAL,
        )
