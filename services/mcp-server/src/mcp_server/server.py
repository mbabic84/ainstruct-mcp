import logging

from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan
from shared.config import settings
from starlette.requests import Request
from starlette.responses import PlainTextResponse

from mcp_server.tools.auth import setup_auth
from mcp_server.tools.cat_tools import (
    CreateCatInput,
    RevokeCatInput,
    RotateCatInput,
    create_cat,
    list_cats,
    revoke_cat,
    rotate_cat,
)
from mcp_server.tools.collection_tools import (
    CreateCollectionInput,
    DeleteCollectionInput,
    GetCollectionInput,
    RenameCollectionInput,
    create_collection,
    delete_collection,
    get_collection,
    list_collections,
    rename_collection,
)
from mcp_server.tools.document_tools import (
    DeleteDocumentInput,
    GetDocumentInput,
    ListDocumentsInput,
    MoveDocumentInput,
    SearchDocumentsInput,
    StoreDocumentInput,
    UpdateDocumentInput,
    delete_document,
    get_document,
    list_documents,
    move_document,
    search_documents,
    store_document,
    update_document,
)

log = logging.getLogger(__name__)


@lifespan
async def db_migrations_lifespan(server):
    log.info("Running database migrations...")
    try:
        from alembic import command
        from alembic.config import Config
        from sqlalchemy import create_engine, text

        sync_url = settings.database_url.replace("+asyncpg", "")
        engine = create_engine(sync_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", sync_url)
        command.upgrade(alembic_cfg, "head")
        log.info("Migrations applied successfully!")
    except Exception as e:
        log.error(f"Migration failed: {e}")
        raise
    yield {}


mcp = FastMCP(
    name="AI Document Memory",
    instructions="MCP server for storing and searching markdown documents with semantic embeddings. Use this to store knowledge base documents, notes, and retrieve relevant information using semantic search.",
    lifespan=db_migrations_lifespan,
)


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


@mcp.tool()
async def store_document_tool(
    title: str,
    content: str,
    document_type: str = "markdown",
    doc_metadata: dict | None = None,
    collection_id: str | None = None,
) -> dict:
    """
    Store a markdown document with automatic chunking and embedding generation.

    Args:
        title: Document title
        content: Markdown content
        document_type: Type of document (markdown, pdf, docx, html, text, json)
        doc_metadata: Optional custom metadata
        collection_id: Optional UUID of the collection to store the document in

    Returns:
        Document ID, chunk count, and total token count
    """
    result = await store_document(
        StoreDocumentInput(
            title=title,
            content=content,
            document_type=document_type,
            doc_metadata=doc_metadata or {},
            collection_id=collection_id,
        )
    )
    return {
        "document_id": result.document_id,
        "chunk_count": result.chunk_count,
        "token_count": result.token_count,
        "message": result.message,
    }


@mcp.tool()
async def search_documents_tool(
    query: str,
    max_results: int = 5,
    max_tokens: int = 2000,
) -> dict:
    """
    Semantic search across all documents using embeddings.

    Args:
        query: Search query string
        max_results: Maximum number of results to return (default: 5)
        max_tokens: Token budget for response (default: 2000)

    Returns:
        List of relevant chunks with source document info, formatted as markdown
    """
    result = await search_documents(
        SearchDocumentsInput(
            query=query,
            max_results=max_results,
            max_tokens=max_tokens,
        )
    )
    return {
        "results": [r.model_dump() for r in result.results],
        "total_results": result.total_results,
        "tokens_used": result.tokens_used,
        "formatted_context": result.formatted_context,
    }


@mcp.tool()
async def get_document_tool(document_id: str) -> dict:
    """
    Retrieve full document by ID.

    Args:
        document_id: UUID of the document

    Returns:
        Full document content with metadata
    """
    result = await get_document(GetDocumentInput(document_id=document_id))
    if result is None:
        return {"error": "Document not found"}
    return result.model_dump()


@mcp.tool()
async def list_documents_tool(limit: int = 50, offset: int = 0) -> dict:
    """
    List all stored documents with pagination.

    Args:
        limit: Number of documents to return (default: 50)
        offset: Pagination offset (default: 0)

    Returns:
        List of documents with titles and metadata
    """
    result = await list_documents(ListDocumentsInput(limit=limit, offset=offset))
    return {
        "documents": [d.model_dump() for d in result.documents],
        "total": result.total,
    }


@mcp.tool()
async def delete_document_tool(document_id: str) -> dict:
    """
    Delete a document and all its chunks from storage.

    Args:
        document_id: UUID of the document to delete

    Returns:
        Success confirmation
    """
    result = await delete_document(DeleteDocumentInput(document_id=document_id))
    return result.model_dump()


@mcp.tool()
async def update_document_tool(
    document_id: str,
    title: str,
    content: str,
    document_type: str = "markdown",
    doc_metadata: dict | None = None,
) -> dict:
    """
    Update an existing document, replacing its content and re-generating embeddings.

    Args:
        document_id: UUID of the document to update
        title: New document title
        content: New markdown content
        document_type: Type of document (markdown, pdf, docx, html, text, json)
        doc_metadata: Optional custom metadata

    Returns:
        Document ID, chunk count, and total token count
    """
    result = await update_document(
        UpdateDocumentInput(
            document_id=document_id,
            title=title,
            content=content,
            document_type=document_type,
            doc_metadata=doc_metadata or {},
        )
    )
    return {
        "document_id": result.document_id,
        "chunk_count": result.chunk_count,
        "token_count": result.token_count,
        "message": result.message,
    }


@mcp.tool()
async def move_document_tool(
    document_id: str,
    target_collection_id: str,
) -> dict:
    """
    Move a document to a different collection.

    Args:
        document_id: UUID of the document to move
        target_collection_id: UUID of the target collection

    Returns:
        Document ID, new collection ID, and success message
    """
    result = await move_document(
        MoveDocumentInput(
            document_id=document_id,
            target_collection_id=target_collection_id,
        )
    )
    return {
        "document_id": result.document_id,
        "new_collection_id": result.new_collection_id,
        "message": result.message,
    }


@mcp.tool()
async def create_collection_access_token_tool(
    label: str,
    collection_id: str,
    permission: str = "read_write",
    expires_in_days: int | None = None,
) -> dict:
    """
    Create a new Collection Access Token for a specific collection.

    Args:
        label: Descriptive label for the Collection Access Token
        collection_id: UUID of the collection to grant access to
        permission: Permission level ("read" or "read_write"). Default: "read_write"
        expires_in_days: Optional expiry in days

    Returns:
        Created Collection Access Token (only shown once)
    """
    result = await create_cat(
        CreateCatInput(
            label=label,
            collection_id=collection_id,
            permission=permission,
            expires_in_days=expires_in_days,
        )
    )
    return result.model_dump()


@mcp.tool()
async def list_collection_access_tokens_tool() -> dict:
    """
    List all Collection Access Tokens for the current user. Admins see all tokens.

    Returns:
        List of Collection Access Tokens (without the actual token values)
    """
    result = await list_cats()
    return {"keys": [k.model_dump() for k in result]}


@mcp.tool()
async def revoke_collection_access_token_tool(key_id: str) -> dict:
    """
    Revoke (deactivate) a Collection Access Token.

    Args:
        key_id: ID of the Collection Access Token to revoke

    Returns:
        Success confirmation
    """
    result = await revoke_cat(RevokeCatInput(key_id=key_id))
    return result


@mcp.tool()
async def rotate_collection_access_token_tool(key_id: str) -> dict:
    """
    Rotate a Collection Access Token. The old token is revoked and a new one is created.

    Args:
        key_id: ID of the Collection Access Token to rotate

    Returns:
        New Collection Access Token (only shown once)
    """
    result = await rotate_cat(RotateCatInput(key_id=key_id))
    return result.model_dump()


@mcp.tool()
async def create_collection_tool(name: str) -> dict:
    """
    Create a new collection owned by the authenticated user.

    Args:
        name: User-friendly name for the collection

    Returns:
        Created collection information
    """
    result = await create_collection(CreateCollectionInput(name=name))
    return result.model_dump()


@mcp.tool()
async def list_collections_tool() -> dict:
    """
    List all collections owned by the authenticated user.

    Returns:
        List of collections
    """
    result = await list_collections()
    return {"collections": [c.model_dump() for c in result]}


@mcp.tool()
async def get_collection_tool(collection_id: str) -> dict:
    """
    Get details of a specific collection.

    Args:
        collection_id: UUID of the collection

    Returns:
        Collection details with document and API key counts
    """
    result = await get_collection(GetCollectionInput(collection_id=collection_id))
    return result.model_dump()


@mcp.tool()
async def delete_collection_tool(collection_id: str) -> dict:
    """
    Delete a collection and all its documents. Requires no active API keys.

    Args:
        collection_id: UUID of the collection to delete

    Returns:
        Success confirmation
    """
    result = await delete_collection(DeleteCollectionInput(collection_id=collection_id))
    return result


@mcp.tool()
async def rename_collection_tool(collection_id: str, name: str) -> dict:
    """
    Rename a collection.

    Args:
        collection_id: UUID of the collection to rename
        name: New name for the collection

    Returns:
        Updated collection information
    """
    result = await rename_collection(
        RenameCollectionInput(
            collection_id=collection_id,
            name=name,
        )
    )
    return result.model_dump()


setup_auth(mcp)
