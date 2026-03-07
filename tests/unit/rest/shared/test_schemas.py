"""Tests for REST API schemas."""

import pytest
from pydantic import ValidationError
from rest_api.schemas import DocumentCreate, DocumentUpdate
from shared.constants import DocumentType


class TestDocumentCreate:
    """Test cases for DocumentCreate schema."""

    def test_valid_document_types(self):
        """Test that all valid document types are accepted."""
        valid_types = DocumentType.get_codemirror_types()

        for doc_type in valid_types:
            doc = DocumentCreate(
                title="Test Document",
                content="Test content",
                collection_id="col-123",
                document_type=doc_type,
            )
            assert doc.document_type == doc_type

    def test_default_document_type_is_markdown(self):
        """Test that default document type is markdown."""
        doc = DocumentCreate(
            title="Test Document",
            content="Test content",
            collection_id="col-123",
        )
        assert doc.document_type == "markdown"

    def test_invalid_document_type_raises_error(self):
        """Test that invalid document type raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentCreate(
                title="Test Document",
                content="Test content",
                collection_id="col-123",
                document_type="pdf",
            )

        assert "Invalid document_type" in str(exc_info.value)

    def test_case_sensitive_validation(self):
        """Test that document type validation is case-sensitive."""
        # Uppercase should fail
        with pytest.raises(ValidationError):
            DocumentCreate(
                title="Test",
                content="Test",
                collection_id="col-123",
                document_type="PYTHON",
            )

        # Mixed case should fail
        with pytest.raises(ValidationError):
            DocumentCreate(
                title="Test",
                content="Test",
                collection_id="col-123",
                document_type="Python",
            )

        # Lowercase should pass
        doc = DocumentCreate(
            title="Test",
            content="Test",
            collection_id="col-123",
            document_type="python",
        )
        assert doc.document_type == "python"


class TestDocumentUpdate:
    """Test cases for DocumentUpdate schema."""

    def test_valid_document_types(self):
        """Test that all valid document types are accepted."""
        valid_types = DocumentType.get_codemirror_types()

        for doc_type in valid_types:
            doc = DocumentUpdate(document_type=doc_type)
            assert doc.document_type == doc_type

    def test_none_document_type_is_allowed(self):
        """Test that None document type is allowed (for partial updates)."""
        doc = DocumentUpdate(
            title="Updated Title",
        )
        assert doc.document_type is None
        assert doc.title == "Updated Title"

    def test_invalid_document_type_raises_error(self):
        """Test that invalid document type raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentUpdate(document_type="docx")

        assert "Invalid document_type" in str(exc_info.value)

    def test_partial_update_without_document_type(self):
        """Test partial update without changing document type."""
        doc = DocumentUpdate(
            title="Updated Title",
            content="Updated content",
        )
        assert doc.document_type is None
        assert doc.title == "Updated Title"
        assert doc.content == "Updated content"
