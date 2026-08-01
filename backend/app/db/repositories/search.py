from typing import Dict, Any, List
from .collections import MemoryRepository
import logging

logger = logging.getLogger("db.search")

class SemanticMemoryRepository(MemoryRepository):
    async def semantic_search(self, query_vector: List[float], user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Perform a vector search using MongoDB Atlas Vector Search.
        Gracefully falls back to text/metadata search if Vector Search isn't configured
        or fails due to missing index.
        """
        try:
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "path": "embedding",
                        "queryVector": query_vector,
                        "numCandidates": limit * 10,
                        "limit": limit,
                        "filter": {"user_id": user_id}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "id": {"$toString": "$_id"},
                        "user_id": 1,
                        "memory_type": 1,
                        "classification": 1,
                        "key": 1,
                        "value": 1,
                        "score": {"$meta": "vectorSearchScore"}
                    }
                }
            ]
            
            cursor = self.collection.aggregate(pipeline)
            results = await cursor.to_list(length=limit)
            
            if results:
                return results
                
        except Exception as e:
            logger.warning(f"Vector search failed, falling back to metadata search: {e}")
            
        # Fallback to semantic metadata search (text search)
        logger.info("Executing metadata fallback search")
        fallback_pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    # Basic fallback assuming we do metadata matching or text search on 'value'
                    # In a real app this would use $text if a text index exists
                }
            },
            {"$limit": limit},
            {
                "$project": {
                    "_id": 0,
                    "id": {"$toString": "$_id"},
                    "user_id": 1,
                    "memory_type": 1,
                    "classification": 1,
                    "key": 1,
                    "value": 1,
                }
            }
        ]
        
        cursor = self.collection.aggregate(fallback_pipeline)
        return await cursor.to_list(length=limit)
