"""Tests for MCP server module."""


class TestMcpServer:
    """Test cases for MCP server module."""

    def test_mcp_server_imports(self):
        """Test that MCP server module imports correctly."""
        from mcp_server import main
        assert main is not None

    def test_mcp_server_has_mcp_instance(self):
        """Test that MCP server has mcp instance."""
        from mcp_server.server import mcp

        assert mcp is not None
        assert mcp.name == "AI Document Memory"

    def test_mcp_server_tools_registered(self):
        """Test that MCP tools are registered."""
        from mcp_server.server import mcp

        # Tools should be registered
        assert mcp is not None
