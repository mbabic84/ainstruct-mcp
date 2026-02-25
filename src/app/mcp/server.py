import asyncio
import logging

from alembic import command
from alembic.config import Config
from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan

from ..config import settings
from ..tools.admin_tools import (
    DeleteUserInput,
    GetUserInput,
    ListUsersInput,
    SearchUsersInput,
    UpdateUserInput,
    delete_user,
    get_user,
    list_users,
    search_users,
    update_user,
)
from ..tools.auth import setup_auth
from ..tools.cat_tools import (
    CreateCatInput,
    RevokeCatInput,
    RotateCatInput,
    create_cat,
    list_cats,
    revoke_cat,
    rotate_cat,
)
from ..tools.collection_tools import (
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
from ..tools.document_tools import (
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
from ..tools.pat_tools import (
    CreatePatTokenInput,
    RevokePatTokenInput,
    RotatePatTokenInput,
    create_pat_token,
    list_pat_tokens,
    revoke_pat_token,
    rotate_pat_token,
)
from ..tools.user_tools import (
    LoginInput,
    RefreshInput,
    RegisterInput,
    user_login,
    user_profile,
    user_refresh,
    user_register,
)

log = logging.getLogger(__name__)


@lifespan
async def db_migrations_lifespan(server):
    log.info("Running database migrations...")
    try:
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{settings.db_path}")
        await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
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
    result = await store_document(StoreDocumentInput(
        title=title,
        content=content,
        document_type=document_type,
        doc_metadata=doc_metadata or {},
        collection_id=collection_id,
    ))
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
    result = await search_documents(SearchDocumentsInput(
        query=query,
        max_results=max_results,
        max_tokens=max_tokens,
    ))
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
    result = await update_document(UpdateDocumentInput(
        document_id=document_id,
        title=title,
        content=content,
        document_type=document_type,
        doc_metadata=doc_metadata or {},
    ))
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
    result = await move_document(MoveDocumentInput(
        document_id=document_id,
        target_collection_id=target_collection_id,
    ))
    return {
        "document_id": result.document_id,
        "new_collection_id": result.new_collection_id,
        "message": result.message,
    }


@mcp.tool()
async def user_register_tool(
    email: str,
    username: str,
    password: str,
) -> dict:
    """
    Register a new user account. This tool is public and does not require authentication.

    Args:
        email: User email address
        username: Unique username
        password: User password

    Returns:
        Created user information
    """
    result = await user_register(RegisterInput(
        email=email,
        username=username,
        password=password,
    ))
    return result.model_dump()


@mcp.tool()
async def user_login_tool(username: str, password: str) -> dict:
    """
    Authenticate a user and receive access and refresh tokens.

    Args:
        username: User username
        password: User password

    Returns:
        Access token, refresh token, and expiry information
    """
    result = await user_login(LoginInput(username=username, password=password))
    return result.model_dump()


@mcp.tool()
async def user_profile_tool() -> dict:
    """
    Get the current authenticated user's profile information.

    Returns:
        Current user profile
    """
    return await user_profile()


@mcp.tool()
async def user_refresh_tool(refresh_token: str) -> dict:
    """
    Refresh an access token using a valid refresh token.

    Args:
        refresh_token: Valid refresh token

    Returns:
        New access token, refresh token, and expiry information
    """
    result = await user_refresh(RefreshInput(refresh_token=refresh_token))
    return result.model_dump()


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
    result = await create_cat(CreateCatInput(
        label=label,
        collection_id=collection_id,
        permission=permission,
        expires_in_days=expires_in_days,
    ))
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
async def create_pat_token_tool(
    label: str,
    expires_in_days: int | None = None,
) -> dict:
    """
    Create a new Personal Access Token (PAT) for the authenticated user.

    Args:
        label: Descriptive label for the PAT
        expires_in_days: Optional expiry in days

    Returns:
        Created PAT token (only shown once)
    """
    result = await create_pat_token(CreatePatTokenInput(
        label=label,
        expires_in_days=expires_in_days,
    ))
    return result.model_dump()


@mcp.tool()
async def list_pat_tokens_tool() -> dict:
    """
    List all PAT tokens for the current user. Admins see all tokens.

    Returns:
        List of PAT tokens (without the actual token values)
    """
    result = await list_pat_tokens()
    return {"tokens": [t.model_dump() for t in result]}


@mcp.tool()
async def revoke_pat_token_tool(pat_id: str) -> dict:
    """
    Revoke (deactivate) a PAT token.

    Args:
        pat_id: ID of the PAT token to revoke

    Returns:
        Success confirmation
    """
    result = await revoke_pat_token(RevokePatTokenInput(pat_id=pat_id))
    return result


@mcp.tool()
async def rotate_pat_token_tool(pat_id: str) -> dict:
    """
    Rotate a PAT token. The old token is revoked and a new one is created.

    Args:
        pat_id: ID of the PAT token to rotate

    Returns:
        New PAT token (only shown once)
    """
    result = await rotate_pat_token(RotatePatTokenInput(pat_id=pat_id))
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
    result = await rename_collection(RenameCollectionInput(
        collection_id=collection_id,
        name=name,
    ))
    return result.model_dump()


@mcp.tool()
async def list_users_tool(limit: int = 50, offset: int = 0) -> dict:
    """
    List all users. Requires admin scope.

    Args:
        limit: Number of users to return (default: 50)
        offset: Pagination offset (default: 0)

    Returns:
        List of users
    """
    result = await list_users(ListUsersInput(limit=limit, offset=offset))
    return {"users": [u.model_dump() for u in result]}


@mcp.tool()
async def search_users_tool(query: str, limit: int = 50, offset: int = 0) -> dict:
    """
    Search users by username or email. Requires admin scope.

    Args:
        query: Search query (case-insensitive partial match on username or email)
        limit: Number of results to return (default: 50)
        offset: Pagination offset (default: 0)

    Returns:
        List of matching users
    """
    result = await search_users(SearchUsersInput(query=query, limit=limit, offset=offset))
    return {"users": [u.model_dump() for u in result]}


@mcp.tool()
async def get_user_tool(user_id: str) -> dict:
    """
    Get a specific user by ID. Requires admin scope.

    Args:
        user_id: UUID of the user

    Returns:
        User information
    """
    result = await get_user(GetUserInput(user_id=user_id))
    return result.model_dump()


@mcp.tool()
async def update_user_tool(
    user_id: str,
    email: str | None = None,
    username: str | None = None,
    password: str | None = None,
    is_active: bool | None = None,
    is_superuser: bool | None = None,
) -> dict:
    """
    Update a user. Requires admin scope.

    Args:
        user_id: UUID of the user to update
        email: New email address
        username: New username
        password: New password
        is_active: Account active status
        is_superuser: Superuser status

    Returns:
        Updated user information
    """
    result = await update_user(UpdateUserInput(
        user_id=user_id,
        email=email,
        username=username,
        password=password,
        is_active=is_active,
        is_superuser=is_superuser,
    ))
    return result.model_dump()


@mcp.tool()
async def delete_user_tool(user_id: str) -> dict:
    """
    Delete a user. Requires admin scope.

    Args:
        user_id: UUID of the user to delete

    Returns:
        Success confirmation
    """
    result = await delete_user(DeleteUserInput(user_id=user_id))
    return result


setup_auth(mcp)
