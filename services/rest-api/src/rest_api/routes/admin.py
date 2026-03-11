from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from shared.db import (
    get_cat_repository,
    get_collection_repository,
    get_document_repository,
    get_pat_token_repository,
    get_qdrant_service,
    get_usage_repository,
    get_user_repository,
)
from shared.services import get_auth_service

from rest_api.deps import AdminApiKeyDep, AdminDep, DbDep
from rest_api.schemas import (
    ErrorResponse,
    MessageResponse,
    UsageHistoryResponse,
    UsageMonthlyResponse,
    UserDetailResponse,
    UserListItem,
    UserListResponse,
    UserResponse,
    UserUpdate,
)

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
    users = await user_repo.list_all(limit=limit, offset=offset)
    total = await user_repo.count_all()

    items = [
        UserListItem(
            user_id=u.user_id,
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
    "/users/search",
    response_model=UserListResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Query parameter required"},
    },
)
async def search_users(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: DbDep = None,
    admin: AdminDep = None,
):
    user_repo = get_user_repository()
    users = await user_repo.search(query=query, limit=limit, offset=offset)

    items = [
        UserListItem(
            user_id=u.user_id,
            email=u.email,
            username=u.username,
            is_active=u.is_active,
            is_superuser=u.is_superuser,
            created_at=u.created_at,
        )
        for u in users
    ]
    return UserListResponse(users=items, total=len(users), limit=limit, offset=offset)


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
    document_repo = get_document_repository()

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    collections = await collection_repo.list_by_user(user_id)
    pats = await pat_repo.list_by_user(user_id)
    cats = await cat_repo.list_all(user_id)
    document_count = await document_repo.count_by_user(user_id)

    def is_token_active(expires_at):
        return expires_at is None or expires_at > datetime.utcnow()

    pat_active = sum(1 for p in pats if is_token_active(p.get("expires_at")))
    pat_inactive = len(pats) - pat_active
    cat_active = sum(1 for c in cats if is_token_active(c.get("expires_at")))
    cat_inactive = len(cats) - cat_active

    return UserDetailResponse(
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
        collection_count=len(collections),
        pat_active_count=pat_active,
        pat_inactive_count=pat_inactive,
        cat_active_count=cat_active,
        cat_inactive_count=cat_inactive,
        document_count=document_count,
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
    user = await user_repo.get_by_id(user_id)

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
        await user_repo.update(user_id, **update_data)

    updated = await user_repo.get_by_id(user_id)
    return UserResponse(
        user_id=updated.user_id,
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
        500: {"model": ErrorResponse, "description": "Qdrant deletion failed"},
    },
)
async def delete_user(
    user_id: str,
    db: DbDep,
    admin: AdminDep,
):
    user_repo = get_user_repository()
    collection_repo = get_collection_repository()

    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    if user.user_id == admin.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CANNOT_DELETE_SELF", "message": "Cannot delete your own account"},
        )

    collections = await collection_repo.list_by_user(user_id)

    for collection in collections:
        qdrant_service = get_qdrant_service(collection["qdrant_collection"])
        try:
            await qdrant_service.delete_collection(collection["qdrant_collection"])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "QDRANT_DELETE_FAILED",
                    "message": f"Failed to delete collection '{collection['name']}' from vector store: {e}",
                },
            )

    await user_repo.delete(user_id)
    return MessageResponse(message="User deleted successfully")


@router.post(
    "/users/{user_id}/promote",
    response_model=UserResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
        401: {"model": ErrorResponse, "description": "Invalid admin API key"},
        503: {"model": ErrorResponse, "description": "Admin API key not configured"},
    },
    dependencies=[],
)
async def promote_user(
    user_id: str,
    admin_api_key: AdminApiKeyDep,
    db: DbDep,
):
    user_repo = get_user_repository()

    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    await user_repo.update(user_id, is_superuser=True)

    updated = await user_repo.get_by_id(user_id)
    return UserResponse(
        user_id=updated.user_id,
        email=updated.email,
        username=updated.username,
        is_active=updated.is_active,
        is_superuser=updated.is_superuser,
        created_at=updated.created_at,
    )


@router.get(
    "/usage/{user_id}",
    response_model=UsageMonthlyResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def get_user_usage(
    user_id: str,
    year_month: str = Query(None, description="Year-month in format YYYY-MM (e.g., 2026-03)"),
    db: DbDep = None,
    admin: AdminDep = None,
):
    usage_repo = get_usage_repository()
    result = await usage_repo.get_monthly_usage(user_id, year_month)

    return UsageMonthlyResponse(
        year_month=result["year_month"],
        api_requests=result["api_requests"],
        mcp_requests=result["mcp_requests"],
        total_requests=result["total_requests"],
    )


@router.get(
    "/usage/{user_id}/history",
    response_model=UsageHistoryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "User not found"},
    },
)
async def get_user_usage_history(
    user_id: str,
    months: int = Query(6, ge=1, le=24, description="Number of months to retrieve"),
    db: DbDep = None,
    admin: AdminDep = None,
):
    usage_repo = get_usage_repository()
    history = await usage_repo.get_usage_history(user_id, months=months)

    return UsageHistoryResponse(
        history=[
            {
                "year_month": h["year_month"],
                "api_requests": h["api_requests"],
                "mcp_requests": h["mcp_requests"],
                "total": h["total"],
            }
            for h in history
        ]
    )
