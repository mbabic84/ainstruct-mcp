from enum import StrEnum


class DocumentType(StrEnum):
    """Supported document types for CodeMirror editor.

    These are the built-in languages supported by CodeMirror 6.
    """

    MARKDOWN = "markdown"
    TEXT = "text"
    HTML = "html"
    CSS = "css"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JSON = "json"
    PYTHON = "python"
    JAVA = "java"
    PHP = "php"
    RUST = "rust"
    GO = "go"
    CPP = "cpp"
    SQL = "sql"
    XML = "xml"
    YAML = "yaml"
    VUE = "vue"
    ANGULAR = "angular"
    SASS = "sass"
    LIQUID = "liquid"
    JINJA = "jinja"
    WAST = "wast"

    @classmethod
    def get_codemirror_types(cls) -> list[str]:
        """Return list of all supported document types for CodeMirror."""
        return [member.value for member in cls]

    @classmethod
    def is_valid(cls, value: str) -> bool:
        """Check if a given value is a valid document type."""
        return value in cls.get_codemirror_types()
