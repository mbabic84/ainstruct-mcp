from pydantic import BaseModel

from ..db import get_collection_repository
from ..db.models import CollectionListResponse, CollectionResponse
from .context import get_current_user_id, get_pat_info, get_user_info


class CreateCollectionInput(BaseModel):
    name: str


class GetCollectionInput(BaseModel):
    collection_id: str


class DeleteCollectionInput(BaseModel):
    collection_id: str


class RenameCollectionInput(BaseModel):
    collection_id: str
    name: str


async def create_collection(input_data: CreateCollectionInput) -> CollectionResponse:
    user_id = get_current_user_id()
    if not user_id:
        raise ValueError("Not authenticated")

    repo = get_collection_repository()
    return repo.create(user_id=user_id, name=input_data.name)


async def list_collections() -> list[CollectionListResponse]:
    user_info = get_user_info()
    pat_info = get_pat_info()

    auth_info = user_info or pat_info
    if not auth_info:
        raise ValueError("JWT or PAT authentication required")

    user_id = auth_info.get("id")
    if not user_id:
        raise ValueError("Invalid user info")

    repo = get_collection_repository()
    collections = repo.list_by_user(user_id)

    return [
        CollectionListResponse(
            id=c["id"],
            name=c["name"],
            created_at=c["created_at"],
        )
        for c in collections
    ]


async def get_collection(input_data: GetCollectionInput) -> CollectionResponse:
    user_info = get_user_info()
    if not user_info:
        raise ValueError("JWT authentication required")

    repo = get_collection_repository()
    collection = repo.get_by_id(input_data.collection_id)

    if not collection:
        raise ValueError("Collection not found")

    if collection["user_id"] != user_info.get("id") and not user_info.get("is_superuser"):
        raise ValueError("Collection not found")

    return CollectionResponse(
        id=collection["id"],
        name=collection["name"],
        document_count=collection["document_count"],
        api_key_count=collection["api_key_count"],
        created_at=collection["created_at"],
    )


async def delete_collection(input_data: DeleteCollectionInput) -> dict:
    user_info = get_user_info()
    if not user_info:
        raise ValueError("JWT authentication required")

    repo = get_collection_repository()
    collection = repo.get_by_id(input_data.collection_id)

    if not collection:
        raise ValueError("Collection not found")

    if collection["user_id"] != user_info.get("id") and not user_info.get("is_superuser"):
        raise ValueError("Collection not found")

    if collection["api_key_count"] > 0:
        raise ValueError("Cannot delete collection with active API keys. Revoke all API keys first.")

    success = repo.delete(input_data.collection_id)
    if not success:
        raise ValueError("Failed to delete collection")

    return {"success": True, "message": "Collection deleted successfully"}


async def rename_collection(input_data: RenameCollectionInput) -> CollectionResponse:
    user_info = get_user_info()
    if not user_info:
        raise ValueError("JWT authentication required")

    repo = get_collection_repository()
    collection = repo.get_by_id(input_data.collection_id)

    if not collection:
        raise ValueError("Collection not found")

    if collection["user_id"] != user_info.get("id") and not user_info.get("is_superuser"):
        raise ValueError("Collection not found")

    result = repo.rename(input_data.collection_id, input_data.name)
    if not result:
        raise ValueError("Failed to rename collection")

    return result
