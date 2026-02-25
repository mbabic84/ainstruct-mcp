import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from app.tools.pat_tools import (
    CreatePatTokenInput,
    RevokePatTokenInput,
    RotatePatTokenInput,
    create_pat_token,
    list_pat_tokens,
    revoke_pat_token,
    rotate_pat_token,
)
from app.tools.context import set_user_info, set_pat_info, clear_all_auth
from app.db.models import Scope


@pytest.fixture
def mock_user_info():
    return {
        "id": "test-user-id",
        "username": "testuser",
        "email": "test@example.com",
        "is_superuser": False,
        "scopes": [Scope.READ, Scope.WRITE],
    }


@pytest.fixture
def mock_admin_info():
    return {
        "id": "admin-user-id",
        "username": "admin",
        "email": "admin@example.com",
        "is_superuser": True,
        "scopes": [Scope.READ, Scope.WRITE, Scope.ADMIN],
    }


@pytest.fixture
def mock_pat_token():
    return {
        "id": "pat-id-123",
        "label": "Test PAT",
        "user_id": "test-user-id",
        "scopes": [Scope.READ, Scope.WRITE],
        "created_at": datetime.now(timezone.utc),
        "expires_at": None,
        "is_active": True,
        "last_used": None,
    }


class TestCreatePatToken:
    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_create_pat_token_success(self, mock_user_info, mock_pat_token):
        set_user_info(mock_user_info)

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.create.return_value = ("pat-id-123", "pat_live_testtoken123")
            mock_repo.get_by_id.return_value = mock_pat_token
            mock_repo_factory.return_value = mock_repo

            result = await create_pat_token(CreatePatTokenInput(
                label="My PAT Token",
            ))

            assert result.id == "pat-id-123"
            assert result.token == "pat_live_testtoken123"
            assert result.label == "My PAT Token"
            assert result.user_id == "test-user-id"
            assert Scope.READ in result.scopes
            assert Scope.WRITE in result.scopes

    @pytest.mark.asyncio
    async def test_create_pat_token_with_custom_expiry(self, mock_user_info, mock_pat_token):
        set_user_info(mock_user_info)

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.create.return_value = ("pat-id-123", "pat_live_testtoken123")
            mock_repo.get_by_id.return_value = mock_pat_token
            mock_repo_factory.return_value = mock_repo

            result = await create_pat_token(CreatePatTokenInput(
                label="My PAT Token",
                expires_in_days=180,
            ))

            assert result.id == "pat-id-123"
            mock_repo.create.assert_called_once()
            call_kwargs = mock_repo.create.call_args[1]
            assert call_kwargs["expires_in_days"] == 180

    @pytest.mark.asyncio
    async def test_create_pat_token_exceeds_max_expiry(self, mock_user_info):
        set_user_info(mock_user_info)

        with pytest.raises(ValueError, match="Maximum expiry days"):
            await create_pat_token(CreatePatTokenInput(
                label="My PAT Token",
                expires_in_days=400,
            ))

    @pytest.mark.asyncio
    async def test_create_pat_token_invalid_expiry(self, mock_user_info):
        set_user_info(mock_user_info)

        with pytest.raises(ValueError, match="Expiry days must be at least 1"):
            await create_pat_token(CreatePatTokenInput(
                label="My PAT Token",
                expires_in_days=0,
            ))

    @pytest.mark.asyncio
    async def test_create_pat_token_not_authenticated(self):
        with pytest.raises(ValueError, match="JWT authentication required"):
            await create_pat_token(CreatePatTokenInput(
                label="My PAT Token",
            ))

    @pytest.mark.asyncio
    async def test_create_pat_token_inherits_user_scopes(self, mock_admin_info, mock_pat_token):
        set_user_info(mock_admin_info)

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.create.return_value = ("pat-id-123", "pat_live_testtoken123")
            mock_pat_token["scopes"] = [Scope.READ, Scope.WRITE, Scope.ADMIN]
            mock_repo.get_by_id.return_value = mock_pat_token
            mock_repo_factory.return_value = mock_repo

            result = await create_pat_token(CreatePatTokenInput(
                label="Admin PAT",
            ))

            call_kwargs = mock_repo.create.call_args[1]
            assert "admin" in call_kwargs["scopes"]


class TestListPatTokens:
    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_list_pat_tokens_as_user(self, mock_user_info, mock_pat_token):
        set_user_info(mock_user_info)

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = [mock_pat_token]
            mock_repo_factory.return_value = mock_repo

            result = await list_pat_tokens()

            assert len(result) == 1
            mock_repo.list_all.assert_called_once_with(user_id=mock_user_info["id"])

    @pytest.mark.asyncio
    async def test_list_pat_tokens_as_admin(self, mock_admin_info, mock_pat_token):
        set_user_info(mock_admin_info)

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.list_all.return_value = [mock_pat_token]
            mock_repo_factory.return_value = mock_repo

            result = await list_pat_tokens()

            assert len(result) == 1
            mock_repo.list_all.assert_called_once_with(user_id=None)


class TestRevokePatToken:
    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_revoke_own_token(self, mock_user_info, mock_pat_token):
        set_user_info(mock_user_info)

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_pat_token
            mock_repo.revoke.return_value = True
            mock_repo_factory.return_value = mock_repo

            result = await revoke_pat_token(RevokePatTokenInput(pat_id="pat-id-123"))

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_revoke_other_user_token_forbidden(self, mock_user_info, mock_pat_token):
        set_user_info(mock_user_info)
        mock_pat_token["user_id"] = "different-user-id"

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_pat_token
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="You can only revoke your own PAT tokens"):
                await revoke_pat_token(RevokePatTokenInput(pat_id="pat-id-123"))

    @pytest.mark.asyncio
    async def test_revoke_other_user_token_as_admin(self, mock_admin_info, mock_pat_token):
        set_user_info(mock_admin_info)
        mock_pat_token["user_id"] = "different-user-id"

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_pat_token
            mock_repo.revoke.return_value = True
            mock_repo_factory.return_value = mock_repo

            result = await revoke_pat_token(RevokePatTokenInput(pat_id="pat-id-123"))

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_token(self, mock_user_info):
        set_user_info(mock_user_info)

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="PAT token not found"):
                await revoke_pat_token(RevokePatTokenInput(pat_id="nonexistent"))


class TestRotatePatToken:
    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_rotate_own_token(self, mock_user_info, mock_pat_token):
        set_user_info(mock_user_info)

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_pat_token
            mock_repo.rotate.return_value = ("new-pat-id", "pat_live_newtoken123")
            mock_repo_factory.return_value = mock_repo

            result = await rotate_pat_token(RotatePatTokenInput(pat_id="pat-id-123"))

            assert result.id == "new-pat-id"
            assert result.token == "pat_live_newtoken123"

    @pytest.mark.asyncio
    async def test_rotate_other_user_token_forbidden(self, mock_user_info, mock_pat_token):
        set_user_info(mock_user_info)
        mock_pat_token["user_id"] = "different-user-id"

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_pat_token
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="You can only rotate your own PAT tokens"):
                await rotate_pat_token(RotatePatTokenInput(pat_id="pat-id-123"))

    @pytest.mark.asyncio
    async def test_rotate_nonexistent_token(self, mock_user_info):
        set_user_info(mock_user_info)

        with patch("app.tools.pat_tools.get_pat_token_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_factory.return_value = mock_repo

            with pytest.raises(ValueError, match="PAT token not found"):
                await rotate_pat_token(RotatePatTokenInput(pat_id="nonexistent"))


class TestPatTokenAuthentication:
    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_pat_token_can_access_tools(self, mock_pat_token):
        set_pat_info({
            "id": "pat-id-123",
            "user_id": "test-user-id",
            "username": "testuser",
            "email": "test@example.com",
            "scopes": [Scope.READ, Scope.WRITE],
            "is_superuser": False,
        })

        from app.tools.context import get_current_user_id, has_scope, has_write_permission

        assert get_current_user_id() == "test-user-id"
        assert has_scope(Scope.READ) is True
        assert has_scope(Scope.WRITE) is True
        assert has_write_permission() is True

    @pytest.mark.asyncio
    async def test_pat_token_read_only(self):
        set_pat_info({
            "id": "pat-id-123",
            "user_id": "test-user-id",
            "username": "testuser",
            "email": "test@example.com",
            "scopes": [Scope.READ],
            "is_superuser": False,
        })

        from app.tools.context import has_scope, has_write_permission

        assert has_scope(Scope.READ) is True
        assert has_scope(Scope.WRITE) is False
        assert has_write_permission() is False

    @pytest.mark.asyncio
    async def test_pat_token_superuser(self):
        set_pat_info({
            "id": "pat-id-123",
            "user_id": "admin-user-id",
            "username": "admin",
            "email": "admin@example.com",
            "scopes": [Scope.READ, Scope.WRITE, Scope.ADMIN],
            "is_superuser": True,
        })

        from app.tools.context import has_scope, has_write_permission

        assert has_scope(Scope.READ) is True
        assert has_scope(Scope.WRITE) is True
        assert has_scope(Scope.ADMIN) is True
        assert has_write_permission() is True
