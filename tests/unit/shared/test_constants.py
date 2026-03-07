"""Tests for shared constants."""

import pytest
from pydantic import BaseModel, Field, field_validator
from shared.constants import DocumentType


class TestDocumentType:
    """Test cases for DocumentType enum."""

    def test_all_document_types(self):
        """Test that all expected document types are defined."""
        expected_types = {
            "markdown",
            "text",
            "html",
            "css",
            "javascript",
            "typescript",
            "json",
            "python",
            "java",
            "php",
            "rust",
            "go",
            "cpp",
            "sql",
            "xml",
            "yaml",
            "vue",
            "angular",
            "sass",
            "liquid",
            "jinja",
            "wast",
        }
        actual_types = set(DocumentType.get_codemirror_types())
        assert actual_types == expected_types

    def test_is_valid_with_valid_types(self):
        """Test is_valid returns True for valid document types."""
        valid_types = [
            "markdown",
            "python",
            "javascript",
            "json",
            "html",
            "css",
            "typescript",
            "java",
            "go",
            "rust",
        ]
        for doc_type in valid_types:
            assert DocumentType.is_valid(doc_type) is True

    def test_is_valid_with_invalid_types(self):
        """Test is_valid returns False for invalid document types."""
        invalid_types = [
            "pdf",
            "docx",
            "invalid",
            "",
            "MARKDOWN",  # Case sensitive
            "Python",  # Case sensitive
            "javascript ",  # Trailing space
        ]
        for doc_type in invalid_types:
            assert DocumentType.is_valid(doc_type) is False

    def test_get_codemirror_types_returns_list(self):
        """Test get_codemirror_types returns a list of strings."""
        types = DocumentType.get_codemirror_types()
        assert isinstance(types, list)
        assert all(isinstance(t, str) for t in types)
        assert len(types) == 22

    def test_default_value_is_markdown(self):
        """Test that the default document type is markdown."""
        assert DocumentType.MARKDOWN.value == "markdown"

    def test_enum_members_are_strings(self):
        """Test that enum members are strings (StrEnum)."""
        assert isinstance(DocumentType.MARKDOWN.value, str)
        assert DocumentType.MARKDOWN == "markdown"
        assert DocumentType.PYTHON == "python"


class TestDocumentTypeValidation:
    """Test cases for DocumentType validation in Pydantic models."""

    def test_valid_document_type_in_model(self):
        """Test that valid document types are accepted."""

        class TestModel(BaseModel):
            document_type: str = Field(default=DocumentType.MARKDOWN.value)

            @field_validator("document_type")
            @classmethod
            def validate_document_type(cls, v: str) -> str:
                if not DocumentType.is_valid(v):
                    valid_types = ", ".join(DocumentType.get_codemirror_types())
                    raise ValueError(f"Invalid document_type. Must be one of: {valid_types}")
                return v

        # Should not raise
        model = TestModel(document_type="python")
        assert model.document_type == "python"

        model2 = TestModel(document_type="markdown")
        assert model2.document_type == "markdown"

    def test_invalid_document_type_in_model(self):
        """Test that invalid document types raise validation error."""

        class TestModel(BaseModel):
            document_type: str = Field(default=DocumentType.MARKDOWN.value)

            @field_validator("document_type")
            @classmethod
            def validate_document_type(cls, v: str) -> str:
                if not DocumentType.is_valid(v):
                    valid_types = ", ".join(DocumentType.get_codemirror_types())
                    raise ValueError(f"Invalid document_type. Must be one of: {valid_types}")
                return v

        with pytest.raises(ValueError) as exc_info:
            TestModel(document_type="pdf")

        assert "Invalid document_type" in str(exc_info.value)
        assert "markdown" in str(exc_info.value)  # Should list valid types

    def test_default_value_in_model(self):
        """Test that default value is used when not provided."""

        class TestModel(BaseModel):
            document_type: str = Field(default=DocumentType.MARKDOWN.value)

            @field_validator("document_type")
            @classmethod
            def validate_document_type(cls, v: str) -> str:
                if not DocumentType.is_valid(v):
                    valid_types = ", ".join(DocumentType.get_codemirror_types())
                    raise ValueError(f"Invalid document_type. Must be one of: {valid_types}")
                return v

        model = TestModel()
        assert model.document_type == "markdown"

    def test_case_sensitivity(self):
        """Test that document type validation is case-sensitive."""

        class TestModel(BaseModel):
            document_type: str = Field(default=DocumentType.MARKDOWN.value)

            @field_validator("document_type")
            @classmethod
            def validate_document_type(cls, v: str) -> str:
                if not DocumentType.is_valid(v):
                    valid_types = ", ".join(DocumentType.get_codemirror_types())
                    raise ValueError(f"Invalid document_type. Must be one of: {valid_types}")
                return v

        # Uppercase should fail
        with pytest.raises(ValueError):
            TestModel(document_type="PYTHON")

        # Mixed case should fail
        with pytest.raises(ValueError):
            TestModel(document_type="Python")

        # Lowercase should pass
        model = TestModel(document_type="python")
        assert model.document_type == "python"
