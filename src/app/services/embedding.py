
import hashlib

import httpx

from ..config import settings


class EmbeddingService:
    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions
        self.use_mock = settings.use_mock_embeddings
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self.use_mock:
            raise ValueError("Mock embeddings are enabled. Do not use client property.")

        if not self.api_key:
            raise ValueError(
                "OpenRouter API key is not configured. "
                "Please set OPENROUTER_API_KEY environment variable "
                "or set USE_MOCK_EMBEDDINGS=true for testing."
            )

        if self._client is None:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }
            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=60.0,
            )
        return self._client

    def _generate_mock_embedding(self, text: str) -> list[float]:
        """Generate a deterministic mock embedding based on text hash."""
        text_hash = hashlib.sha256(text.encode('utf-8')).digest()

        embedding = []
        for i in range(self.dimensions):
            byte_val = text_hash[i % len(text_hash)]
            value = (byte_val / 127.5) - 1.0
            embedding.append(value)

        return embedding

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self.use_mock:
            return [self._generate_mock_embedding(text) for text in texts]

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

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
