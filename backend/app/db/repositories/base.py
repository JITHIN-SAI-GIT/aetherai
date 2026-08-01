from typing import Any, Dict, List, Optional
from bson import ObjectId
from app.db.mongo import get_db

class BaseMongoRepository:
    collection_name: str = ""

    @property
    def collection(self):
        db = get_db()
        return db[self.collection_name]

    def _convert_id(self, document: Dict[str, Any]) -> Dict[str, Any]:
        if not document:
            return document
        if "_id" in document:
            document["id"] = str(document.pop("_id"))
        return document

    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one({"_id": ObjectId(doc_id)})
        return self._convert_id(doc)

    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        doc = await self.collection.find_one(query)
        return self._convert_id(doc)

    async def find_many(self, query: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        cursor = self.collection.find(query).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [self._convert_id(doc) for doc in docs]

    async def insert_one(self, document: Dict[str, Any]) -> str:
        # Don't mutate original document
        doc_copy = document.copy()
        if "id" in doc_copy:
            doc_copy.pop("id")
        result = await self.collection.insert_one(doc_copy)
        return str(result.inserted_id)

    async def update_one(self, query: Dict[str, Any], update_data: Dict[str, Any], upsert: bool = False) -> bool:
        result = await self.collection.update_one(query, {"$set": update_data}, upsert=upsert)
        return result.modified_count > 0 or result.upserted_id is not None

    async def delete_one(self, query: Dict[str, Any]) -> bool:
        result = await self.collection.delete_one(query)
        return result.deleted_count > 0

    async def delete_many(self, query: Dict[str, Any]) -> int:
        result = await self.collection.delete_many(query)
        return result.deleted_count
