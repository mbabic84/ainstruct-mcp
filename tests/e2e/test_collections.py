"""
E2E tests for collection management tools.
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
SERVER_URL = os.environ["MCP_SERVER_URL"]
# Use HTTP transport (streamable HTTP, modern MCP protocol)
TRANSPORT = os.environ.get("MCP_TRANSPORT", "http")


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

    @pytest.mark.asyncio
    async def test_pat_can_access_all_collections(self):
        """Test PAT has access to all user collections."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Register and login
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )
            
            collection_ids = []
            
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"]) as auth_client:
                # Get default collection
                collections_result = await auth_client.call_tool("list_collections_tool", {})
                collection_ids.append(collections_result["collections"][0]["id"])
                
                # Create additional collections
                for i in range(2):
                    new_coll = await auth_client.call_tool("create_collection_tool", {
                        "name": f"PAT Test Collection {i+1}",
                    })
                    collection_ids.append(new_coll["id"])
                
                # Create PAT token
                pat_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "Collection Access PAT",
                })
                pat_token = pat_result["token"]
            
            # Use PAT to list collections - should see all
            async with MCPClient(SERVER_URL, auth_token=pat_token) as pat_client:
                collections_result = await pat_client.call_tool("list_collections_tool", {})
                
                collections = collections_result.get("collections", [])
                assert len(collections) >= 3, f"Expected at least 3 collections, got {len(collections)}"
                
                print(f"\nPAT can see {len(collections)} collections")


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
                await auth_client.call_tool("delete_collection_tool", {
                    "collection_id": new_collection_id,
                })
                
                print(f"\nDeleted collection: {new_collection_id}")
