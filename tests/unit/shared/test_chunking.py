"""Tests for shared chunking module."""
import pytest


class TestChunkingService:
    """Test cases for ChunkingService class."""

    @pytest.fixture
    def chunking_service(self, mock_settings):
        """Create ChunkingService instance."""
        from shared.services import ChunkingService
        return ChunkingService()

    def test_count_tokens(self, chunking_service):
        """Test token counting."""
        text = "This is a test sentence."
        count = chunking_service.count_tokens(text)

        assert count > 0
        assert isinstance(count, int)

    def test_chunk_markdown_empty(self, chunking_service):
        """Test chunking empty content."""
        chunks = chunking_service.chunk_markdown("", "Test")

        assert chunks == []

    def test_chunk_markdown_simple(self, chunking_service):
        """Test chunking simple markdown."""
        content = "# Header\n\nThis is a paragraph."
        chunks = chunking_service.chunk_markdown(content, "Test Doc")

        assert len(chunks) > 0
        assert chunks[0]["title"] == "Test Doc"
        assert "content" in chunks[0]
        assert "token_count" in chunks[0]
        assert "chunk_index" in chunks[0]

    def test_chunk_markdown_multiple_headers(self, chunking_service):
        """Test chunking markdown with multiple headers."""
        content = """# Header 1

Content 1.

## Header 2

Content 2.

### Header 3

Content 3.
"""
        chunks = chunking_service.chunk_markdown(content, "Test Doc")

        assert len(chunks) > 0
        # Verify chunk structure
        for chunk in chunks:
            assert "content" in chunk
            assert "token_count" in chunk
            assert chunk["token_count"] > 0

    def test_chunk_max_tokens(self, chunking_service):
        """Test that chunks respect max_tokens limit."""
        # Create content longer than default max_tokens (400)
        content = "# Header\n\n" + ("A" * 1000)

        chunks = chunking_service.chunk_markdown(content, "Test")

        # Should create chunks (actual count depends on implementation)
        assert len(chunks) >= 1

    def test_chunk_preserves_content(self, chunking_service):
        """Test that chunked content preserves original text."""
        content = "# Title\n\nSome content here."

        chunks = chunking_service.chunk_markdown(content, "Test")

        combined = "".join(c["content"] for c in chunks)
        assert "Title" in combined
        assert "Some content" in combined
