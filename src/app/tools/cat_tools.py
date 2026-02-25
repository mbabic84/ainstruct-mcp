from pydantic import BaseModel

from ..db import get_cat_repository, get_collection_repository
from ..db.models import CatListResponse, CatResponse, Permission
from .context import get_current_user_id, get_pat_info, get_user_info


class CreateCatInput(BaseModel):
    label: str
    collection_id: str
    permission: str = "read_write"
    expires_in_days: int | None = None


class RevokeCatInput(BaseModel):
    key_id: str


class RotateCatInput(BaseModel):
    key_id: str


async def create_cat(input_data: CreateCatInput) -> CatResponse:
    user_id = get_current_user_id()
    if not user_id:
        raise ValueError("Not authenticated")

    user_info = get_user_info()
    pat_info = get_pat_info()

    auth_info = user_info or pat_info
    if not auth_info:
        raise ValueError("JWT or PAT authentication required to create CAT tokens")

    collection_repo = get_collection_repository()
    collection = collection_repo.get_by_id(input_data.collection_id)

    if not collection:
        raise ValueError("Collection not found")

    if collection["user_id"] != auth_info.get("id") and not auth_info.get("is_superuser"):
        raise ValueError("Collection not found")

    try:
        permission = Permission(input_data.permission)
    except ValueError:
        raise ValueError(f"Invalid permission: {input_data.permission}. Must be 'read' or 'read_write'")

    repo = get_cat_repository()
    key_id, key = repo.create(
        label=input_data.label,
        collection_id=input_data.collection_id,
        user_id=user_id,
        permission=permission,
        expires_in_days=input_data.expires_in_days,
    )

    key_info = repo.get_by_id(key_id)
    if not key_info:
        raise ValueError("Failed to retrieve key info")

    return CatResponse(
        id=key_id,
        label=input_data.label,
        key=key,
        collection_id=input_data.collection_id,
        collection_name=collection["name"],
        permission=permission,
        created_at=key_info["created_at"],
        expires_at=key_info.get("expires_at"),
        is_active=True,
        last_used=None,
    )


async def list_cats() -> list[CatListResponse]:
    user_info = get_user_info()
    pat_info = get_pat_info()

    auth_info = user_info or pat_info
    user_id = None

    if auth_info and not auth_info.get("is_superuser"):
        user_id = auth_info.get("id")

    repo = get_cat_repository()
    keys = repo.list_all(user_id=user_id)

    return [
        CatListResponse(
            id=k["id"],
            label=k["label"],
            collection_id=k["collection_id"],
            collection_name=k.get("collection_name", ""),
            permission=k["permission"],
            created_at=k["created_at"],
            expires_at=k.get("expires_at"),
            is_active=k["is_active"],
            last_used=k.get("last_used"),
        )
        for k in keys
    ]


async def revoke_cat(input_data: RevokeCatInput) -> dict:
    repo = get_cat_repository()

    key_info = repo.get_by_id(input_data.key_id)
    if not key_info:
        raise ValueError("CAT token not found")

    user_info = get_user_info()
    pat_info = get_pat_info()

    auth_info = user_info or pat_info
    if auth_info and not auth_info.get("is_superuser"):
        if key_info.get("user_id") and key_info.get("user_id") != auth_info.get("id"):
            raise ValueError("You can only revoke your own CAT tokens")

    success = repo.revoke(input_data.key_id)
    if not success:
        raise ValueError("Failed to revoke CAT token")

    return {"success": True, "message": "CAT token revoked"}


async def rotate_cat(input_data: RotateCatInput) -> CatResponse:
    repo = get_cat_repository()

    key_info = repo.get_by_id(input_data.key_id)
    if not key_info:
        raise ValueError("CAT token not found")

    user_info = get_user_info()
    pat_info = get_pat_info()

    auth_info = user_info or pat_info
    if auth_info and not auth_info.get("is_superuser"):
        if key_info.get("user_id") and key_info.get("user_id") != auth_info.get("id"):
            raise ValueError("You can only rotate your own CAT tokens")

    result = repo.rotate(input_data.key_id)
    if not result:
        raise ValueError("Failed to rotate CAT token")

    new_key_id, new_key = result
    new_key_info = repo.get_by_id(new_key_id)
    if not new_key_info:
        raise ValueError("Failed to retrieve new key info")

    return CatResponse(
        id=new_key_id,
        label=new_key_info["label"],
        key=new_key,
        collection_id=new_key_info["collection_id"],
        collection_name=new_key_info.get("collection_name", ""),
        permission=new_key_info["permission"],
        created_at=new_key_info["created_at"],
        expires_at=new_key_info.get("expires_at"),
        is_active=True,
        last_used=None,
    )
