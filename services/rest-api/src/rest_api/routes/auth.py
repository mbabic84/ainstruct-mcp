from fastapi import APIRouter, HTTPException, status
from shared.db import get_user_repository
from shared.services.auth_service import AuthService

from rest_api.deps import DbDep, UserDep
from rest_api.schemas import (
    ErrorResponse,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Username or email already exists"},
    },
)
async def register(
    body: UserCreate,
    db: DbDep,
):

    user_repo = get_user_repository()
    auth_service = AuthService()

    existing_user = await user_repo.get_by_username(body.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "USERNAME_EXISTS", "message": "Username already registered"},
        )

    existing_email = await user_repo.get_by_email(body.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMAIL_EXISTS", "message": "Email already registered"},
        )

    password_hash = auth_service.hash_password(body.password)
    user = await user_repo.create(
        username=body.username,
        email=body.email,
        password_hash=password_hash,
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        403: {"model": ErrorResponse, "description": "Account disabled"},
    },
)
async def login(
    body: UserLogin,
    db: DbDep,
):

    user_repo = get_user_repository()
    auth_service = AuthService()

    user = await user_repo.get_by_username(body.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Wrong username or password"},
        )

    if not auth_service.verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Wrong username or password"},
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ACCOUNT_DISABLED", "message": "User account is inactive"},
        )

    scopes = ["read", "write"]
    if user["is_superuser"]:
        scopes.append("admin")

    access_token = auth_service.create_access_token(
        user_id=user["id"],
        username=user["username"],
        email=user["email"],
        is_superuser=user["is_superuser"],
        scopes=[s for s in scopes],
    )
    refresh_token = auth_service.create_refresh_token(user_id=user["id"])

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=auth_service.get_access_token_expiry(),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid refresh token"},
    },
)
async def refresh(
    body: RefreshRequest,
    db: DbDep,
):

    auth_service = AuthService()
    user_repo = get_user_repository()

    payload = auth_service.validate_refresh_token(body.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_REFRESH_TOKEN", "message": "Refresh token invalid or expired"},
        )

    user = await user_repo.get_by_id(payload.get("sub"))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_REFRESH_TOKEN", "message": "User not found or inactive"},
        )

    scopes = ["read", "write"]
    if user.is_superuser:
        scopes.append("admin")

    access_token = auth_service.create_access_token(
        user_id=user.id,
        username=user.username,
        email=user.email,
        is_superuser=user.is_superuser,
        scopes=[s for s in scopes],
    )
    refresh_token = auth_service.create_refresh_token(user_id=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=auth_service.get_access_token_expiry(),
    )


@router.get(
    "/profile",
    response_model=UserResponse,
)
async def get_profile(
    user: UserDep,
):
    user_repo = get_user_repository()
    db_user = await user_repo.get_by_id(user.user_id)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        is_active=db_user.is_active,
        is_superuser=db_user.is_superuser,
        created_at=db_user.created_at,
    )
