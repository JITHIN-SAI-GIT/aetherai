from typing import List
from app.search.models import SearchResult


class SerpAPISearchProvider:
    def name(self) -> str: return "serpapi"
    async def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        raise NotImplementedError("SerpAPI integration not yet implemented.")
    async def health_check(self) -> bool: raise NotImplementedError()
