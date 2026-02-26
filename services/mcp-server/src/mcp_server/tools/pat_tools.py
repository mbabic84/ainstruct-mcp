from pydantic import BaseModel
from shared.config import settings
from shared.db import get_pat_token_repository
from shared.db.models import PatTokenListResponse, PatTokenResponse, Scope

from mcp_server.tools.context import get_user_info


class CreatePatTokenInput(BaseModel):
    label: str
    expires_in_days: int | None = None


class RevokePatTokenInput(BaseModel):
    pat_id: str


class RotatePatTokenInput(BaseModel):
    pat_id: str


async def create_pat_token(input_data: CreatePatTokenInput) -> PatTokenResponse:
    user_info = get_user_info()
    if not user_info:
        raise ValueError("JWT authentication required to create PAT tokens")

    user_id = user_info.get("id")
    if not user_id:
        raise ValueError("User ID not found in token")

    if input_data.expires_in_days is not None:
        if input_data.expires_in_days > settings.pat_max_expiry_days:
            raise ValueError(f"Maximum expiry days is {settings.pat_max_expiry_days}")
        if input_data.expires_in_days < 1:
            raise ValueError("Expiry days must be at least 1")

    scopes = user_info.get("scopes", [Scope.READ.value])
    scopes_str = [s.value if isinstance(s, Scope) else str(s) for s in scopes]

    repo = get_pat_token_repository()
    token_id, token = await repo.create(
        label=input_data.label,
        user_id=user_id,
        scopes=scopes_str,
        expires_in_days=input_data.expires_in_days,
    )

    token_info = await repo.get_by_id(token_id)
    if not token_info:
        raise ValueError("Failed to retrieve token info")

    return PatTokenResponse(
        id=token_id,
        label=input_data.label,
        token=token,
        user_id=user_id,
        scopes=token_info["scopes"],
        created_at=token_info["created_at"],
        expires_at=token_info.get("expires_at"),
        is_active=True,
        last_used=None,
    )


async def list_pat_tokens() -> list[PatTokenListResponse]:
    user_info = get_user_info()
    user_id = None

    if user_info and not user_info.get("is_superuser"):
        user_id = user_info.get("id")

    repo = get_pat_token_repository()
    tokens = await repo.list_all(user_id=user_id)

    return [
        PatTokenListResponse(
            id=t["id"],
            label=t["label"],
            user_id=t["user_id"],
            scopes=t["scopes"],
            created_at=t["created_at"],
            expires_at=t.get("expires_at"),
            is_active=t["is_active"],
            last_used=t.get("last_used"),
        )
        for t in tokens
    ]


async def revoke_pat_token(input_data: RevokePatTokenInput) -> dict:
    repo = get_pat_token_repository()

    token_info = await repo.get_by_id(input_data.pat_id)
    if not token_info:
        raise ValueError("PAT token not found")

    user_info = get_user_info()
    if user_info and not user_info.get("is_superuser"):
        if token_info.get("user_id") != user_info.get("id"):
            raise ValueError("You can only revoke your own PAT tokens")

    success = await repo.revoke(input_data.pat_id)
    if not success:
        raise ValueError("Failed to revoke PAT token")

    return {"success": True, "message": "PAT token revoked"}


async def rotate_pat_token(input_data: RotatePatTokenInput) -> PatTokenResponse:
    repo = get_pat_token_repository()

    token_info = await repo.get_by_id(input_data.pat_id)
    if not token_info:
        raise ValueError("PAT token not found")

    user_info = get_user_info()
    if user_info and not user_info.get("is_superuser"):
        if token_info.get("user_id") != user_info.get("id"):
            raise ValueError("You can only rotate your own PAT tokens")

    result = await repo.rotate(input_data.pat_id)
    if not result:
        raise ValueError("Failed to rotate PAT token")

    new_token_id, new_token = result
    new_token_info = await repo.get_by_id(new_token_id)
    if not new_token_info:
        raise ValueError("Failed to retrieve new token info")

    return PatTokenResponse(
        id=new_token_id,
        label=token_info["label"],
        token=new_token,
        user_id=new_token_info["user_id"],
        scopes=new_token_info["scopes"],
        created_at=new_token_info["created_at"],
        expires_at=new_token_info.get("expires_at"),
        is_active=True,
        last_used=None,
    )
