from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..db.models import Scope
from ..services import get_auth_service

security = HTTPBearer(auto_error=False)


def get_db() -> Session:
    from ..config import settings
    from ..db.models import get_db_engine

    engine = get_db_engine(settings.db_path)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


class CurrentUser:
    def __init__(self, user_id: str, username: str, email: str, is_superuser: bool, scopes: list[Scope]):
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

    return CurrentUser(
        user_id=payload.get("sub"),
        username=payload.get("username"),
        email=payload.get("email"),
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

    return CurrentUser(
        user_id=payload.get("sub"),
        username=payload.get("username"),
        email=payload.get("email"),
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
DbDep = Annotated[Session, Depends(get_db)]
