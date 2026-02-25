"""
E2E tests for PAT token management and document access.
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


class TestPATTokens:
    """Test PAT token management and authentication."""
    
    @pytest.mark.asyncio
    async def test_create_and_list_pat_tokens(self):
        """Test creating and listing PAT tokens."""
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
                # Create PAT token
                pat_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "Test PAT Token",
                })
                
                assert "token" in pat_result
                assert pat_result["token"].startswith("pat_live_")
                
                pat_token = pat_result["token"]
                print(f"\nCreated PAT token: {pat_token[:30]}...")
                
                # List PAT tokens
                list_result = await auth_client.call_tool("list_pat_tokens_tool", {})
                
                tokens = list_result.get("tokens", [])
                assert len(tokens) >= 1
                
                # Find our token (raw token not returned in list)
                our_token = next(
                    (t for t in tokens if t.get("label") == "Test PAT Token"),
                    None
                )
                assert our_token is not None
                
                print(f"\nListed {len(tokens)} PAT tokens")
    
    @pytest.mark.asyncio
    async def test_pat_token_authentication(self):
        """Test authenticating with PAT token."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Register and login
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )
            
            pat_token = None
            
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"]) as auth_client:
                # Create PAT token
                pat_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "Auth Test PAT",
                })
                pat_token = pat_result["token"]
            
            # Use PAT token for authentication
            async with MCPClient(SERVER_URL, auth_token=pat_token) as pat_client:
                # Should be able to access user profile
                profile = await pat_client.call_tool("user_profile_tool", {})
                
                assert profile.get("username") == reg_result["username"]
                assert profile.get("email") == reg_result["email"]
                
                print(f"\nPAT token auth worked for user: {profile.get('username')}")
    
    @pytest.mark.asyncio
    async def test_pat_token_with_custom_expiry(self):
        """Test creating PAT token with custom expiry."""
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
                # Create PAT token with 30-day expiry
                pat_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "30-day PAT",
                    "expires_in_days": 30,
                })
                
                assert "token" in pat_result
                assert pat_result["token"].startswith("pat_live_")

                print("\nCreated PAT with 30-day expiry")

    @pytest.mark.asyncio
    async def test_pat_token_rotate(self):
        """Test rotating PAT token."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Register and login
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )
            
            pat_id = None
            
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"]) as auth_client:
                # Create PAT token
                pat_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "Rotate Test PAT",
                })
                pat_id = pat_result["id"]
                old_token = pat_result["token"]
                
                # Rotate the token
                rotate_result = await auth_client.call_tool("rotate_pat_token_tool", {
                    "pat_id": pat_id,
                })
                
                assert "token" in rotate_result
                assert rotate_result["token"].startswith("pat_live_")
                assert rotate_result["token"] != old_token
                
                new_token = rotate_result["token"]
                print(f"\nRotated PAT token: {new_token[:30]}...")
    
    @pytest.mark.asyncio
    async def test_pat_token_revoke(self):
        """Test revoking PAT token."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Register and login
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )
            
            pat_id = None
            pat_token = None
            
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"]) as auth_client:
                # Create PAT token
                pat_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "Revoke Test PAT",
                })
                pat_id = pat_result["id"]
                pat_token = pat_result["token"]
                
                # Revoke the token
                revoke_result = await auth_client.call_tool("revoke_pat_token_tool", {
                    "pat_id": pat_id,
                })
                
                assert revoke_result.get("success") is True
                print(f"\nRevoked PAT token: {pat_id}")
            
            # Verify revoked token no longer works - error is returned as string response
            async with MCPClient(SERVER_URL, auth_token=pat_token) as revoked_client:
                profile_result = await revoked_client.call_tool("user_profile_tool", {})
                
                # Error is returned as string, not raised as exception
                error_msg = str(profile_result).lower()
                assert "invalid" in error_msg or "expired" in error_msg, f"Expected invalid/expired error, got: {profile_result}"
                print(f"\nRevoked token correctly rejected: {profile_result}")


class TestPATDocumentAccess:
    """Test PAT token document access across all user collections."""
    
    @pytest.mark.asyncio
    async def test_pat_document_operations(self):
        """Test PAT can create, get, update, delete documents."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Register and login
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )
            
            pat_token = None
            collection_id = None
            
            # Get collection ID and create PAT token
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"]) as auth_client:
                collections_result = await auth_client.call_tool("list_collections_tool", {})
                collection_id = collections_result["collections"][0]["id"]
                
                pat_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "Doc Test PAT",
                })
                pat_token = pat_result["token"]
            
            # Use PAT for document operations
            async with MCPClient(SERVER_URL, auth_token=pat_token) as pat_client:
                # Store document
                store_result = await pat_client.call_tool("store_document_tool", {
                    "title": "PAT Test Document",
                    "content": "# PAT Test\n\nThis document is stored via PAT token.",
                    "document_type": "markdown",
                })
                
                assert "document_id" in store_result
                document_id = store_result["document_id"]
                print(f"\nPAT stored document: {document_id}")
                
                # Get document
                get_result = await pat_client.call_tool("get_document_tool", {
                    "document_id": document_id,
                })
                
                assert get_result.get("title") == "PAT Test Document"
                print(f"\nPAT retrieved document: {get_result.get('title')}")
                
                # Update document
                update_result = await pat_client.call_tool("update_document_tool", {
                    "document_id": document_id,
                    "title": "Updated PAT Document",
                    "content": "# Updated\n\nThis was updated via PAT.",
                    "document_type": "markdown",
                })
                
                assert update_result.get("document_id") == document_id
                print(f"\nPAT updated document")
                
                # Delete document
                delete_result = await pat_client.call_tool("delete_document_tool", {
                    "document_id": document_id,
                })
                
                assert delete_result.get("success") is True
                print(f"\nPAT deleted document")

    @pytest.mark.asyncio
    async def test_pat_list_all_documents(self):
        """Test PAT list_documents returns all user's documents across collections."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Register and login
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )
            
            pat_token = None
            collection_ids = []
            
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"]) as auth_client:
                # Get default collection
                collections_result = await auth_client.call_tool("list_collections_tool", {})
                collection_ids.append(collections_result["collections"][0]["id"])
                
                # Create a second collection
                new_coll = await auth_client.call_tool("create_collection_tool", {
                    "name": "Second Collection",
                })
                collection_ids.append(new_coll["id"])
                
                # Create API key for each collection to store documents
                key1_result = await auth_client.call_tool("create_collection_access_token_tool", {
                    "label": "Key1",
                    "collection_id": collection_ids[0],
                    "permission": "read_write",
                })
                key2_result = await auth_client.call_tool("create_collection_access_token_tool", {
                    "label": "Key2",
                    "collection_id": collection_ids[1],
                    "permission": "read_write",
                })
                
                # Create PAT token
                pat_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "List Test PAT",
                })
                pat_token = pat_result["token"]
            
            # Store documents in each collection using API keys
            for key, coll_id in [(key1_result["key"], collection_ids[0]), 
                                  (key2_result["key"], collection_ids[1])]:
                async with MCPClient(SERVER_URL, auth_token=key) as key_client:
                    await key_client.call_tool("store_document_tool", {
                        "title": f"Doc in {coll_id[:8]}",
                        "content": f"Document in collection {coll_id}",
                        "document_type": "markdown",
                    })
            
            # Use PAT to list all documents (should see both)
            async with MCPClient(SERVER_URL, auth_token=pat_token) as pat_client:
                list_result = await pat_client.call_tool("list_documents_tool", {
                    "limit": 50,
                })
                
                total = list_result.get("total", 0)
                assert total >= 2, f"Expected at least 2 documents, got {total}"
                print(f"\nPAT listed {total} documents across all collections")

    @pytest.mark.asyncio
    async def test_pat_search_all_collections(self):
        """Test PAT search returns results from all user collections."""
        test_id = generate_test_id()
        
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Register and login
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )
            
            pat_token = None
            collection_ids = []
            
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"]) as auth_client:
                # Get default collection
                collections_result = await auth_client.call_tool("list_collections_tool", {})
                collection_ids.append(collections_result["collections"][0]["id"])
                
                # Create a second collection
                new_coll = await auth_client.call_tool("create_collection_tool", {
                    "name": "Search Test Collection",
                })
                collection_ids.append(new_coll["id"])
                
                # Create API keys for each collection
                key1_result = await auth_client.call_tool("create_collection_access_token_tool", {
                    "label": "SearchKey1",
                    "collection_id": collection_ids[0],
                    "permission": "read_write",
                })
                key2_result = await auth_client.call_tool("create_collection_access_token_tool", {
                    "label": "SearchKey2",
                    "collection_id": collection_ids[1],
                    "permission": "read_write",
                })
                
                # Create PAT token
                pat_result = await auth_client.call_tool("create_pat_token_tool", {
                    "label": "Search Test PAT",
                })
                pat_token = pat_result["token"]
            
            # Store searchable documents in each collection
            async with MCPClient(SERVER_URL, auth_token=key1_result["key"]) as key_client:
                await key_client.call_tool("store_document_tool", {
                    "title": "Python Guide",
                    "content": "# Python Programming\n\nLearn Python basics.",
                    "document_type": "markdown",
                })
            
            async with MCPClient(SERVER_URL, auth_token=key2_result["key"]) as key_client:
                await key_client.call_tool("store_document_tool", {
                    "title": "JavaScript Guide",
                    "content": "# JavaScript Programming\n\nLearn JavaScript basics.",
                    "document_type": "markdown",
                })
            
            # Use PAT to search (should search both collections)
            async with MCPClient(SERVER_URL, auth_token=pat_token) as pat_client:
                search_result = await pat_client.call_tool("search_documents_tool", {
                    "query": "programming",
                    "max_results": 10,
                })
                
                total = search_result.get("total_results", 0)
                assert total >= 2, f"Expected results from both collections, got {total}"
                print(f"\nPAT search found {total} results across all collections")
