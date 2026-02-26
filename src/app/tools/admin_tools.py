from pydantic import BaseModel, EmailStr

from ..db import get_user_repository
from ..db.models import Scope, UserResponse
from ..services import get_auth_service
from .auth import require_scope
from .context import get_user_info


class ListUsersInput(BaseModel):
    limit: int = 50
    offset: int = 0


class SearchUsersInput(BaseModel):
    query: str
    limit: int = 50
    offset: int = 0


class GetUserInput(BaseModel):
    user_id: str


class UpdateUserInput(BaseModel):
    user_id: str
    email: EmailStr | None = None
    username: str | None = None
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class DeleteUserInput(BaseModel):
    user_id: str


@require_scope(Scope.ADMIN)
async def list_users(input_data: ListUsersInput) -> list[UserResponse]:
    repo = get_user_repository()
    return await repo.list_all(limit=input_data.limit, offset=input_data.offset)


@require_scope(Scope.ADMIN)
async def search_users(input_data: SearchUsersInput) -> list[UserResponse]:
    repo = get_user_repository()
    return await repo.search(query=input_data.query, limit=input_data.limit, offset=input_data.offset)


@require_scope(Scope.ADMIN)
async def get_user(input_data: GetUserInput) -> UserResponse:
    repo = get_user_repository()
    user = await repo.get_by_id(input_data.user_id)
    if not user:
        raise ValueError("User not found")
    return user


@require_scope(Scope.ADMIN)
async def update_user(input_data: UpdateUserInput) -> UserResponse:
    repo = get_user_repository()
    auth_service = get_auth_service()

    user = await repo.get_by_id(input_data.user_id)
    if not user:
        raise ValueError("User not found")

    password_hash = None
    if input_data.password:
        password_hash = auth_service.hash_password(input_data.password)

    updated = await repo.update(
        user_id=input_data.user_id,
        email=input_data.email,
        username=input_data.username,
        password_hash=password_hash,
        is_active=input_data.is_active,
        is_superuser=input_data.is_superuser,
    )
    if not updated:
        raise ValueError("Failed to update user")
    return updated


@require_scope(Scope.ADMIN)
async def delete_user(input_data: DeleteUserInput) -> dict:
    user_info = get_user_info()
    if user_info and user_info.get("id") == input_data.user_id:
        raise ValueError("Cannot delete your own account")

    repo = get_user_repository()
    success = await repo.delete(input_data.user_id)

    if not success:
        raise ValueError("User not found")

    return {"success": True, "message": "User deleted"}
