from typing import List
from app.search.models import SearchResult


class BraveSearchProvider:
    def name(self) -> str: return "brave"
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        raise NotImplementedError("Brave Search integration not yet implemented.")
    async def health_check(self) -> bool: raise NotImplementedError()
