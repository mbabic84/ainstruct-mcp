from fastapi import APIRouter, HTTPException, Query, status

from app.db import get_collection_repository
from app.db.models import DocumentCreate
from app.db.qdrant import get_qdrant_service
from app.rest.deps import DbDep, UserDep
from app.rest.schemas import (
    DocumentCreate as DocumentCreateSchema,
)
from app.rest.schemas import (
    DocumentListItem,
    DocumentListResponse,
    DocumentResponse,
    DocumentStoreResponse,
    DocumentUpdate,
    DocumentUpdateResponse,
    ErrorResponse,
    MessageResponse,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from app.services.chunking import get_chunking_service
from app.services.embedding import get_embedding_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post(
    "",
    response_model=DocumentStoreResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": ErrorResponse, "description": "Collection not found"},
    },
)
async def store_document(
    body: DocumentCreateSchema,
    db: DbDep,
    user: UserDep,
):
    from app.db.repository import get_document_repository

    collection_repo = get_collection_repository()
    collection = await collection_repo.get_by_id(body.collection_id)

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COLLECTION_NOT_FOUND", "message": "Collection not found"},
        )

    if collection["user_id"] != user.user_id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Cannot store document in another user's collection"},
        )

    doc_repo = get_document_repository()
    embedding_service = get_embedding_service()
    chunking_service = get_chunking_service()

    doc_create = DocumentCreate(
        collection_id=body.collection_id,
        title=body.title,
        content=body.content,
        document_type=body.document_type,
        doc_metadata=body.metadata or {},
    )

    document = await doc_repo.create(doc_create)

    chunks = chunking_service.chunk_markdown(body.content, body.title)
    token_count = sum(c.get("token_count", 0) for c in chunks)

    chunk_data = [
        {
            "chunk_index": c.get("chunk_index", i),
            "content": c.get("content", ""),
            "title": c.get("title", body.title),
            "document_id": document.id,
        }
        for i, c in enumerate(chunks)
    ]

    texts = [c.get("content", "") for c in chunks]
    vectors = await embedding_service.embed_texts(texts)

    qdrant_service = get_qdrant_service(collection["qdrant_collection"])
    await qdrant_service.upsert_chunks(chunk_data, vectors)

    return DocumentStoreResponse(
        id=document.id,
        title=document.title,
        collection_id=document.collection_id,
        chunk_count=len(chunks),
        token_count=token_count,
        created_at=document.created_at,
    )


@router.get(
    "",
    response_model=DocumentListResponse,
)
async def list_documents(
    db: DbDep,
    user: UserDep,
    collection_id: str | None = Query(None, description="Filter by collection"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    from app.db.repository import get_document_repository

    collection_repo = get_collection_repository()
    doc_repo = get_document_repository()

    if collection_id:
        collection = await collection_repo.get_by_id(collection_id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "COLLECTION_NOT_FOUND", "message": "Collection not found"},
            )
        if collection["user_id"] != user.user_id and not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Cannot access another user's collection"},
            )
        documents = await doc_repo.list_all_for_user(user.user_id, limit, offset)
        total = await doc_repo.count_by_collection(collection_id)
    else:
        documents = await doc_repo.list_all_for_user(user.user_id, limit, offset)
        total = len(documents)

    items = [
        DocumentListItem(
            id=d.id,
            title=d.title,
            collection_id=d.collection_id,
            document_type=d.document_type,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in documents
    ]

    return DocumentListResponse(
        documents=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def get_document(
    document_id: str,
    db: DbDep,
    user: UserDep,
):
    from app.db.repository import get_document_repository

    doc_repo = get_document_repository()
    collection_repo = get_collection_repository()

    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found"},
        )

    collection = await collection_repo.get_by_id(document.collection_id)
    if collection and collection["user_id"] != user.user_id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Cannot access another user's document"},
        )

    return DocumentResponse(
        id=document.id,
        title=document.title,
        content=document.content,
        collection_id=document.collection_id,
        document_type=document.document_type,
        created_at=document.created_at,
        updated_at=document.updated_at,
        metadata=document.doc_metadata,
    )


@router.patch(
    "/{document_id}",
    response_model=DocumentUpdateResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def update_document(
    document_id: str,
    body: DocumentUpdate,
    db: DbDep,
    user: UserDep,
):
    from app.db.repository import get_document_repository

    doc_repo = get_document_repository()
    collection_repo = get_collection_repository()
    embedding_service = get_embedding_service()
    chunking_service = get_chunking_service()

    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found"},
        )

    collection = await collection_repo.get_by_id(document.collection_id)
    if collection and collection["user_id"] != user.user_id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Cannot update another user's document"},
        )

    update_data = {}
    if body.title is not None:
        update_data["title"] = body.title
    if body.content is not None:
        update_data["content"] = body.content
    if body.document_type is not None:
        update_data["document_type"] = body.document_type
    if body.metadata is not None:
        update_data["doc_metadata"] = body.metadata

    if body.content is not None or body.title is not None:
        title = body.title or document.title
        content = body.content or document.content

        chunks = chunking_service.chunk_markdown(content, title)

        chunk_data = [
            {
                "chunk_index": c.get("chunk_index", i),
                "content": c.get("content", ""),
                "title": c.get("title", title),
                "document_id": document.id,
            }
            for i, c in enumerate(chunks)
        ]

        texts = [c.get("content", "") for c in chunks]
        vectors = await embedding_service.embed_texts(texts)

        if collection:
            qdrant_service = get_qdrant_service(collection["qdrant_collection"])
            await qdrant_service.delete_by_document_id(document.id)
            await qdrant_service.upsert_chunks(chunk_data, vectors)

    if update_data:
        updated = await doc_repo.update(document_id, **update_data)
    else:
        updated = await doc_repo.get_by_id(document_id)

    return DocumentUpdateResponse(
        id=updated.id,
        title=updated.title,
        chunk_count=None,
        token_count=None,
        updated_at=updated.updated_at,
    )


@router.delete(
    "/{document_id}",
    response_model=MessageResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def delete_document(
    document_id: str,
    db: DbDep,
    user: UserDep,
):
    from app.db.repository import get_document_repository

    doc_repo = get_document_repository()
    collection_repo = get_collection_repository()

    document = await doc_repo.get_by_id(document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found"},
        )

    collection = await collection_repo.get_by_id(document.collection_id)
    if collection and collection["user_id"] != user.user_id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Cannot delete another user's document"},
        )

    if collection:
        qdrant_service = get_qdrant_service(collection["qdrant_collection"])
        await qdrant_service.delete_by_document_id(document.id)

    await doc_repo.delete(document_id)
    return MessageResponse(message="Document deleted successfully")


@router.post(
    "/search",
    response_model=SearchResponse,
)
async def search_documents(
    body: SearchRequest,
    db: DbDep,
    user: UserDep,
):

    collection_repo = get_collection_repository()
    embedding_service = get_embedding_service()

    if body.collection_id:
        collection = await collection_repo.get_by_id(body.collection_id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "COLLECTION_NOT_FOUND", "message": "Collection not found"},
            )
        if collection["user_id"] != user.user_id and not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Cannot search another user's collection"},
            )
        collection_ids = [body.collection_id]
        collection_names = {collection["id"]: collection["name"]}
    else:
        collections = await collection_repo.list_by_user(user.user_id)
        collection_ids = [c["id"] for c in collections]
        collection_names = {c["id"]: c["name"] for c in collections}
        if not collection_ids:
            return SearchResponse(
                results=[],
                total_results=0,
                tokens_used=0,
                formatted_context="",
            )

    query_vector = await embedding_service.embed_query(body.query)

    all_results = []
    for coll_id in collection_ids:
        collection = await collection_repo.get_by_id(coll_id)
        if not collection:
            continue

        qdrant_service = get_qdrant_service(collection["qdrant_collection"])
        results = await qdrant_service.search(
            query_vector=query_vector,
            limit=body.max_results,
        )

        for r in results:
            r["collection"] = collection_names.get(coll_id, "unknown")
            all_results.append(r)

    all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    all_results = all_results[: body.max_results]

    tokens_used = 0
    formatted_parts: list[str] = []
    result_items = []

    for r in all_results:
        content = r.get("content", "")
        tokens_used += len(content.split())

        result_items.append(
            SearchResultItem(
                document_id=r.get("id", ""),
                title=r.get("title", ""),
                chunk_index=r.get("chunk_index", 0),
                content=content,
                score=r.get("score", 0),
                collection=r.get("collection", ""),
            )
        )

        if formatted_parts:
            formatted_parts.append("\n\n---\n\n")
        formatted_parts.append(f"## {r.get('title', '')}\n\n{content}")

    formatted_context = "".join(formatted_parts)

    return SearchResponse(
        results=result_items,
        total_results=len(all_results),
        tokens_used=tokens_used,
        formatted_context=formatted_context,
    )
