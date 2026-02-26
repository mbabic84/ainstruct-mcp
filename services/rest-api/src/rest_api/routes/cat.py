from fastapi import APIRouter, HTTPException, Query, status
from shared.db import get_cat_repository, get_collection_repository
from shared.db.models import Permission as ModelPermission

from rest_api.deps import DbDep, UserDep
from rest_api.schemas import (
    CatCreate,
    CatListItem,
    CatListResponse,
    CatResponse,
    ErrorResponse,
    MessageResponse,
)

router = APIRouter(prefix="/auth/cat", tags=["CAT Management"])


@router.post(
    "",
    response_model=CatResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Collection not found"},
    },
)
async def create_cat(
    body: CatCreate,
    db: DbDep,
    user: UserDep,
):
    cat_repo = get_cat_repository()
    collection_repo = get_collection_repository()

    collection = await collection_repo.get_by_id(body.collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COLLECTION_NOT_FOUND", "message": "Collection not found"},
        )

    if collection["user_id"] != user.user_id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Cannot create CAT for another user's collection"},
        )

    perm = ModelPermission.READ_WRITE if body.permission == "read_write" else ModelPermission.READ

    cat_id, token = await cat_repo.create(
        label=body.label,
        collection_id=body.collection_id,
        user_id=user.user_id,
        permission=perm,
        expires_in_days=body.expires_in_days,
    )

    cat = await cat_repo.get_by_id(cat_id)
    if cat is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "CAT_CREATE_FAILED", "message": "Failed to create CAT"},
        )

    return CatResponse(
        id=cat["id"],
        label=cat["label"],
        token=token,
        collection_id=cat["collection_id"],
        collection_name=collection["name"],
        permission=body.permission,
        created_at=cat["created_at"],
        expires_at=cat["expires_at"],
        is_active=cat["is_active"],
    )


@router.get(
    "",
    response_model=CatListResponse,
)
async def list_cats(
    db: DbDep,
    user: UserDep,
    collection_id: str | None = Query(None, description="Filter by collection"),
):
    cat_repo = get_cat_repository()

    if collection_id:
        cats = await cat_repo.list_by_user(user.user_id)
        cats = [c for c in cats if c.get("collection_id") == collection_id]
    else:
        cats = await cat_repo.list_by_user(user.user_id)

    items = [
        CatListItem(
            id=c["id"],
            label=c["label"],
            collection_id=c["collection_id"],
            collection_name=c.get("collection_name"),
            permission="read_write" if c.get("permission") == ModelPermission.READ_WRITE else "read",
            created_at=c["created_at"],
            expires_at=c.get("expires_at"),
            is_active=c["is_active"],
        )
        for c in cats
    ]

    return CatListResponse(keys=items)


@router.delete(
    "/{cat_id}",
    response_model=MessageResponse,
    responses={
        404: {"model": ErrorResponse, "description": "CAT not found"},
    },
)
async def revoke_cat(
    cat_id: str,
    db: DbDep,
    user: UserDep,
):
    cat_repo = get_cat_repository()

    cat = await cat_repo.get_by_id(cat_id)
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CAT_NOT_FOUND", "message": "CAT not found"},
        )

    if cat["user_id"] != user.user_id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Cannot revoke another user's CAT"},
        )

    await cat_repo.revoke(cat_id)
    return MessageResponse(message="CAT revoked successfully")


@router.post(
    "/{cat_id}/rotate",
    response_model=CatResponse,
    responses={
        404: {"model": ErrorResponse, "description": "CAT not found"},
    },
)
async def rotate_cat(
    cat_id: str,
    db: DbDep,
    user: UserDep,
):
    cat_repo = get_cat_repository()
    collection_repo = get_collection_repository()

    old_cat = await cat_repo.get_by_id(cat_id)
    if not old_cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CAT_NOT_FOUND", "message": "CAT not found"},
        )

    if old_cat["user_id"] != user.user_id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Cannot rotate another user's CAT"},
        )

    new_cat_id, new_token = await cat_repo.rotate(cat_id)

    new_cat = await cat_repo.get_by_id(new_cat_id)
    if new_cat is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "CAT_ROTATE_FAILED", "message": "Failed to rotate CAT"},
        )

    collection = await collection_repo.get_by_id(new_cat["collection_id"])

    return CatResponse(
        id=new_cat["id"],
        label=new_cat["label"],
        token=new_token,
        collection_id=new_cat["collection_id"],
        collection_name=collection["name"] if collection else None,
        permission="read_write" if new_cat.get("permission") == ModelPermission.READ_WRITE else "read",
        created_at=new_cat["created_at"],
        expires_at=new_cat.get("expires_at"),
        is_active=new_cat["is_active"],
    )
