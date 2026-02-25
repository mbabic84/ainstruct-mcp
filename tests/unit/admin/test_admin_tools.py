"""
Comprehensive tests for admin user management tools.
Tests list_users, search_users, get_user, update_user, delete_user operations.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.tools.admin_tools import (
    ListUsersInput,
    SearchUsersInput,
    GetUserInput,
    UpdateUserInput,
    DeleteUserInput,
    list_users,
    search_users,
    get_user,
    update_user,
    delete_user,
)
from app.tools.context import set_user_info, clear_all_auth
from app.db.models import UserResponse, Scope


@pytest.fixture
def mock_regular_user():
    """Regular user without admin scope."""
    return {
        "id": "user-123",
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": "$2b$12$hashedpassword",
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def mock_admin_user():
    """Admin user with is_superuser=True."""
    return {
        "id": "admin-123",
        "username": "admin",
        "email": "admin@example.com",
        "password_hash": "$2b$12$hashedpassword",
        "is_active": True,
        "is_superuser": True,
        "created_at": datetime.now(timezone.utc),
    }


@pytest.fixture
def mock_user_response():
    """Mock user response object."""
    return UserResponse(
        id="user-456",
        email="user@example.com",
        username="user456",
        is_active=True,
        is_superuser=False,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_user_list():
    """Mock list of users."""
    return [
        UserResponse(
            id="user-1",
            email="user1@example.com",
            username="user1",
            is_active=True,
            is_superuser=False,
            created_at=datetime.now(timezone.utc),
        ),
        UserResponse(
            id="user-2",
            email="user2@example.com",
            username="user2",
            is_active=True,
            is_superuser=False,
            created_at=datetime.now(timezone.utc),
        ),
    ]


class TestListUsers:
    """Tests for list_users tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_list_users_with_admin(self, mock_admin_user, mock_user_list):
        """Admin can list all users."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = mock_user_list
            mock_repo_factory.return_value = mock_repo

            result = await list_users(ListUsersInput(limit=50, offset=0))

            assert len(result) == 2
            assert result[0].id == "user-1"
            assert result[1].id == "user-2"
            mock_repo.list_all.assert_called_once_with(limit=50, offset=0)

    @pytest.mark.asyncio
    async def test_list_users_with_pagination(self, mock_admin_user, mock_user_list):
        """Pagination parameters are passed correctly."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = mock_user_list
            mock_repo_factory.return_value = mock_repo

            await list_users(ListUsersInput(limit=10, offset=20))

            mock_repo.list_all.assert_called_once_with(limit=10, offset=20)

    @pytest.mark.asyncio
    async def test_list_users_empty_database(self, mock_admin_user):
        """Empty user list returns empty list."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = []
            mock_repo_factory.return_value = mock_repo

            result = await list_users(ListUsersInput())

            assert result == []

    @pytest.mark.asyncio
    async def test_list_users_non_admin_denied(self, mock_regular_user):
        """Non-admin user cannot list all users."""
        set_user_info(mock_regular_user)

        with pytest.raises(ValueError, match="Insufficient permissions"):
            await list_users(ListUsersInput())

    @pytest.mark.asyncio
    async def test_list_users_not_authenticated(self):
        """Unauthenticated request denied."""
        clear_all_auth()

        with pytest.raises(ValueError, match="Not authenticated"):
            await list_users(ListUsersInput())

    @pytest.mark.asyncio
    async def test_list_users_with_default_parameters(self, mock_admin_user, mock_user_list):
        """Default limit and offset are used."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = mock_user_list
            mock_repo_factory.return_value = mock_repo

            await list_users(ListUsersInput())

            mock_repo.list_all.assert_called_once_with(limit=50, offset=0)


class TestSearchUsers:
    """Tests for search_users tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_search_users_success(self, mock_admin_user, mock_user_list):
        """Admin can search users."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.search.return_value = mock_user_list
            mock_repo_factory.return_value = mock_repo

            result = await search_users(SearchUsersInput(query="user", limit=50, offset=0))

            assert len(result) == 2
            mock_repo.search.assert_called_once_with(query="user", limit=50, offset=0)

    @pytest.mark.asyncio
    async def test_search_users_no_matches(self, mock_admin_user):
        """Search with no matches returns empty list."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.search.return_value = []
            mock_repo_factory.return_value = mock_repo

            result = await search_users(SearchUsersInput(query="nonexistent"))

            assert result == []

    @pytest.mark.asyncio
    async def test_search_users_with_special_characters(self, mock_admin_user, mock_user_list):
        """Search query with special characters works."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.search.return_value = mock_user_list
            mock_repo_factory.return_value = mock_repo

            await search_users(SearchUsersInput(query="user@example.com"))

            mock_repo.search.assert_called_once_with(query="user@example.com", limit=50, offset=0)

    @pytest.mark.asyncio
    async def test_search_users_case_sensitivity(self, mock_admin_user, mock_user_list):
        """Search should handle case according to database collation."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.search.return_value = mock_user_list
            mock_repo_factory.return_value = mock_repo

            await search_users(SearchUsersInput(query="USER"))

            mock_repo.search.assert_called_once_with(query="USER", limit=50, offset=0)

    @pytest.mark.asyncio
    async def test_search_users_non_admin_denied(self, mock_regular_user):
        """Non-admin user cannot search users."""
        set_user_info(mock_regular_user)

        with pytest.raises(ValueError, match="Insufficient permissions"):
            await search_users(SearchUsersInput(query="test"))

    @pytest.mark.asyncio
    async def test_search_users_empty_query(self, mock_admin_user):
        """Empty query should still be handled."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.search.return_value = []
            mock_repo_factory.return_value = mock_repo

            result = await search_users(SearchUsersInput(query=""))

            assert result == []
            mock_repo.search.assert_called_once_with(query="", limit=50, offset=0)


class TestGetUser:
    """Tests for get_user tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_get_user_success(self, mock_admin_user, mock_user_response):
        """Admin can get any user by ID."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_user_response
            mock_repo_factory.return_value = mock_repo

            result = await get_user(GetUserInput(user_id="user-456"))

            assert result.id == "user-456"
            assert result.email == "user@example.com"
            mock_repo.get_by_id.assert_called_once_with("user-456")

    @pytest.mark.asyncio
    async def test_get_user_not_found(self, mock_admin_user):
        """Non-existent user raises error."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="User not found"):
                await get_user(GetUserInput(user_id="nonexistent"))

    @pytest.mark.asyncio
    async def test_get_user_invalid_uuid_format(self, mock_admin_user):
        """Invalid UUID format should be handled by pydantic validation."""
        set_user_info(mock_admin_user)

        # Pydantic should validate UUID format before reaching the function
        with pytest.raises(Exception):  # Could be ValidationError
            await get_user(GetUserInput(user_id="not-a-uuid"))

    @pytest.mark.asyncio
    async def test_get_user_non_admin_denied(self, mock_regular_user):
        """Non-admin user cannot get user details."""
        set_user_info(mock_regular_user)

        with pytest.raises(ValueError, match="Insufficient permissions"):
            await get_user(GetUserInput(user_id="any-user-id"))

    @pytest.mark.asyncio
    async def test_get_user_admin_access_others(self, mock_admin_user, mock_user_response):
        """Admin can access other users' data."""
        set_user_info(mock_admin_user)
        mock_user_response.id = "different-user-id"

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_user_response
            mock_repo_factory.return_value = mock_repo

            result = await get_user(GetUserInput(user_id="different-user-id"))

            assert result.id == "different-user-id"


class TestUpdateUser:
    """Tests for update_user tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.fixture
    def mock_auth_service(self):
        mock = MagicMock()
        mock.hash_password.return_value = "hashed_new_password"
        return mock

    @pytest.mark.asyncio
    async def test_update_user_email_only(self, mock_admin_user, mock_user_response, mock_auth_service):
        """Admin can update user email."""
        set_user_info(mock_admin_user)
        mock_user_response.id = "user-456"

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory, \
             patch("app.tools.admin_tools.get_auth_service") as mock_auth_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_user_response
            mock_repo.update.return_value = mock_user_response
            mock_repo_factory.return_value = mock_repo
            mock_auth_factory.return_value = mock_auth_service

            result = await update_user(UpdateUserInput(
                user_id="user-456",
                email="newemail@example.com",
            ))

            assert result.email == "user@example.com"  # Original, update returns old?
            mock_repo.update.assert_called_once_with(
                user_id="user-456",
                email="newemail@example.com",
                username=None,
                password_hash=None,
                is_active=None,
                is_superuser=None,
            )
            mock_auth_service.hash_password.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_password_only(self, mock_admin_user, mock_user_response, mock_auth_service):
        """Admin can update user password."""
        set_user_info(mock_admin_user)
        mock_user_response.id = "user-456"

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory, \
             patch("app.tools.admin_tools.get_auth_service") as mock_auth_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_user_response
            mock_repo.update.return_value = mock_user_response
            mock_repo_factory.return_value = mock_repo
            mock_auth_factory.return_value = mock_auth_service

            result = await update_user(UpdateUserInput(
                user_id="user-456",
                password="newpassword",
            ))

            mock_repo.update.assert_called_once_with(
                user_id="user-456",
                email=None,
                username=None,
                password_hash="hashed_new_password",
                is_active=None,
                is_superuser=None,
            )
            mock_auth_service.hash_password.assert_called_once_with("newpassword")

    @pytest.mark.asyncio
    async def test_update_user_all_fields(self, mock_admin_user, mock_user_response, mock_auth_service):
        """Admin can update all fields at once."""
        set_user_info(mock_admin_user)
        mock_user_response.id = "user-456"

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory, \
             patch("app.tools.admin_tools.get_auth_service") as mock_auth_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_user_response
            mock_repo.update.return_value = mock_user_response
            mock_repo_factory.return_value = mock_repo
            mock_auth_factory.return_value = mock_auth_service

            await update_user(UpdateUserInput(
                user_id="user-456",
                email="new@example.com",
                username="newusername",
                password="newpass",
                is_active=False,
                is_superuser=True,
            ))

            mock_repo.update.assert_called_once_with(
                user_id="user-456",
                email="new@example.com",
                username="newusername",
                password_hash="hashed_new_password",
                is_active=False,
                is_superuser=True,
            )

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, mock_admin_user):
        """Update non-existent user raises error."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="User not found"):
                await update_user(UpdateUserInput(user_id="nonexistent"))

    @pytest.mark.asyncio
    async def test_update_user_duplicate_email(self, mock_admin_user, mock_user_response):
        """Cannot update to an email that's already in use."""
        set_user_info(mock_admin_user)
        mock_user_response.id = "user-456"

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_user_response
            # Simulate email already exists - the update method should check this
            mock_repo.update.return_value = None  # Update fails due to duplicate
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="Failed to update user"):
                await update_user(UpdateUserInput(
                    user_id="user-456",
                    email="taken@example.com",
                ))

    @pytest.mark.asyncio
    async def test_update_user_duplicate_username(self, mock_admin_user, mock_user_response):
        """Cannot update to a username that's already in use."""
        set_user_info(mock_admin_user)
        mock_user_response.id = "user-456"

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_user_response
            # Simulate username already exists - update should fail
            mock_repo.update.return_value = None
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="Failed to update user"):
                await update_user(UpdateUserInput(
                    user_id="user-456",
                    username="taken",
                ))

    @pytest.mark.asyncio
    async def test_update_user_non_admin_denied(self, mock_regular_user):
        """Non-admin user cannot update users."""
        set_user_info(mock_regular_user)

        with pytest.raises(ValueError, match="Insufficient permissions"):
            await update_user(UpdateUserInput(user_id="any-id"))

    @pytest.mark.asyncio
    async def test_update_user_all_none_fields(self, mock_admin_user, mock_user_response):
        """Update with all None fields should not update anything (or raise error)."""
        set_user_info(mock_admin_user)
        mock_user_response.id = "user-456"

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory, \
             patch("app.tools.admin_tools.get_auth_service") as mock_auth_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_user_response
            mock_repo.update.return_value = None  # No update performed
            mock_repo_factory.return_value = mock_repo
            mock_auth_factory.return_value = MagicMock()

            with pytest.raises(ValueError, match="Failed to update user"):
                await update_user(UpdateUserInput(user_id="user-456"))

            mock_repo.update.assert_called_once_with(
                user_id="user-456",
                email=None,
                username=None,
                password_hash=None,
                is_active=None,
                is_superuser=None,
            )

    @pytest.mark.asyncio
    async def test_update_user_invalid_email_format(self, mock_admin_user, mock_user_response):
        """Invalid email format should be caught by pydantic validation."""
        set_user_info(mock_admin_user)
        mock_user_response.id = "user-456"

        # Pydantic validates email format in the input model
        # The UpdateUserInput model should validate email format
        from pydantic import ValidationError
        
        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_user_response
            mock_repo_factory.return_value = mock_repo

            # Pydantic should validate email format - invalid email should raise ValidationError
            with pytest.raises(ValidationError):
                await update_user(UpdateUserInput(
                    user_id="user-456",
                    email="invalid-email",
                ))

    @pytest.mark.asyncio
    async def test_update_user_self_update_allowed(self, mock_admin_user, mock_user_response, mock_auth_service):
        """Admin can update their own user record."""
        set_user_info(mock_admin_user)
        mock_user_response.id = mock_admin_user["id"]

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory, \
             patch("app.tools.admin_tools.get_auth_service") as mock_auth_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_user_response
            mock_repo.update.return_value = mock_user_response
            mock_repo_factory.return_value = mock_repo
            mock_auth_factory.return_value = mock_auth_service

            result = await update_user(UpdateUserInput(
                user_id=mock_admin_user["id"],
                email="newadmin@example.com",
            ))

            assert result.email == "user@example.com"  # Mock returns original


class TestDeleteUser:
    """Tests for delete_user tool."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_delete_user_success(self, mock_admin_user):
        """Admin can delete a user."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.delete.return_value = True
            mock_repo_factory.return_value = mock_repo

            result = await delete_user(DeleteUserInput(user_id="user-to-delete"))

            assert result["success"] is True
            assert result["message"] == "User deleted"
            mock_repo.delete.assert_called_once_with("user-to-delete")

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, mock_admin_user):
        """Delete non-existent user raises error."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.delete.return_value = False
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="User not found"):
                await delete_user(DeleteUserInput(user_id="nonexistent"))

    @pytest.mark.asyncio
    async def test_delete_user_self_protection(self, mock_admin_user):
        """User cannot delete their own account."""
        set_user_info(mock_admin_user)

        with pytest.raises(ValueError, match="Cannot delete your own account"):
            await delete_user(DeleteUserInput(user_id=mock_admin_user["id"]))

    @pytest.mark.asyncio
    async def test_delete_user_self_protection_non_admin(self, mock_regular_user):
        """Regular user cannot delete their own account."""
        set_user_info(mock_regular_user)

        # Non-admin user trying to delete any user (including self) should be denied by decorator first
        with pytest.raises(ValueError, match="Insufficient permissions"):
            await delete_user(DeleteUserInput(user_id=mock_regular_user["id"]))

    @pytest.mark.asyncio
    async def test_delete_user_non_admin_denied(self, mock_regular_user):
        """Non-admin user cannot delete users."""
        set_user_info(mock_regular_user)

        with pytest.raises(ValueError, match="Insufficient permissions"):
            await delete_user(DeleteUserInput(user_id="any-user-id"))

    @pytest.mark.asyncio
    async def test_delete_user_admin_can_delete_any(self, mock_admin_user):
        """Admin can delete any user (except themselves, checked above)."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.delete.return_value = True
            mock_repo_factory.return_value = mock_repo

            result = await delete_user(DeleteUserInput(user_id="other-user-id"))

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_delete_user_invalid_uuid(self, mock_admin_user):
        """Invalid UUID format is accepted as string (UUID validation not enforced)."""
        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.delete.return_value = False  # User not found / not deleted
            mock_repo_factory.return_value = mock_repo

            # Invalid UUID is accepted, but user won't be found
            with pytest.raises(ValueError, match="User not found"):
                await delete_user(DeleteUserInput(user_id="not-a-uuid"))


class TestAdminAuthorization:
    """Tests for admin authorization requirements."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_require_admin_scope_decorator(self):
        """All admin tools require ADMIN scope."""
        from app.db.models import Scope
        from app.tools.auth import get_tool_auth_level

        assert get_tool_auth_level("list_users") == Scope.ADMIN
        assert get_tool_auth_level("search_users") == Scope.ADMIN
        assert get_tool_auth_level("get_user") == Scope.ADMIN
        assert get_tool_auth_level("update_user") == Scope.ADMIN
        assert get_tool_auth_level("delete_user") == Scope.ADMIN


class TestConcurrentRequests:
    """Tests for concurrent admin operations."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_concurrent_list_users(self, mock_admin_user, mock_user_list):
        """Multiple concurrent list_users requests should work independently."""
        import asyncio

        set_user_info(mock_admin_user)

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = mock_user_list
            mock_repo_factory.return_value = mock_repo

            # Run 5 concurrent list_users calls
            tasks = [list_users(ListUsersInput()) for _ in range(5)]
            results = await asyncio.gather(*tasks)

            assert len(results) == 5
            assert all(len(r) == 2 for r in results)
            # Should be called 5 times (once per task)
            assert mock_repo.list_all.call_count == 5

    @pytest.fixture
    def mock_auth_service(self):
        mock = MagicMock()
        mock.hash_password.return_value = "hashed_password"
        return mock

    @pytest.mark.asyncio
    async def test_concurrent_updates_same_user(self, mock_admin_user, mock_user_response, mock_auth_service):
        """Concurrent updates to same user should be handled."""
        import asyncio

        set_user_info(mock_admin_user)
        mock_user_response.id = "user-456"

        with patch("app.tools.admin_tools.get_user_repository") as mock_repo_factory, \
             patch("app.tools.admin_tools.get_auth_service") as mock_auth_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_user_response
            mock_repo.update.return_value = mock_user_response
            mock_repo_factory.return_value = mock_repo
            mock_auth_factory.return_value = mock_auth_service

            async def update_email(email):
                return await update_user(UpdateUserInput(user_id="user-456", email=email))

            # Run 3 concurrent updates with different emails
            tasks = [
                update_email("email1@example.com"),
                update_email("email2@example.com"),
                update_email("email3@example.com"),
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All should succeed (last write wins unless repo has locking)
            assert len(results) == 3
            # All should have called update
            assert mock_repo.update.call_count == 3
