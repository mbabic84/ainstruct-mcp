
from pydantic import BaseModel

from ..db import (
    DocumentCreate,
    get_document_repository,
    get_qdrant_service,
)
from ..services import get_chunking_service, get_embedding_service
from .context import get_api_key_info


class StoreDocumentInput(BaseModel):
    title: str
    content: str
    document_type: str = "markdown"
    doc_metadata: dict = {}


class StoreDocumentOutput(BaseModel):
    document_id: str
    chunk_count: int
    token_count: int
    message: str


async def store_document(input_data: StoreDocumentInput) -> StoreDocumentOutput:
    api_key_info = get_api_key_info()
    if not api_key_info:
        raise ValueError("API key not authenticated")

    if api_key_info.get("is_admin"):
        raise ValueError("Admin cannot store documents")

    doc_repo = get_document_repository(api_key_info["id"])
    qdrant = get_qdrant_service(api_key_info["qdrant_collection"])
    embedding_service = get_embedding_service()
    chunking_service = get_chunking_service()

    doc = doc_repo.create(DocumentCreate(
        api_key_id=api_key_info["id"],
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
    api_key_info = get_api_key_info()
    if not api_key_info:
        raise ValueError("API key not authenticated")

    embedding_service = get_embedding_service()

    is_admin = api_key_info.get("is_admin", False)
    collection = api_key_info.get("qdrant_collection")
    qdrant = get_qdrant_service(
        str(collection) if collection and not is_admin else None,
        is_admin=is_admin
    )

    query_embedding = await embedding_service.embed_query(input_data.query)

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
    api_key_id: str
    title: str
    content: str
    document_type: str
    created_at: str
    updated_at: str
    doc_metadata: dict


async def get_document(input_data: GetDocumentInput) -> GetDocumentOutput | None:
    api_key_info = get_api_key_info()
    if not api_key_info:
        raise ValueError("API key not authenticated")

    is_admin = api_key_info.get("is_admin", False)
    api_key_id = api_key_info.get("id")
    doc_repo = get_document_repository(
        str(api_key_id) if api_key_id and not is_admin else None
    )

    doc = doc_repo.get_by_id(input_data.document_id)

    if not doc:
        return None

    return GetDocumentOutput(
        id=doc.id,
        api_key_id=doc.api_key_id,
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
    api_key_info = get_api_key_info()
    if not api_key_info:
        raise ValueError("API key not authenticated")

    is_admin = api_key_info.get("is_admin", False)
    api_key_id = api_key_info.get("id")
    doc_repo = get_document_repository(
        str(api_key_id) if api_key_id and not is_admin else None
    )

    docs = doc_repo.list_all(limit=input_data.limit, offset=input_data.offset)

    documents = [
        GetDocumentOutput(
            id=d.id,
            api_key_id=d.api_key_id,
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
    api_key_info = get_api_key_info()
    if not api_key_info:
        raise ValueError("API key not authenticated")

    is_admin = api_key_info.get("is_admin", False)
    api_key_id = api_key_info.get("id")
    collection = api_key_info.get("qdrant_collection")
    doc_repo = get_document_repository(
        str(api_key_id) if api_key_id and not is_admin else None
    )
    qdrant = get_qdrant_service(
        str(collection) if collection and not is_admin else None,
        is_admin=is_admin
    )

    doc = doc_repo.get_by_id(input_data.document_id)

    if not doc:
        return DeleteDocumentOutput(
            success=False,
            message="Document not found",
        )

    qdrant.delete_by_document_id(input_data.document_id)

    doc_repo.delete(input_data.document_id)

    return DeleteDocumentOutput(
        success=True,
        message="Document deleted successfully",
    )
