
from fastapi import APIRouter, HTTPException, status
from shared.db import get_collection_repository

from rest_api.deps import DbDep, UserDep
from rest_api.schemas import (
    CollectionCreate,
    CollectionListItem,
    CollectionListResponse,
    CollectionResponse,
    CollectionUpdate,
    ErrorResponse,
    MessageResponse,
)

router = APIRouter(prefix="/collections", tags=["Collections"])


@router.post(
    "",
    response_model=CollectionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_collection(
    body: CollectionCreate,
    db: DbDep,
    user: UserDep,
):
    collection_repo = get_collection_repository()

    collection = await collection_repo.create(
        user_id=user.user_id,
        name=body.name,
    )

    return CollectionResponse(
        id=collection.id,
        name=collection.name,
        document_count=0,
        cat_count=0,
        created_at=collection.created_at,
        updated_at=None,
    )


@router.get(
    "",
    response_model=CollectionListResponse,
)
async def list_collections(
    db: DbDep,
    user: UserDep,
):
    collection_repo = get_collection_repository()
    collections = await collection_repo.list_by_user(user.user_id)

    items = [
        CollectionListItem(
            id=c["id"],
            name=c["name"],
            document_count=0,
            cat_count=0,
            created_at=c["created_at"],
        )
        for c in collections
    ]

    return CollectionListResponse(collections=items)


@router.get(
    "/{collection_id}",
    response_model=CollectionResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Collection not found"},
    },
)
async def get_collection(
    collection_id: str,
    db: DbDep,
    user: UserDep,
):
    collection_repo = get_collection_repository()
    collection = await collection_repo.get_by_id(collection_id)

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

    return CollectionResponse(
        id=collection["id"],
        name=collection["name"],
        document_count=collection.get("document_count", 0),
        cat_count=collection.get("cat_count", 0),
        created_at=collection["created_at"],
        updated_at=collection.get("updated_at"),
    )


@router.patch(
    "/{collection_id}",
    response_model=CollectionResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Collection not found"},
    },
)
async def rename_collection(
    collection_id: str,
    body: CollectionUpdate,
    db: DbDep,
    user: UserDep,
):
    collection_repo = get_collection_repository()
    collection = await collection_repo.get_by_id(collection_id)

    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COLLECTION_NOT_FOUND", "message": "Collection not found"},
        )

    if collection["user_id"] != user.user_id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Cannot modify another user's collection"},
        )

    updated = await collection_repo.rename(collection_id, name=body.name)

    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "RENAME_FAILED", "message": "Failed to rename collection"},
        )

    return CollectionResponse(
        id=updated.id,
        name=updated.name,
        document_count=updated.document_count,
        cat_count=updated.cat_count,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.delete(
    "/{collection_id}",
    response_model=MessageResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Collection not found"},
        400: {"model": ErrorResponse, "description": "Collection has active CATs"},
    },
)
async def delete_collection(
    collection_id: str,
    db: DbDep,
    user: UserDep,
):
    collection_repo = get_collection_repository()

    collection = await collection_repo.get_by_id(collection_id)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COLLECTION_NOT_FOUND", "message": "Collection not found"},
        )

    if collection["user_id"] != user.user_id and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Cannot delete another user's collection"},
        )

    cat_count = collection.get("cat_count", 0)
    if cat_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "COLLECTION_HAS_ACTIVE_CATS",
                "message": "Cannot delete collection with active CATs",
            },
        )

    await collection_repo.delete(collection_id)
    return MessageResponse(message="Collection deleted successfully")
