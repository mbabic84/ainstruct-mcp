"""
Live integration tests for ainstruct-mcp production server.
Tests against https://ainstruct.kralicinora.cz/mcp

Run with: docker build -f Dockerfile.mcp-client -t mcp-client-test . && docker run --rm mcp-client-test
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
        """List tools without authentication returns only public tools."""
        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            tools = await client.list_tools()

            tool_names = {t["name"] for t in tools}

            # Without auth, only public tools should be visible
            public_tools = {
                "user_register_tool",
                "user_login_tool",
                "user_refresh_tool",
            }
            assert tool_names == public_tools, f"Expected only public tools, got: {tool_names}"

            print(f"\nFound {len(tools)} public tools (no auth)")

    @pytest.mark.asyncio
    async def test_list_tools_authenticated(self):
        """List tools with JWT authentication returns all non-admin tools."""
        test_id = generate_test_id()

        async with MCPClient(SERVER_URL, transport=TRANSPORT) as client:
            # Register and login to get JWT token
            reg_result = await register_test_user(client, test_id)
            login_result = await login_user(
                client,
                reg_result["username"],
                reg_result["password"]
            )

            # List tools with JWT auth
            async with MCPClient(SERVER_URL, auth_token=login_result["access_token"], transport=TRANSPORT) as auth_client:
                tools = await auth_client.list_tools()
                tool_names = {t["name"] for t in tools}

                # With JWT, should see public + user + collections + keys/PATs + documents
                assert "user_register_tool" in tool_names
                assert "user_login_tool" in tool_names
                assert "user_profile_tool" in tool_names

                # Collection tools
                assert "create_collection_tool" in tool_names
                assert "list_collections_tool" in tool_names

                # API key tools
                assert "create_api_key_tool" in tool_names
                assert "list_api_keys_tool" in tool_names

                # Document tools
                assert "store_document_tool" in tool_names
                assert "search_documents_tool" in tool_names

                print(f"\nFound {len(tools)} tools with JWT auth")


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

            print("\nRefreshed token successfully")


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
                
                # Should NOT be able to store - error is returned as string response
                store_result = await ro_client.call_tool("store_document_tool", {
                    "title": "Should Fail",
                    "content": "This should not work",
                })
                
                # Error is returned as string, not raised as exception
                error_msg = str(store_result).lower()
                assert "permission" in error_msg or "insufficient" in error_msg, f"Expected permission error, got: {store_result}"
                print(f"\nRead-only key correctly denied write: {store_result}")


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
                key1_result = await auth_client.call_tool("create_api_key_tool", {
                    "label": "Key1",
                    "collection_id": collection_ids[0],
                    "permission": "read_write",
                })
                key2_result = await auth_client.call_tool("create_api_key_tool", {
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
                key1_result = await auth_client.call_tool("create_api_key_tool", {
                    "label": "SearchKey1",
                    "collection_id": collection_ids[0],
                    "permission": "read_write",
                })
                key2_result = await auth_client.call_tool("create_api_key_tool", {
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


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
