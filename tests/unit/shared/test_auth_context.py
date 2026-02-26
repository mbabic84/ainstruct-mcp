"""Tests for MCP server context module."""


class TestAuthContext:
    """Test cases for auth context functions."""

    def test_set_and_get_auth_context(self):
        """Test setting and getting auth context."""
        from shared.auth import clear_auth_context, get_auth_context, set_auth_context

        test_context = {
            "user_id": "user-123",
            "username": "testuser",
            "is_superuser": False,
        }

        set_auth_context(test_context)
        assert get_auth_context() == test_context

        clear_auth_context()
        assert get_auth_context() is None

    def test_has_write_permission_superuser(self):
        """Test that superusers have write permission."""
        from shared.auth import has_write_permission, set_auth_context

        set_auth_context({"is_superuser": True})
        assert has_write_permission() is True

    def test_has_write_permission_read_write(self):
        """Test that READ_WRITE permission grants write access."""
        from shared.auth import has_write_permission, set_auth_context
        from shared.db.models import Permission

        set_auth_context({"permission": Permission.READ_WRITE})
        assert has_write_permission() is True

    def test_has_write_permission_no_context(self):
        """Test that no context means no write permission."""
        from shared.auth import clear_auth_context, has_write_permission

        clear_auth_context()
        assert has_write_permission() is False

    def test_has_write_permission_read_only(self):
        """Test that READ permission denies write access."""
        from shared.auth import has_write_permission, set_auth_context
        from shared.db.models import Permission

        set_auth_context({"permission": Permission.READ})
        assert has_write_permission() is False

    def test_has_write_permission_with_scopes(self):
        """Test that WRITE scope grants write access."""
        from shared.auth import has_write_permission, set_auth_context
        from shared.db.models import Scope

        set_auth_context({"scopes": [Scope.READ, Scope.WRITE]})
        assert has_write_permission() is True

    def test_has_write_permission_write_scope_only(self):
        """Test that WRITE scope alone grants access."""
        from shared.auth import has_write_permission, set_auth_context
        from shared.db.models import Scope

        set_auth_context({"scopes": [Scope.WRITE]})
        assert has_write_permission() is True

    def test_has_write_permission_no_write_scope(self):
        """Test that no WRITE scope denies access."""
        from shared.auth import has_write_permission, set_auth_context
        from shared.db.models import Scope

        set_auth_context({"scopes": [Scope.READ]})
        assert has_write_permission() is False
