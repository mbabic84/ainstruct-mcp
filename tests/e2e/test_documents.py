"""
E2E tests for document operations (store, search, get, list, update, delete).
"""
import os
import pytest

from tests.e2e.mcp_client_test import (
    MCPClient,
    generate_test_id,
    register_test_user,
    login_user,
)


# Production server URL
SERVER_URL = os.environ.get("MCP_SERVER_URL", "https://ainstruct.kralicinora.cz/mcp")
TRANSPORT = os.environ.get("MCP_TRANSPORT", "http")


class TestDocumentOperations:
    """Test document CRUD operations with API key."""
    
    @pytest.mark.asyncio
    async def test_store_and_search_document(self):
        """Test storing and searching documents."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Setup: register, login, create API key
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )
            
            collection_id = None
            api_key = None
            
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"]) as auth_client:
                # Get collection and create API key
                collections_result = await auth_client.call_tool("list_collections_tool", {})
                collection_id = collections_result["collections"][0]["id"]
                
                key_result = await auth_client.call_tool("create_api_key_tool", {
                    "label": "Doc Test Key",
                    "collection_id": collection_id,
                    "permission": "read_write",
                })
                api_key = key_result["key"]
            
            # Use API key for document operations
            async with MCPClient(SERVER_URL, auth_token=api_key) as doc_client:
                # Store a document
                store_result = await doc_client.call_tool("store_document_tool", {
                    "title": "Test Document",
                    "content": "# Test Document\n\nThis is a test document about Python programming and machine learning.",
                    "document_type": "markdown",
                })
                
                assert "document_id" in store_result
                document_id = store_result["document_id"]
                
                print(f"\nStored document: {document_id}")
                print(f"  Chunks: {store_result.get('chunk_count')}")
                print(f"  Tokens: {store_result.get('token_count')}")
                
                # Search for the document
                search_result = await doc_client.call_tool("search_documents_tool", {
                    "query": "Python programming",
                    "max_results": 5,
                })
                
                assert search_result.get("total_results", 0) >= 1
                
                print(f"\nSearch results: {search_result.get('total_results')}")
                
                # Get the document
                get_result = await doc_client.call_tool("get_document_tool", {
                    "document_id": document_id,
                })
                
                assert get_result.get("title") == "Test Document"
                assert "Python" in get_result.get("content", "")
                
                print(f"\nRetrieved document: {get_result.get('title')}")
                
                # List documents
                list_result = await doc_client.call_tool("list_documents_tool", {
                    "limit": 10,
                })
                
                assert list_result.get("total", 0) >= 1
                
                print(f"\nTotal documents: {list_result.get('total')}")
                
                # Update the document
                update_result = await doc_client.call_tool("update_document_tool", {
                    "document_id": document_id,
                    "title": "Updated Test Document",
                    "content": "# Updated Document\n\nThis document was updated. It covers JavaScript now.",
                    "document_type": "markdown",
                })
                
                assert update_result.get("document_id") == document_id
                
                print(f"\nUpdated document: {update_result.get('document_id')}")
                
                # Delete the document
                delete_result = await doc_client.call_tool("delete_document_tool", {
                    "document_id": document_id,
                })
                
                assert delete_result.get("success") is True or "success" in str(delete_result).lower()
                
                print(f"\nDeleted document: {document_id}")
