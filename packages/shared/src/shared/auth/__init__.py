from contextvars import ContextVar
from typing import Any

from shared.db.models import Permission, Scope

_auth_context: ContextVar[dict[str, Any] | None] = ContextVar("auth_context", default=None)


def set_auth_context(context: dict[str, Any]) -> None:
    _auth_context.set(context)


def get_auth_context() -> dict[str, Any] | None:
    return _auth_context.get()


def clear_auth_context() -> None:
    _auth_context.set(None)


def has_write_permission() -> bool:
    ctx = get_auth_context()
    if not ctx:
        return False

    if ctx.get("is_superuser"):
        return True

    permission = ctx.get("permission")
    if permission == Permission.READ_WRITE:
        return True

    scopes = ctx.get("scopes", [])
    return Scope.WRITE in scopes
