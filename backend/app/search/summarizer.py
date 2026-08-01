import re
import logging
from typing import List, Dict, Any
from .models import SearchResult

logger = logging.getLogger("search.summarizer")

_HTML_TAG = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _HTML_TAG.sub("", text).strip()


class Summarizer:
    """
    Converts raw provider dicts into clean SearchResult objects.
    No raw HTML is ever exposed to downstream consumers.
    """

    def summarize(self, raw_results: List[Dict[str, Any]]) -> List[SearchResult]:
        results = []
        for item in raw_results:
            title   = _strip_html(item.get("title",   "Untitled"))
            snippet = _strip_html(item.get("snippet", item.get("description", "")))
            url     = item.get("url", item.get("link", ""))
            source  = item.get("source", item.get("domain", ""))
            pub     = item.get("published", item.get("date", None))

            results.append(SearchResult(
                title=title,
                snippet=snippet,
                url=url,
                source=source,
                published=pub,
                summary=snippet[:200] if snippet else None,
            ))

        logger.info("Results summarized", extra={"count": len(results)})
        return results
