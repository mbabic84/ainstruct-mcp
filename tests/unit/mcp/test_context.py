"""Tests for context module - auth context management."""

from mcp_server.tools.context import (
    clear_all_auth,
    clear_cat_info,
    clear_pat_info,
    clear_user_info,
    get_auth_type,
    get_cat_info,
    get_current_user_id,
    get_pat_info,
    get_user_collections,
    get_user_info,
    has_scope,
    has_write_permission,
    is_authenticated,
    set_auth_type,
    set_cat_info,
    set_pat_info,
    set_user_collections,
    set_user_info,
)


class TestAuthContext:
    """Test cases for auth context functions."""

    def setup_method(self):
        """Clear all auth context before each test."""
        clear_all_auth()

    def teardown_method(self):
        """Clear all auth context after each test."""
        clear_all_auth()

    def test_set_and_get_user_info(self):
        """Test setting and getting user info."""
        user_info = {
            "user_id": "user-123",
            "username": "testuser",
            "email": "test@example.com",
            "is_superuser": False,
            "scopes": ["read", "write"],
        }
        set_user_info(user_info)

        result = get_user_info()
        assert result == user_info

    def test_clear_user_info(self):
        """Test clearing user info."""
        set_user_info({"user_id": "user-123", "is_superuser": False})
        clear_user_info()

        assert get_user_info() is None

    def test_set_and_get_pat_info(self):
        """Test setting and getting PAT info."""
        pat_info = {
            "user_id": "user-123",
            "is_superuser": False,
            "scopes": ["read"],
        }
        set_pat_info(pat_info)

        result = get_pat_info()
        assert result == pat_info

    def test_clear_pat_info(self):
        """Test clearing PAT info."""
        set_pat_info({"user_id": "user-123", "is_superuser": False})
        clear_pat_info()

        assert get_pat_info() is None

    def test_set_and_get_cat_info(self):
        """Test setting and getting CAT info."""
        cat_info = {
            "id": "cat-123",
            "user_id": "user-456",
            "collection_id": "coll-123",
            "collection_name": "Test Collection",
            "qdrant_collection": "docs_abc123",
            "permission": "read_write",
            "is_admin": False,
        }
        set_cat_info(cat_info)

        result = get_cat_info()
        assert result == cat_info

    def test_clear_cat_info(self):
        """Test clearing CAT info."""
        set_cat_info({"id": "cat-123", "user_id": "user-123"})
        clear_cat_info()

        assert get_cat_info() is None

    def test_set_and_get_user_collections(self):
        """Test setting and getting user collections."""
        collections = [
            {"collection_id": "coll-1", "name": "Collection 1", "qdrant_collection": "docs_1"},
            {"collection_id": "coll-2", "name": "Collection 2", "qdrant_collection": "docs_2"},
        ]
        set_user_collections(collections)

        result = get_user_collections()
        assert result == collections

    def test_clear_all_auth(self):
        """Test clearing all auth context."""
        set_user_info({"user_id": "user-123", "is_superuser": False})
        set_pat_info({"user_id": "user-123", "is_superuser": False})
        set_cat_info({"id": "cat-123", "user_id": "user-123"})
        set_user_collections([{"collection_id": "coll-1"}])
        set_auth_type("jwt")

        clear_all_auth()

        assert get_user_info() is None
        assert get_pat_info() is None
        assert get_cat_info() is None
        assert get_user_collections() == []
        assert get_auth_type() is None

    def test_set_and_get_auth_type(self):
        """Test setting and getting auth type."""
        set_auth_type("jwt")
        assert get_auth_type() == "jwt"

        set_auth_type("pat")
        assert get_auth_type() == "pat"

        set_auth_type("cat")
        assert get_auth_type() == "cat"


class TestGetCurrentUserId:
    """Test cases for get_current_user_id function."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    def test_get_current_user_id_from_user_info(self):
        """Test getting user ID from user info."""
        set_user_info({"user_id": "user-123", "is_superuser": False})
        assert get_current_user_id() == "user-123"

    def test_get_current_user_id_from_cat_info(self):
        """Test getting user ID from CAT info when no user info."""
        set_cat_info({"id": "cat-123", "user_id": "user-456"})
        assert get_current_user_id() == "user-456"

    def test_get_current_user_id_from_pat_info(self):
        """Test getting user ID from PAT info when no user or CAT info."""
        set_pat_info({"user_id": "user-789", "is_superuser": False})
        assert get_current_user_id() == "user-789"

    def test_get_current_user_id_priority(self):
        """Test that user_info takes priority over cat_info and pat_info."""
        set_user_info({"user_id": "user-123", "is_superuser": False})
        set_cat_info({"id": "cat-123", "user_id": "user-456"})
        set_pat_info({"user_id": "user-789", "is_superuser": False})

        assert get_current_user_id() == "user-123"

    def test_get_current_user_id_none_when_not_authenticated(self):
        """Test that None is returned when not authenticated."""
        assert get_current_user_id() is None


class TestIsAuthenticated:
    """Test cases for is_authenticated function."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    def test_is_authenticated_with_user_info(self):
        """Test authenticated with user info."""
        set_user_info({"user_id": "user-123", "is_superuser": False})
        assert is_authenticated() is True

    def test_is_authenticated_with_pat_info(self):
        """Test authenticated with PAT info."""
        set_pat_info({"user_id": "user-123", "is_superuser": False})
        assert is_authenticated() is True

    def test_is_authenticated_with_cat_info(self):
        """Test authenticated with CAT info."""
        set_cat_info({"id": "cat-123", "user_id": "user-123"})
        assert is_authenticated() is True

    def test_is_authenticated_not_authenticated(self):
        """Test not authenticated when no auth context."""
        assert is_authenticated() is False


class TestHasScope:
    """Test cases for has_scope function."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    def test_has_scope_superuser_has_all_scopes(self):
        """Test that superuser has all scopes."""
        set_user_info({"user_id": "admin-123", "is_superuser": True, "scopes": []})
        from shared.db.models import Scope

        assert has_scope(Scope.ADMIN) is True
        assert has_scope(Scope.WRITE) is True
        assert has_scope(Scope.READ) is True

    def test_has_scope_with_user_scopes(self):
        """Test has_scope with user scopes."""
        from shared.db.models import Scope

        set_user_info(
            {"user_id": "user-123", "is_superuser": False, "scopes": [Scope.READ, Scope.WRITE]}
        )

        assert has_scope(Scope.READ) is True
        assert has_scope(Scope.WRITE) is True
        assert has_scope(Scope.ADMIN) is False

    def test_has_scope_cat_admin_has_all(self):
        """Test that CAT admin has all scopes."""
        set_cat_info({"id": "cat-123", "user_id": "user-123", "is_admin": True})
        from shared.db.models import Scope

        assert has_scope(Scope.ADMIN) is True
        assert has_scope(Scope.WRITE) is True
        assert has_scope(Scope.READ) is True

    def test_has_scope_pat_superuser(self):
        """Test that PAT superuser has all scopes."""
        set_pat_info({"user_id": "admin-123", "is_superuser": True, "scopes": []})
        from shared.db.models import Scope

        assert has_scope(Scope.ADMIN) is True


class TestHasWritePermission:
    """Test cases for has_write_permission function."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    def test_has_write_permission_superuser(self):
        """Test superuser has write permission."""
        set_user_info({"user_id": "admin-123", "is_superuser": True, "scopes": []})
        assert has_write_permission() is True

    def test_has_write_permission_with_write_scope(self):
        """Test user with write scope has write permission."""
        from shared.db.models import Scope

        set_user_info({"user_id": "user-123", "is_superuser": False, "scopes": [Scope.WRITE]})
        assert has_write_permission() is True

    def test_has_write_permission_cat_read_write(self):
        """Test CAT with read_write permission has write permission."""
        set_cat_info(
            {"id": "cat-123", "user_id": "user-123", "permission": "read_write", "is_admin": False}
        )
        assert has_write_permission() is True

    def test_has_write_permission_cat_read_only(self):
        """Test CAT with read only permission does NOT have write permission."""
        set_cat_info(
            {"id": "cat-123", "user_id": "user-123", "permission": "read", "is_admin": False}
        )
        assert has_write_permission() is False
