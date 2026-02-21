from typing import Optional
import httpx

from ..config import settings


class EmbeddingService:
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=60.0,
            )
        return self._client

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        url = "https://openrouter.ai/api/v1/embeddings"

        payload = {
            "model": self.model,
            "input": texts,
        }

        response = await self.client.post(url, json=payload)
        response.raise_for_status()

        data = response.json()
        embeddings = sorted(
            data["data"], key=lambda x: x["index"]
        )
        return [e["embedding"] for e in embeddings]

    async def embed_query(self, query: str) -> list[float]:
        embeddings = await self.embed_texts([query])
        return embeddings[0]

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
