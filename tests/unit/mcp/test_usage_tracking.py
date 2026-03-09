"""Tests for MCP usage tracking."""



class TestDocumentToolsTracking:
    """Test cases for MCP usage tracking in document tools."""

    def test_document_tools_defined(self):
        """Test that document tools are defined."""
        from mcp_server.tools.auth import DOCUMENT_TOOLS

        expected_tools = {
            "store_document_tool",
            "search_documents_tool",
            "get_document_tool",
            "list_documents_tool",
            "delete_document_tool",
            "update_document_tool",
        }

        assert expected_tools.issubset(DOCUMENT_TOOLS)

    def test_is_document_tool(self):
        """Test that document tool detection works."""
        from mcp_server.tools.auth import is_document_tool

        assert is_document_tool("store_document_tool") is True
        assert is_document_tool("search_documents_tool") is True
        assert is_document_tool("get_document_tool") is True
        assert is_document_tool("list_documents_tool") is True
        assert is_document_tool("delete_document_tool") is True
        assert is_document_tool("update_document_tool") is True

    def test_non_document_tool_returns_false(self):
        """Test that non-document tools return False."""
        from mcp_server.tools.auth import is_document_tool

        assert is_document_tool("create_collection_tool") is False
        assert is_document_tool("list_collections_tool") is False
        assert is_document_tool("invalid_tool") is False


class TestUsageTracking:
    """Test cases for usage tracking integration."""

    def test_extract_user_id_from_user_info(self):
        """Test extracting user_id from user_info."""
        from mcp_server.tools.context import clear_all_auth, get_user_info, set_user_info

        clear_all_auth()
        set_user_info({"user_id": "user-123", "username": "testuser"})

        user_info = get_user_info()
        assert user_info["user_id"] == "user-123"

    def test_extract_user_id_from_pat_info(self):
        """Test extracting user_id from pat_info."""
        from mcp_server.tools.context import clear_all_auth, get_pat_info, set_pat_info

        clear_all_auth()
        set_pat_info({"user_id": "user-456", "pat_id": "pat-123"})

        pat_info = get_pat_info()
        assert pat_info["user_id"] == "user-456"

    def test_extract_user_id_from_cat_info(self):
        """Test extracting user_id from cat_info."""
        from mcp_server.tools.context import clear_all_auth, get_cat_info, set_cat_info

        clear_all_auth()
        set_cat_info({"user_id": "user-789", "cat_id": "cat-123"})

        cat_info = get_cat_info()
        assert cat_info["user_id"] == "user-789"
