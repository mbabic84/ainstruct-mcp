import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from ..config import settings


class QdrantService:
    def __init__(self, collection_name: str | None = None, is_admin: bool = False):
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
        self.collection_name = collection_name
        self.is_admin = is_admin
        if collection_name and not is_admin:
            self._ensure_collection()

    def _ensure_collection(self):
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=settings.embedding_dimensions,
                    distance=Distance.COSINE,
                ),
            )

    def get_all_collections(self) -> list[str]:
        collections = self.client.get_collections().collections
        return [c.name for c in collections]

    def upsert_chunks(
        self,
        chunks: list[dict],
        vectors: list[list[float]],
    ):
        if self.is_admin:
            raise ValueError("Admin cannot upsert to all collections")

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload=chunk,
            )
            for chunk, vector in zip(chunks, vectors)
        ]

        if self.collection_name is None:
            raise ValueError("Collection name is required for upsert")
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        return [p.id for p in points]

    def search(
        self,
        query_vector: list[float],
        limit: int = 5,
        filter_document_id: str | None = None,
    ) -> list[dict]:
        if self.is_admin:
            all_results = []
            for collection in self.get_all_collections():
                results = self._search_collection(
                    collection, query_vector, limit, filter_document_id
                )
                all_results.extend(results)

            all_results.sort(key=lambda x: x["score"], reverse=True)
            return all_results[:limit]

        if self.collection_name is None:
            raise ValueError("Collection name is required for non-admin search")

        return self._search_collection(
            self.collection_name, query_vector, limit, filter_document_id
        )

    def _search_collection(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int,
        filter_document_id: str | None = None,
    ) -> list[dict]:
        query_filter = None
        if filter_document_id:
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=filter_document_id),
                    )
                ]
            )

        search_result = self.client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            query_filter=query_filter,
            with_payload=True,
        )
        results = search_result.points

        return [
            {
                "id": r.id,
                "score": r.score,
                "document_id": r.payload.get("document_id") if r.payload else None,
                "chunk_index": r.payload.get("chunk_index") if r.payload else None,
                "content": r.payload.get("content") if r.payload else None,
                "token_count": r.payload.get("token_count") if r.payload else None,
                "title": r.payload.get("title") if r.payload else None,
                "collection": collection_name,
            }
            for r in results
        ]

    def delete_by_document_id(self, document_id: str):
        if self.is_admin:
            for collection in self.get_all_collections():
                self._delete_from_collection(collection, document_id)
        else:
            if self.collection_name is None:
                raise ValueError("Collection name is required for non-admin delete")
            self._delete_from_collection(self.collection_name, document_id)

    def _delete_from_collection(self, collection_name: str, document_id: str):
        self.client.delete(
            collection_name=collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            ),
        )

    def delete_by_point_ids(self, point_ids: list[str]):
        if self.is_admin:
            raise ValueError("Admin cannot delete by point IDs across all collections")

        if self.collection_name is None:
            raise ValueError("Collection name is required for delete")

        from qdrant_client.models import PointIdsList

        self.client.delete(
            collection_name=self.collection_name,
            points_selector=PointIdsList(points=list(point_ids)),
        )


def get_qdrant_service(collection_name: str | None = None, is_admin: bool = False) -> QdrantService:
    return QdrantService(collection_name, is_admin)
