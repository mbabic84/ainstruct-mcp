import pytest
from unittest.mock import MagicMock, patch

from app.tools.user_tools import (
    LoginInput,
    RefreshInput,
    RegisterInput,
    user_login,
    user_profile,
    user_refresh,
    user_register,
)
from app.tools.context import set_user_info, clear_all_auth


@pytest.fixture
def mock_user():
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "username": "testuser",
        "password_hash": "$2b$12$hashedpassword",
        "is_active": True,
        "is_superuser": False,
        "created_at": "2026-01-01T00:00:00",
    }


@pytest.fixture
def mock_superuser():
    return {
        "id": "admin-user-id",
        "email": "admin@example.com",
        "username": "admin",
        "password_hash": "$2b$12$hashedpassword",
        "is_active": True,
        "is_superuser": True,
        "created_at": "2026-01-01T00:00:00",
    }


class TestUserRegistration:
    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_register_success(self):
        with (
            patch("app.tools.user_tools.get_user_repository") as mock_repo_factory,
            patch("app.tools.user_tools.get_auth_service") as mock_auth_factory,
            patch("app.tools.user_tools.get_collection_repository") as mock_coll_factory,
        ):
            mock_repo = MagicMock()
            mock_repo.get_by_username.return_value = None
            mock_repo.get_by_email.return_value = None
            mock_repo.create.return_value = MagicMock(
                id="new-user-id",
                email="new@example.com",
                username="newuser",
                is_active=True,
                is_superuser=False,
                created_at="2026-01-01T00:00:00",
            )
            mock_repo_factory.return_value = mock_repo

            mock_auth = MagicMock()
            mock_auth.hash_password.return_value = "hashed_password"
            mock_auth_factory.return_value = mock_auth

            mock_coll_repo = MagicMock()
            mock_coll_repo.create.return_value = MagicMock(
                id="collection-id",
                name="default",
            )
            mock_coll_factory.return_value = mock_coll_repo

            result = await user_register(RegisterInput(
                email="new@example.com",
                username="newuser",
                password="password123",
            ))

            assert result.id == "new-user-id"
            assert result.email == "new@example.com"
            assert result.username == "newuser"
            mock_repo.create.assert_called_once()
            mock_coll_repo.create.assert_called_once_with(user_id="new-user-id", name="default")

    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, mock_user):
        with patch("app.tools.user_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_username.return_value = mock_user
            mock_repo_factory.return_value = mock_repo
            
            with pytest.raises(ValueError, match="Username already exists"):
                await user_register(RegisterInput(
                    email="different@example.com",
                    username="testuser",
                    password="password123",
                ))

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, mock_user):
        with patch("app.tools.user_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_username.return_value = None
            mock_repo.get_by_email.return_value = MagicMock(email="test@example.com")
            mock_repo_factory.return_value = mock_repo
            
            with pytest.raises(ValueError, match="Email already exists"):
                await user_register(RegisterInput(
                    email="test@example.com",
                    username="different",
                    password="password123",
                ))


class TestUserLogin:
    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_login_success(self, mock_user):
        with patch("app.tools.user_tools.get_user_repository") as mock_repo_factory, \
             patch("app.tools.user_tools.get_auth_service") as mock_auth_factory:
            
            mock_repo = MagicMock()
            mock_repo.get_by_username.return_value = mock_user
            mock_repo_factory.return_value = mock_repo
            
            mock_auth = MagicMock()
            mock_auth.verify_password.return_value = True
            mock_auth.create_access_token.return_value = "access_token"
            mock_auth.create_refresh_token.return_value = "refresh_token"
            mock_auth.get_access_token_expiry.return_value = 1800
            mock_auth_factory.return_value = mock_auth
            
            result = await user_login(LoginInput(
                username="testuser",
                password="password123",
            ))
            
            assert result.access_token == "access_token"
            assert result.refresh_token == "refresh_token"
            assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_login_invalid_username(self):
        with patch("app.tools.user_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_username.return_value = None
            mock_repo_factory.return_value = mock_repo
            
            with pytest.raises(ValueError, match="Invalid username or password"):
                await user_login(LoginInput(
                    username="nonexistent",
                    password="password123",
                ))

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, mock_user):
        with patch("app.tools.user_tools.get_user_repository") as mock_repo_factory, \
             patch("app.tools.user_tools.get_auth_service") as mock_auth_factory:
            
            mock_repo = MagicMock()
            mock_repo.get_by_username.return_value = mock_user
            mock_repo_factory.return_value = mock_repo
            
            mock_auth = MagicMock()
            mock_auth.verify_password.return_value = False
            mock_auth_factory.return_value = mock_auth
            
            with pytest.raises(ValueError, match="Invalid username or password"):
                await user_login(LoginInput(
                    username="testuser",
                    password="wrongpassword",
                ))

    @pytest.mark.asyncio
    async def test_login_disabled_user(self, mock_user):
        mock_user["is_active"] = False
        
        with patch("app.tools.user_tools.get_user_repository") as mock_repo_factory, \
             patch("app.tools.user_tools.get_auth_service") as mock_auth_factory:
            
            mock_repo = MagicMock()
            mock_repo.get_by_username.return_value = mock_user
            mock_repo_factory.return_value = mock_repo
            
            mock_auth = MagicMock()
            mock_auth.verify_password.return_value = True
            mock_auth_factory.return_value = mock_auth
            
            with pytest.raises(ValueError, match="User account is disabled"):
                await user_login(LoginInput(
                    username="testuser",
                    password="password123",
                ))


class TestUserProfile:
    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_profile_success(self, mock_user):
        set_user_info({
            "id": mock_user["id"],
            "username": mock_user["username"],
            "email": mock_user["email"],
            "is_superuser": False,
        })
        
        with patch("app.tools.user_tools.get_user_repository") as mock_repo_factory:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = MagicMock(
                id=mock_user["id"],
                email=mock_user["email"],
                username=mock_user["username"],
                is_active=True,
                is_superuser=False,
                created_at=mock_user["created_at"],
            )
            mock_repo_factory.return_value = mock_repo
            
            result = await user_profile()
            
            assert result.id == mock_user["id"]
            assert result.email == mock_user["email"]

    @pytest.mark.asyncio
    async def test_profile_not_authenticated(self):
        clear_all_auth()
        
        with pytest.raises(ValueError, match="Not authenticated"):
            await user_profile()


class TestTokenRefresh:
    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_refresh_success(self, mock_user):
        with patch("app.tools.user_tools.get_auth_service") as mock_auth_factory, \
             patch("app.tools.user_tools.get_user_repository") as mock_repo_factory:
            
            mock_auth = MagicMock()
            mock_auth.validate_refresh_token.return_value = {"sub": mock_user["id"]}
            mock_auth.create_access_token.return_value = "new_access_token"
            mock_auth.create_refresh_token.return_value = "new_refresh_token"
            mock_auth.get_access_token_expiry.return_value = 1800
            mock_auth_factory.return_value = mock_auth
            
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = MagicMock(
                id=mock_user["id"],
                email=mock_user["email"],
                username=mock_user["username"],
                is_active=True,
                is_superuser=False,
            )
            mock_repo_factory.return_value = mock_repo
            
            result = await user_refresh(RefreshInput(refresh_token="valid_refresh_token"))
            
            assert result.access_token == "new_access_token"
            assert result.refresh_token == "new_refresh_token"

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self):
        with patch("app.tools.user_tools.get_auth_service") as mock_auth_factory:
            mock_auth = MagicMock()
            mock_auth.validate_refresh_token.return_value = None
            mock_auth_factory.return_value = mock_auth
            
            with pytest.raises(ValueError, match="Invalid or expired refresh token"):
                await user_refresh(RefreshInput(refresh_token="invalid_token"))

    @pytest.mark.asyncio
    async def test_refresh_user_not_found(self, mock_user):
        with patch("app.tools.user_tools.get_auth_service") as mock_auth_factory, \
             patch("app.tools.user_tools.get_user_repository") as mock_repo_factory:
            
            mock_auth = MagicMock()
            mock_auth.validate_refresh_token.return_value = {"sub": mock_user["id"]}
            mock_auth_factory.return_value = mock_auth
            
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_factory.return_value = mock_repo
            
            with pytest.raises(ValueError, match="User not found"):
                await user_refresh(RefreshInput(refresh_token="valid_refresh_token"))

    @pytest.mark.asyncio
    async def test_refresh_disabled_user(self, mock_user):
        mock_user["is_active"] = False
        
        with patch("app.tools.user_tools.get_auth_service") as mock_auth_factory, \
             patch("app.tools.user_tools.get_user_repository") as mock_repo_factory:
            
            mock_auth = MagicMock()
            mock_auth.validate_refresh_token.return_value = {"sub": mock_user["id"]}
            mock_auth_factory.return_value = mock_auth
            
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = MagicMock(
                id=mock_user["id"],
                is_active=False,
            )
            mock_repo_factory.return_value = mock_repo
            
            with pytest.raises(ValueError, match="User account is disabled"):
                await user_refresh(RefreshInput(refresh_token="valid_refresh_token"))
