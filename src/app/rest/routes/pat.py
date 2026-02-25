
from fastapi import APIRouter, HTTPException, status

from app.rest.deps import DbDep, UserDep
from app.rest.schemas import (
    ErrorResponse,
    MessageResponse,
    PatCreate,
    PatListItem,
    PatListResponse,
    PatResponse,
)
from app.db.models import Scope, generate_pat_token, parse_scopes, scopes_to_str
from app.db import get_pat_token_repository, get_user_repository

router = APIRouter(prefix="/auth/pat", tags=["PAT Management"])


@router.post(
    "",
    response_model=PatResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)
async def create_pat(
    body: PatCreate,
    db: DbDep,
    user: UserDep,
):
    pat_repo = get_pat_token_repository()
    user_repo = get_user_repository()

    db_user = user_repo.get_by_id(user.user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    token = generate_pat_token()

    pat_id, _ = pat_repo.create(
        label=body.label,
        user_id=user.user_id,
        scopes=scopes_to_str([Scope.READ, Scope.WRITE]),
        expires_in_days=body.expires_in_days,
    )

    pat = pat_repo.get_by_id(pat_id)

    return PatResponse(
        id=pat["id"],
        label=pat["label"],
        token=token,
        user_id=pat["user_id"],
        scopes=parse_scopes(pat["scopes"]),
        created_at=pat["created_at"],
        expires_at=pat["expires_at"],
        is_active=pat["is_active"],
        last_used=pat["last_used"],
    )


@router.get(
    "",
    response_model=PatListResponse,
)
async def list_pats(
    db: DbDep,
    user: UserDep,
):
    pat_repo = get_pat_token_repository()
    pats = pat_repo.list_by_user(user.user_id)

    tokens = [
        PatListItem(
            id=pat["id"],
            label=pat["label"],
            user_id=pat["user_id"],
            scopes=parse_scopes(pat["scopes"]),
            created_at=pat["created_at"],
            expires_at=pat["expires_at"],
            is_active=pat["is_active"],
            last_used=pat["last_used"],
        )
        for pat in pats
    ]

    return PatListResponse(tokens=tokens)


@router.delete(
    "/{pat_id}",
    response_model=MessageResponse,
    responses={
        404: {"model": ErrorResponse, "description": "PAT not found"},
    },
)
async def revoke_pat(
    pat_id: str,
    db: DbDep,
    user: UserDep,
):
    pat_repo = get_pat_token_repository()

    pat = pat_repo.get_by_id(pat_id)
    if not pat or pat["user_id"] != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PAT_NOT_FOUND", "message": "PAT not found or not owned by user"},
        )

    pat_repo.revoke(pat_id)
    return MessageResponse(message="PAT revoked successfully")


@router.post(
    "/{pat_id}/rotate",
    response_model=PatResponse,
    responses={
        404: {"model": ErrorResponse, "description": "PAT not found"},
    },
)
async def rotate_pat(
    pat_id: str,
    db: DbDep,
    user: UserDep,
):
    pat_repo = get_pat_token_repository()
    user_repo = get_user_repository()

    old_pat = pat_repo.get_by_id(pat_id)
    if not old_pat or old_pat["user_id"] != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PAT_NOT_FOUND", "message": "PAT not found or not owned by user"},
        )

    db_user = user_repo.get_by_id(user.user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    new_pat_id, new_token = pat_repo.rotate(pat_id)

    new_pat = pat_repo.get_by_id(new_pat_id)

    return PatResponse(
        id=new_pat["id"],
        label=new_pat["label"],
        token=new_token,
        user_id=new_pat["user_id"],
        scopes=parse_scopes(new_pat["scopes"]),
        created_at=new_pat["created_at"],
        expires_at=new_pat["expires_at"],
        is_active=new_pat["is_active"],
        last_used=new_pat["last_used"],
    )
