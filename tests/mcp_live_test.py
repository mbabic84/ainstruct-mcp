"""
Live integration tests for ainstruct-mcp production server.
Tests against https://ainstruct.kralicinora.cz/mcp

Run with: docker build -f Dockerfile.mcp-client -t mcp-client-test . && docker run --rm mcp-client-test
"""
import os
import pytest
import uuid

from mcp_client_test import (
    MCPClient,
    generate_test_id,
    register_test_user,
    login_user,
    create_api_key,
)


# Production server URL
SERVER_URL = os.environ.get("MCP_SERVER_URL", "https://ainstruct.kralicinora.cz/mcp")
# Use HTTP transport (streamable HTTP, modern MCP protocol)
TRANSPORT = os.environ.get("MCP_TRANSPORT", "http")


class TestMCPServerHealth:
    """Test basic server health and availability."""
    
    @pytest.mark.asyncio
    async def test_server_is_reachable(self):
        """Verify the MCP server is reachable and responds to initialize."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            assert client.session is not None
    
    @pytest.mark.asyncio
    async def test_list_tools_public(self):
        """List tools should work without authentication (public tools exist)."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            tools = await client.list_tools()
            
            # Should have all the expected tools
            tool_names = {t["name"] for t in tools}
            
            # Document tools
            assert "store_document_tool" in tool_names
            assert "search_documents_tool" in tool_names
            assert "get_document_tool" in tool_names
            assert "list_documents_tool" in tool_names
            assert "update_document_tool" in tool_names
            assert "delete_document_tool" in tool_names
            
            # User authentication tools
            assert "user_register_tool" in tool_names
            assert "user_login_tool" in tool_names
            assert "user_profile_tool" in tool_names
            assert "user_refresh_tool" in tool_names
            assert "promote_to_admin_tool" in tool_names
            
            # API key tools
            assert "create_api_key_tool" in tool_names
            assert "list_api_keys_tool" in tool_names
            assert "revoke_api_key_tool" in tool_names
            assert "rotate_api_key_tool" in tool_names
            
            # Collection tools
            assert "create_collection_tool" in tool_names
            assert "list_collections_tool" in tool_names
            assert "get_collection_tool" in tool_names
            assert "delete_collection_tool" in tool_names
            assert "rename_collection_tool" in tool_names
            
            # Admin tools
            assert "list_users_tool" in tool_names
            assert "get_user_tool" in tool_names
            assert "update_user_tool" in tool_names
            assert "delete_user_tool" in tool_names
            
            print(f"\nFound {len(tools)} tools")


class TestUserRegistration:
    """Test user registration flow."""
    
    @pytest.mark.asyncio
    async def test_register_new_user(self):
        """Register a new user account."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            result = await register_test_user(client, test_id)
            
            assert "user" in result
            user = result["user"]
            
            # Check user was created
            assert user.get("id") is not None
            assert user.get("email") == result["email"]
            assert user.get("username") == result["username"]
            assert user.get("is_active") is True
            assert user.get("is_superuser") is False
            
            print(f"\nRegistered user: {user.get('username')} (id: {user.get('id')})")


class TestUserLogin:
    """Test user login and token management."""
    
    @pytest.mark.asyncio
    async def test_login_flow(self):
        """Test complete login flow: register -> login -> profile."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Register
            reg_result = await register_test_user(client, test_id)
            
            # Login
            login_result = await login_user(
                client, 
                reg_result["username"], 
                reg_result["password"]
            )
            
            assert "access_token" in login_result
            assert "refresh_token" in login_result
            assert login_result.get("token_type") == "bearer"
            assert login_result.get("expires_in") > 0
            
            access_token = login_result["access_token"]
            refresh_token = login_result["refresh_token"]
            
            print(f"\nLogged in, got access token: {access_token[:50]}...")
            
            # Test profile with JWT token
            async with MCPClient(SERVER_URL, auth_token=access_token, transport=TRANSPORT) as auth_client:
                profile = await auth_client.call_tool("user_profile_tool", {})
                
                assert profile.get("username") == reg_result["username"]
                assert profile.get("email") == reg_result["email"]
                
                print(f"\nGot profile: {profile.get('username')}")
            
            # Test token refresh
            refresh_result = await client.call_tool("user_refresh_tool", {
                "refresh_token": refresh_token,
            })
            
            assert "access_token" in refresh_result
            assert refresh_result["access_token"] != access_token
            
            print(f"\nRefreshed token successfully")


class TestCollections:
    """Test collection management."""
    
    @pytest.mark.asyncio
    async def test_default_collection_created(self):
        """Verify default collection is created on registration."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Register
            reg_result = await register_test_user(client, test_id)
            
            # Login
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )
            
            # List collections with JWT token
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"]) as auth_client:
                collections_result = await auth_client.call_tool("list_collections_tool", {})
                
                collections = collections_result.get("collections", [])
                assert len(collections) >= 1
                
                # Find default collection
                default_coll = next(
                    (c for c in collections if c["name"] == "default"),
                    None
                )
                assert default_coll is not None
                assert default_coll.get("id") is not None
                
                print(f"\nFound default collection: {default_coll.get('id')}")


class TestAPIKeys:
    """Test API key management."""
    
    @pytest.mark.asyncio
    async def test_create_and_list_api_keys(self):
        """Test creating and listing API keys."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Register and login
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )
            
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"]) as auth_client:
                # Get collections
                collections_result = await auth_client.call_tool("list_collections_tool", {})
                collection_id = collections_result["collections"][0]["id"]
                
                # Create API key
                key_result = await auth_client.call_tool("create_api_key_tool", {
                    "label": "Test Key",
                    "collection_id": collection_id,
                    "permission": "read_write",
                })
                
                assert "key" in key_result
                assert key_result["key"].startswith("ak_live_")
                
                api_key = key_result["key"]
                print(f"\nCreated API key: {api_key[:30]}...")
                
                # List API keys
                keys_result = await auth_client.call_tool("list_api_keys_tool", {})
                
                keys = keys_result.get("keys", [])
                assert len(keys) >= 1
                
                # Find our key (key value is not returned in list)
                our_key = next(
                    (k for k in keys if k.get("label") == "Test Key"),
                    None
                )
                assert our_key is not None
                
                print(f"\nListed {len(keys)} API keys")


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


class TestReadonlyPermissions:
    """Test read-only API key permissions."""
    
    @pytest.mark.asyncio
    async def test_readonly_key_denies_write(self):
        """Verify read-only key cannot perform write operations."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Setup
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )
            
            collection_id = None
            readonly_key = None
            
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"]) as auth_client:
                collections_result = await auth_client.call_tool("list_collections_tool", {})
                collection_id = collections_result["collections"][0]["id"]
                
                # Create read-only key
                key_result = await auth_client.call_tool("create_api_key_tool", {
                    "label": "Readonly Key",
                    "collection_id": collection_id,
                    "permission": "read",  # Read-only!
                })
                readonly_key = key_result["key"]
            
            # Test with read-only key
            async with MCPClient(SERVER_URL, auth_token=readonly_key) as ro_client:
                # Should be able to list documents
                list_result = await ro_client.call_tool("list_documents_tool", {})
                print(f"\nRead-only key can list documents: {list_result.get('total', 0)} documents")
                
                # Should NOT be able to store
                with pytest.raises(Exception) as exc_info:
                    await ro_client.call_tool("store_document_tool", {
                        "title": "Should Fail",
                        "content": "This should not work",
                    })
                
                assert "permission" in str(exc_info.value).lower() or "insufficient" in str(exc_info.value).lower()
                print(f"\nRead-only key correctly denied write: {exc_info.value}")


class TestCollectionManagement:
    """Test collection CRUD operations."""
    
    @pytest.mark.asyncio
    async def test_create_rename_delete_collection(self):
        """Test creating, renaming, and deleting collections."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Setup
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )
            
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"]) as auth_client:
                # Create new collection
                create_result = await auth_client.call_tool("create_collection_tool", {
                    "name": "Test Collection",
                })
                
                new_collection_id = create_result.get("id")
                assert new_collection_id is not None
                assert create_result.get("name") == "Test Collection"
                
                print(f"\nCreated collection: {new_collection_id}")
                
                # Get collection details
                get_result = await auth_client.call_tool("get_collection_tool", {
                    "collection_id": new_collection_id,
                })
                
                assert get_result.get("name") == "Test Collection"
                assert get_result.get("document_count") == 0
                
                print(f"\nGot collection details: {get_result.get('name')}")
                
                # Rename collection
                rename_result = await auth_client.call_tool("rename_collection_tool", {
                    "collection_id": new_collection_id,
                    "name": "Renamed Collection",
                })
                
                assert rename_result.get("name") == "Renamed Collection"
                
                print(f"\nRenamed collection to: {rename_result.get('name')}")
                
                # Delete collection
                delete_result = await auth_client.call_tool("delete_collection_tool", {
                    "collection_id": new_collection_id,
                })
                
                print(f"\nDeleted collection: {new_collection_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
