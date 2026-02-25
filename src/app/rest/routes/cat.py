from fastapi import APIRouter, HTTPException, Query, status

from app.rest.deps import DbDep, UserDep
from app.rest.schemas import (
    CatCreate,
    CatListItem,
    CatListResponse,
    CatResponse,
    ErrorResponse,
    MessageResponse,
)
from app.db.models import Permission as ModelPermission
from app.db import get_cat_repository, get_collection_repository

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

    collection = collection_repo.get_by_id(body.collection_id)
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

    cat_id, token = cat_repo.create(
        label=body.label,
        collection_id=body.collection_id,
        user_id=user.user_id,
        permission=body.permission,
        expires_in_days=body.expires_in_days,
    )

    cat = cat_repo.get_by_id(cat_id)

    return CatResponse(
        id=cat["id"],
        label=cat["label"],
        token=token,
        collection_id=cat["collection_id"],
        collection_name=collection["name"],
        permission=ModelPermission(cat["permission"]),
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
    collection_repo = get_collection_repository()

    if collection_id:
        collection = collection_repo.get_by_id(collection_id)
        if not collection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "COLLECTION_NOT_FOUND", "message": "Collection not found"},
            )
        if collection["user_id"] != user.user_id and not user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "FORBIDDEN", "message": "Cannot access another user's collection"},
            )
        all_cats = cat_repo.list_all(user.user_id)
        cats = [c for c in all_cats if c["collection_id"] == collection_id]
    else:
        cats = cat_repo.list_all(user.user_id)

    tokens = []
    for cat in cats:
        collection = collection_repo.get_by_id(cat["collection_id"])
        collection_name = collection["name"] if collection else "unknown"

        tokens.append(
            CatListItem(
                id=cat["id"],
                label=cat["label"],
                collection_id=cat["collection_id"],
                collection_name=collection_name,
                permission=ModelPermission(cat["permission"]),
                created_at=cat["created_at"],
                expires_at=cat["expires_at"],
                is_active=cat["is_active"],
                last_used=cat["last_used"],
            )
        )

    return CatListResponse(tokens=tokens)


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
    collection_repo = get_collection_repository()

    cat = cat_repo.get_by_id(cat_id)
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CAT_NOT_FOUND", "message": "CAT not found"},
        )

    collection = collection_repo.get_by_id(cat["collection_id"])
    if collection and collection["user_id"] != user.user_id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Cannot revoke CAT for another user's collection"},
        )

    cat_repo.revoke(cat_id)
    return MessageResponse(message="CAT revoked successfully")
