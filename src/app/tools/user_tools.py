from pydantic import BaseModel

from ..config import settings
from ..db import get_collection_repository, get_user_repository
from ..db.models import Scope, TokenResponse, UserResponse
from ..services import get_auth_service


class RegisterInput(BaseModel):
    email: str
    username: str
    password: str


class LoginInput(BaseModel):
    username: str
    password: str


class RefreshInput(BaseModel):
    refresh_token: str


class PromoteAdminInput(BaseModel):
    user_id: str
    admin_api_key: str | None = None


async def user_register(input_data: RegisterInput) -> UserResponse:
    repo = get_user_repository()
    auth_service = get_auth_service()

    existing = repo.get_by_username(input_data.username)
    if existing:
        raise ValueError("Username already exists")

    existing_email = repo.get_by_email(input_data.email)
    if existing_email:
        raise ValueError("Email already exists")

    password_hash = auth_service.hash_password(input_data.password)

    user = repo.create(
        email=input_data.email,
        username=input_data.username,
        password_hash=password_hash,
        is_superuser=False,
    )

    collection_repo = get_collection_repository()
    collection_repo.create(user_id=user.id, name="default")

    return user


async def promote_to_admin(input_data: PromoteAdminInput) -> UserResponse:
    repo = get_user_repository()

    all_users = repo.list_all(limit=1000)
    admin_exists = any(u.is_superuser for u in all_users)

    if admin_exists:
        if not input_data.admin_api_key or input_data.admin_api_key != settings.admin_api_key:
            raise ValueError("Admin API key required (admin already exists)")
        if not settings.admin_api_key:
            raise ValueError("Admin promotion disabled (no ADMIN_API_KEY configured)")

    user = repo.get_by_id(input_data.user_id)
    if not user:
        raise ValueError("User not found")

    if user.is_superuser:
        raise ValueError("User is already an admin")

    updated = repo.update(
        user_id=input_data.user_id,
        is_superuser=True,
    )
    if not updated:
        raise ValueError("Failed to update user")
    return updated


async def user_login(input_data: LoginInput) -> TokenResponse:
    repo = get_user_repository()
    auth_service = get_auth_service()

    user = repo.get_by_username(input_data.username)
    if not user:
        raise ValueError("Invalid username or password")

    if not auth_service.verify_password(input_data.password, user["password_hash"]):
        raise ValueError("Invalid username or password")

    if not user["is_active"]:
        raise ValueError("User account is disabled")

    scopes = [Scope.READ, Scope.WRITE]
    if user["is_superuser"]:
        scopes = [Scope.READ, Scope.WRITE, Scope.ADMIN]

    access_token = auth_service.create_access_token(
        user_id=user["id"],
        username=user["username"],
        email=user["email"],
        is_superuser=user["is_superuser"],
        scopes=scopes,
    )

    refresh_token = auth_service.create_refresh_token(user_id=user["id"])

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=auth_service.get_access_token_expiry(),
    )


async def user_profile() -> UserResponse:
    from .context import get_user_info

    user_info = get_user_info()
    if not user_info:
        raise ValueError("Not authenticated")

    repo = get_user_repository()
    user = repo.get_by_id(user_info["id"])

    if not user:
        raise ValueError("User not found")

    return user


async def user_refresh(input_data: RefreshInput) -> TokenResponse:
    auth_service = get_auth_service()
    repo = get_user_repository()

    payload = auth_service.validate_refresh_token(input_data.refresh_token)
    if not payload:
        raise ValueError("Invalid or expired refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Invalid token payload")
    user = repo.get_by_id(user_id)

    if not user:
        raise ValueError("User not found")

    if not user.is_active:
        raise ValueError("User account is disabled")

    scopes = [Scope.READ, Scope.WRITE]
    if user.is_superuser:
        scopes = [Scope.READ, Scope.WRITE, Scope.ADMIN]

    access_token = auth_service.create_access_token(
        user_id=user.id,
        username=user.username,
        email=user.email,
        is_superuser=user.is_superuser,
        scopes=scopes,
    )

    refresh_token = auth_service.create_refresh_token(user_id=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=auth_service.get_access_token_expiry(),
    )
