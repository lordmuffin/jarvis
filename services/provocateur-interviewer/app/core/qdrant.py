import os
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

class QdrantService:
    def __init__(self):
        self.host = os.getenv("QDRANT_HOST", "qdrant")
        self.port = int(os.getenv("QDRANT_PORT", "6333"))
        self.client = AsyncQdrantClient(host=self.host, port=self.port)

    async def search(self, collection_name: str, vector: list[float], limit: int = 5):
        return await self.client.search(
            collection_name=collection_name,
            query_vector=vector,
            limit=limit
        )

    async def scroll(self, collection_name: str, limit: int = 10, offset: int = 0):
        # Using scroll to iterate over points
        return await self.client.scroll(
            collection_name=collection_name,
            limit=limit,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )
    
    async def get_collection_info(self, collection_name: str):
        return await self.client.get_collection(collection_name)
