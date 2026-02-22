from fastmcp import FastMCP

from ..tools.auth import setup_auth
from ..tools.document_tools import (
    DeleteDocumentInput,
    GetDocumentInput,
    ListDocumentsInput,
    SearchDocumentsInput,
    StoreDocumentInput,
    UpdateDocumentInput,
    delete_document,
    get_document,
    list_documents,
    search_documents,
    store_document,
    update_document,
)

mcp = FastMCP(
    name="AI Document Memory",
    instructions="MCP server for storing and searching markdown documents with semantic embeddings. Use this to store knowledge base documents, notes, and retrieve relevant information using semantic search.",
)


@mcp.tool()
async def store_document_tool(
    title: str,
    content: str,
    document_type: str = "markdown",
    doc_metadata: dict | None = None,
) -> dict:
    """
    Store a markdown document with automatic chunking and embedding generation.

    Args:
        title: Document title
        content: Markdown content
        document_type: Type of document (markdown, pdf, docx, html, text, json)
        doc_metadata: Optional custom metadata

    Returns:
        Document ID, chunk count, and total token count
    """
    result = await store_document(StoreDocumentInput(
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


setup_auth(mcp)
