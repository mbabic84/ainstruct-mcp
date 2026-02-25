from fastapi import APIRouter, HTTPException, Query, status

from app.db import (
    get_cat_repository,
    get_collection_repository,
    get_pat_token_repository,
    get_user_repository,
)
from app.rest.deps import AdminDep, DbDep
from app.rest.schemas import (
    ErrorResponse,
    MessageResponse,
    UserDetailResponse,
    UserListItem,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.services import get_auth_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get(
    "/users",
    response_model=UserListResponse,
)
async def list_users(
    db: DbDep,
    admin: AdminDep,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    user_repo = get_user_repository()
    users = user_repo.list_all(limit=limit, offset=offset)
    total = user_repo.count_all()

    items = [
        UserListItem(
            id=u.id,
            email=u.email,
            username=u.username,
            is_active=u.is_active,
            is_superuser=u.is_superuser,
            created_at=u.created_at,
        )
        for u in users
    ]

    return UserListResponse(
        users=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/users/{user_id}",
    response_model=UserDetailResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def get_user(
    user_id: str,
    db: DbDep,
    admin: AdminDep,
):
    user_repo = get_user_repository()
    collection_repo = get_collection_repository()
    pat_repo = get_pat_token_repository()
    cat_repo = get_cat_repository()

    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    collections = collection_repo.list_by_user(user_id)
    pats = pat_repo.list_by_user(user_id)
    cats = cat_repo.list_all(user_id)

    return UserDetailResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        collection_count=len(collections),
        pat_count=len(pats),
        cat_count=len(cats),
    )


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def update_user(
    user_id: str,
    body: UserUpdate,
    db: DbDep,
    admin: AdminDep,
):
    auth_service = get_auth_service()
    user_repo = get_user_repository()
    user = user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    update_data = {}
    if body.email is not None:
        update_data["email"] = body.email
    if body.username is not None:
        update_data["username"] = body.username
    if body.password is not None:
        update_data["password_hash"] = auth_service.hash_password(body.password)
    if body.is_active is not None:
        update_data["is_active"] = body.is_active
    if body.is_superuser is not None:
        update_data["is_superuser"] = body.is_superuser

    if update_data:
        user_repo.update(user_id, **update_data)

    updated = user_repo.get_by_id(user_id)
    return UserResponse(
        id=updated.id,
        email=updated.email,
        username=updated.username,
        is_active=updated.is_active,
        is_superuser=updated.is_superuser,
        created_at=updated.created_at,
    )


@router.delete(
    "/users/{user_id}",
    response_model=MessageResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        400: {"model": ErrorResponse, "description": "Cannot delete self"},
    },
)
async def delete_user(
    user_id: str,
    db: DbDep,
    admin: AdminDep,
):
    user_repo = get_user_repository()
    user = user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    if user.id == admin.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CANNOT_DELETE_SELF", "message": "Cannot delete your own account"},
        )

    user_repo.delete(user_id)
    return MessageResponse(message="User deleted successfully")
