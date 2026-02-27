from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from shared.config import settings
from shared.db.models import Scope
from shared.services import get_auth_service
from sqlalchemy.ext.asyncio import AsyncSession

security = HTTPBearer(auto_error=False)

_engine = None
_async_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        from shared.config import settings
        from shared.db.models import get_db_engine

        _engine = get_db_engine(settings.database_url)
    return _engine


def get_async_session_factory():
    global _async_session_factory
    if _async_session_factory is None:
        from sqlalchemy.ext.asyncio import async_sessionmaker

        _async_session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession]:
    async_session = get_async_session_factory()
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


class CurrentUser:
    def __init__(
        self, user_id: str, username: str, email: str, is_superuser: bool, scopes: list[Scope]
    ):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.is_superuser = is_superuser
        self.scopes = scopes


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
) -> CurrentUser:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Authentication required"},
        )

    token = credentials.credentials
    auth_service = get_auth_service()
    payload = auth_service.validate_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Invalid or expired token"},
        )

    scopes = [Scope(s) for s in payload.get("scopes", ["read"])]

    user_id = payload.get("sub")
    username = payload.get("username")
    email = payload.get("email")
    if user_id is None or username is None or email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Token missing required claims"},
        )

    return CurrentUser(
        user_id=user_id,
        username=username,
        email=email,
        is_superuser=payload.get("is_superuser", False),
        scopes=scopes,
    )


async def get_current_user_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
) -> CurrentUser | None:
    if not credentials:
        return None

    token = credentials.credentials
    auth_service = get_auth_service()
    payload = auth_service.validate_access_token(token)

    if not payload:
        return None

    scopes = [Scope(s) for s in payload.get("scopes", ["read"])]

    user_id = payload.get("sub")
    username = payload.get("username")
    email = payload.get("email")
    if user_id is None or username is None or email is None:
        return None

    return CurrentUser(
        user_id=user_id,
        username=username,
        email=email,
        is_superuser=payload.get("is_superuser", False),
        scopes=scopes,
    )


def require_admin(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Admin access required"},
        )
    return user


def require_write_scope(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if Scope.WRITE not in user.scopes and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Write scope required"},
        )
    return user


UserDep = Annotated[CurrentUser, Depends(get_current_user)]
UserOptionalDep = Annotated[CurrentUser | None, Depends(get_current_user_optional)]
AdminDep = Annotated[CurrentUser, Depends(require_admin)]
WriteDep = Annotated[CurrentUser, Depends(require_write_scope)]
DbDep = Annotated[AsyncSession, Depends(get_db)]


async def require_admin_api_key(
    x_admin_api_key: str = Header(..., alias="X-Admin-API-Key"),
) -> str:
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "ADMIN_API_KEY_NOT_CONFIGURED",
                "message": "Admin API key not configured",
            },
        )
    if x_admin_api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_ADMIN_API_KEY", "message": "Invalid admin API key"},
        )
    return x_admin_api_key


AdminApiKeyDep = Annotated[str, Depends(require_admin_api_key)]
