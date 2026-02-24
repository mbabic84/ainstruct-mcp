
from pydantic import BaseModel, Field

from ..db import (
    DocumentCreate,
    get_document_repository,
    get_qdrant_service,
)
from ..services import get_chunking_service, get_embedding_service
from .context import get_auth_context, has_write_permission


class StoreDocumentInput(BaseModel):
    title: str
    content: str
    document_type: str = "markdown"
    doc_metadata: dict = Field(default_factory=dict)
    collection_id: str | None = None


class StoreDocumentOutput(BaseModel):
    document_id: str
    chunk_count: int
    token_count: int
    message: str


async def store_document(input_data: StoreDocumentInput) -> StoreDocumentOutput:
    auth = get_auth_context()
    if not auth:
        raise ValueError("Not authenticated")

    if auth.get("auth_type") == "jwt":
        raise ValueError("JWT users cannot store documents directly. Create an API key with read_write permission.")

    if not has_write_permission():
        raise ValueError("Insufficient permissions: read_write permission required to store documents")

    auth_type = auth.get("auth_type")

    if auth_type == "pat":
        collection_ids = auth.get("collection_ids", [])
        qdrant_collections = auth.get("qdrant_collections", [])

        if input_data.collection_id:
            if input_data.collection_id not in collection_ids:
                raise ValueError("Collection not found or access denied")
            idx = collection_ids.index(input_data.collection_id)
            collection_id = input_data.collection_id
            collection = qdrant_collections[idx]
        elif collection_ids:
            collection_id = collection_ids[0]
            collection = qdrant_collections[0]
        else:
            raise ValueError("No collections available. Create a collection first.")
    else:
        collection = auth["qdrant_collection"]
        collection_id = auth["collection_id"]

    doc_repo = get_document_repository(collection_id)
    qdrant = get_qdrant_service(collection)
    embedding_service = get_embedding_service()
    chunking_service = get_chunking_service()

    doc = doc_repo.create(DocumentCreate(
        collection_id=collection_id,
        title=input_data.title,
        content=input_data.content,
        document_type=input_data.document_type,
        doc_metadata=input_data.doc_metadata,
    ))

    chunks = chunking_service.chunk_markdown(input_data.content, input_data.title)

    if chunks:
        texts = [c["content"] for c in chunks]
        embeddings = await embedding_service.embed_texts(texts)

        chunks_with_meta = [
            {
                "document_id": doc.id,
                "chunk_index": c["chunk_index"],
                "content": c["content"],
                "token_count": c["token_count"],
                "title": c["title"],
            }
            for c in chunks
        ]

        point_ids = qdrant.upsert_chunks(chunks_with_meta, embeddings)
        doc_repo.update_qdrant_point_id(doc.id, point_ids)

    total_tokens = sum(c["token_count"] for c in chunks)

    return StoreDocumentOutput(
        document_id=doc.id,
        chunk_count=len(chunks),
        token_count=total_tokens,
        message=f"Document stored successfully with {len(chunks)} chunks",
    )


class SearchDocumentsInput(BaseModel):
    query: str
    max_results: int = 5
    max_tokens: int = 2000


class SearchResultItem(BaseModel):
    document_id: str
    title: str
    chunk_index: int
    content: str
    score: float
    collection: str | None = None


class SearchDocumentsOutput(BaseModel):
    results: list[SearchResultItem]
    total_results: int
    tokens_used: int
    formatted_context: str


async def search_documents(input_data: SearchDocumentsInput) -> SearchDocumentsOutput:
    auth = get_auth_context()
    if not auth:
        raise ValueError("Not authenticated")

    embedding_service = get_embedding_service()

    is_admin = auth.get("is_admin", False) or auth.get("is_superuser", False)
    collection = auth.get("qdrant_collection")
    qdrant_collections = auth.get("qdrant_collections", [])

    query_embedding = await embedding_service.embed_query(input_data.query)

    if is_admin:
        qdrant = get_qdrant_service(None, is_admin=True)
        results = qdrant.search(
            query_vector=query_embedding,
            limit=input_data.max_results,
        )
    elif qdrant_collections:
        qdrant = get_qdrant_service(None, is_admin=False)
        results = qdrant.search_multi(
            collection_names=qdrant_collections,
            query_vector=query_embedding,
            limit=input_data.max_results,
        )
    else:
        qdrant = get_qdrant_service(str(collection) if collection else None)
        results = qdrant.search(
            query_vector=query_embedding,
            limit=input_data.max_results,
        )

    search_results = []
    total_tokens = 0

    for r in results:
        search_results.append(SearchResultItem(
            document_id=r["document_id"],
            title=r["title"],
            chunk_index=r["chunk_index"],
            content=r["content"],
            score=r["score"],
            collection=r.get("collection"),
        ))
        total_tokens += r.get("token_count", 0)

        if total_tokens >= input_data.max_tokens:
            break

    formatted_parts = []
    seen_titles = set()

    for item in search_results:
        if item.title not in seen_titles:
            formatted_parts.append(f"## {item.title}\n\n")
            if item.collection:
                formatted_parts.append(f"*Collection: {item.collection}*\n\n")
            seen_titles.add(item.title)

        formatted_parts.append(f"### Section {item.chunk_index + 1} (relevance: {item.score:.2f})\n\n")
        formatted_parts.append(item.content)
        formatted_parts.append("\n\n---\n\n")

    formatted_context = "".join(formatted_parts)

    return SearchDocumentsOutput(
        results=search_results,
        total_results=len(results),
        tokens_used=min(total_tokens, input_data.max_tokens),
        formatted_context=formatted_context.strip(),
    )


class GetDocumentInput(BaseModel):
    document_id: str


class GetDocumentOutput(BaseModel):
    id: str
    collection_id: str
    title: str
    content: str
    document_type: str
    created_at: str
    updated_at: str
    doc_metadata: dict


async def get_document(input_data: GetDocumentInput) -> GetDocumentOutput | None:
    auth = get_auth_context()
    if not auth:
        raise ValueError("Not authenticated")

    is_admin = auth.get("is_admin", False) or auth.get("is_superuser", False)
    user_id = auth.get("user_id")
    auth_type = auth.get("auth_type")

    if is_admin:
        doc_repo = get_document_repository(None)
        doc = doc_repo.get_by_id(input_data.document_id)
    elif auth_type in ("pat", "jwt") and user_id:
        doc_repo = get_document_repository(None)
        doc = doc_repo.get_by_id_for_user(input_data.document_id, user_id)
    else:
        collection_id = auth.get("collection_id")
        doc_repo = get_document_repository(str(collection_id) if collection_id else None)
        doc = doc_repo.get_by_id(input_data.document_id)

    if not doc:
        return None

    return GetDocumentOutput(
        id=doc.id,
        collection_id=doc.collection_id,
        title=doc.title,
        content=doc.content,
        document_type=doc.document_type,
        created_at=doc.created_at.isoformat(),
        updated_at=doc.updated_at.isoformat(),
        doc_metadata=doc.doc_metadata,
    )


class ListDocumentsInput(BaseModel):
    limit: int = 50
    offset: int = 0


class ListDocumentsOutput(BaseModel):
    documents: list[GetDocumentOutput]
    total: int


async def list_documents(input_data: ListDocumentsInput) -> ListDocumentsOutput:
    auth = get_auth_context()
    if not auth:
        raise ValueError("Not authenticated")

    is_admin = auth.get("is_admin", False) or auth.get("is_superuser", False)
    collection_id = auth.get("collection_id")
    auth_type = auth.get("auth_type")
    user_id = auth.get("user_id")

    if is_admin:
        doc_repo = get_document_repository(None)
        docs = doc_repo.list_all(limit=input_data.limit, offset=input_data.offset)
    elif auth_type in ("pat", "jwt") and user_id:
        doc_repo = get_document_repository(None)
        docs = doc_repo.list_all_for_user(user_id, limit=input_data.limit, offset=input_data.offset)
    else:
        doc_repo = get_document_repository(str(collection_id) if collection_id else None)
        docs = doc_repo.list_all(limit=input_data.limit, offset=input_data.offset)

    documents = [
        GetDocumentOutput(
            id=d.id,
            collection_id=d.collection_id,
            title=d.title,
            content=d.content,
            document_type=d.document_type,
            created_at=d.created_at.isoformat(),
            updated_at=d.updated_at.isoformat(),
            doc_metadata=d.doc_metadata,
        )
        for d in docs
    ]

    return ListDocumentsOutput(
        documents=documents,
        total=len(documents),
    )


class DeleteDocumentInput(BaseModel):
    document_id: str


class DeleteDocumentOutput(BaseModel):
    success: bool
    message: str


async def delete_document(input_data: DeleteDocumentInput) -> DeleteDocumentOutput:
    auth = get_auth_context()
    if not auth:
        raise ValueError("Not authenticated")

    if auth.get("auth_type") == "jwt":
        raise ValueError("JWT users cannot delete documents directly. Create an API key with read_write permission.")

    if not has_write_permission():
        raise ValueError("Insufficient permissions: read_write permission required to delete documents")

    is_admin = auth.get("is_admin", False) or auth.get("is_superuser", False)
    user_id = auth.get("user_id")
    auth_type = auth.get("auth_type")

    if is_admin:
        doc_repo = get_document_repository(None)
        doc = doc_repo.get_by_id(input_data.document_id)
    elif auth_type in ("pat", "jwt") and user_id:
        doc_repo = get_document_repository(None)
        doc = doc_repo.get_by_id_for_user(input_data.document_id, user_id)
    else:
        collection_id = auth.get("collection_id")
        doc_repo = get_document_repository(str(collection_id) if collection_id else None)
        doc = doc_repo.get_by_id(input_data.document_id)

    if not doc:
        return DeleteDocumentOutput(
            success=False,
            message="Document not found",
        )

    qdrant_collection = auth.get("qdrant_collection")
    qdrant_collections = auth.get("qdrant_collections", [])
    if is_admin:
        qdrant = get_qdrant_service(None, is_admin=True)
    elif qdrant_collections:
        qdrant = get_qdrant_service(None, is_admin=False)
    else:
        qdrant = get_qdrant_service(str(qdrant_collection) if qdrant_collection else None)

    if qdrant_collections:
        for coll in qdrant_collections:
            q = get_qdrant_service(coll)
            q.delete_by_document_id(input_data.document_id)
    else:
        qdrant.delete_by_document_id(input_data.document_id)

    doc_repo.delete(input_data.document_id)

    return DeleteDocumentOutput(
        success=True,
        message="Document deleted successfully",
    )


class UpdateDocumentInput(BaseModel):
    document_id: str
    title: str
    content: str
    document_type: str = "markdown"
    doc_metadata: dict = Field(default_factory=dict)


class UpdateDocumentOutput(BaseModel):
    document_id: str
    chunk_count: int
    token_count: int
    message: str


async def update_document(input_data: UpdateDocumentInput) -> UpdateDocumentOutput:
    auth = get_auth_context()
    if not auth:
        raise ValueError("Not authenticated")

    if auth.get("auth_type") == "jwt":
        raise ValueError("JWT users cannot update documents directly. Create an API key with read_write permission.")

    if not has_write_permission():
        raise ValueError("Insufficient permissions: read_write permission required to update documents")

    is_admin = auth.get("is_admin", False) or auth.get("is_superuser", False)
    user_id = auth.get("user_id")
    auth_type = auth.get("auth_type")
    collection_id = auth.get("collection_id")
    qdrant_collection = auth.get("qdrant_collection")
    qdrant_collections = auth.get("qdrant_collections", [])

    if is_admin:
        doc_repo = get_document_repository(None)
        existing_doc = doc_repo.get_by_id(input_data.document_id)
    elif auth_type in ("pat", "jwt") and user_id:
        doc_repo = get_document_repository(None)
        existing_doc = doc_repo.get_by_id_for_user(input_data.document_id, user_id)
    else:
        doc_repo = get_document_repository(str(collection_id) if collection_id else None)
        existing_doc = doc_repo.get_by_id(input_data.document_id)

    if not existing_doc:
        raise ValueError("Document not found")

    embedding_service = get_embedding_service()
    chunking_service = get_chunking_service()

    if qdrant_collections:
        for coll in qdrant_collections:
            q = get_qdrant_service(coll)
            q.delete_by_document_id(input_data.document_id)
    else:
        qdrant = get_qdrant_service(str(qdrant_collection) if qdrant_collection else None)
        qdrant.delete_by_document_id(input_data.document_id)

    updated_doc = doc_repo.update(
        doc_id=input_data.document_id,
        title=input_data.title,
        content=input_data.content,
        document_type=input_data.document_type,
        doc_metadata=input_data.doc_metadata,
    )

    if not updated_doc:
        raise ValueError("Failed to update document")

    chunks = chunking_service.chunk_markdown(input_data.content, input_data.title)

    if chunks:
        texts = [c["content"] for c in chunks]
        embeddings = await embedding_service.embed_texts(texts)

        chunks_with_meta = [
            {
                "document_id": updated_doc.id,
                "chunk_index": c["chunk_index"],
                "content": c["content"],
                "token_count": c["token_count"],
                "title": c["title"],
            }
            for c in chunks
        ]

        if qdrant_collections:
            for coll in qdrant_collections:
                q = get_qdrant_service(coll)
                point_ids = q.upsert_chunks(chunks_with_meta, embeddings)
        else:
            point_ids = qdrant.upsert_chunks(chunks_with_meta, embeddings)
        doc_repo.update_qdrant_point_id(updated_doc.id, point_ids)

    total_tokens = sum(c["token_count"] for c in chunks)

    return UpdateDocumentOutput(
        document_id=updated_doc.id,
        chunk_count=len(chunks),
        token_count=total_tokens,
        message=f"Document updated successfully with {len(chunks)} chunks",
    )
