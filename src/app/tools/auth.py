import hashlib
from collections.abc import Callable

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware import Middleware, MiddlewareContext

from ..config import settings
from ..db import get_api_key_repository
from ..db.models import Permission, Scope
from ..services import get_auth_service
from ..services.auth_service import is_pat_token, verify_pat_token
from .context import (
    clear_all_auth,
    set_api_key_info,
    set_auth_type,
    set_pat_info,
    set_user_info,
)


def _key_to_collection(key: str) -> str:
    key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
    return f"docs_{key_hash}"


def verify_api_key(api_key: str) -> dict | None:
    if not api_key:
        return None

    if api_key == settings.admin_api_key:
        return {
            "id": "admin",
            "label": "admin",
            "collection_id": None,
            "qdrant_collection": None,
            "is_admin": True,
            "permission": Permission.READ_WRITE,
        }

    repo = get_api_key_repository()

    for valid_key in settings.api_keys_list:
        if valid_key == api_key:
            return {
                "id": f"env_{hashlib.sha256(api_key.encode()).hexdigest()[:8]}",
                "label": "env",
                "collection_id": None,
                "qdrant_collection": _key_to_collection(api_key),
                "is_admin": False,
                "permission": Permission.READ_WRITE,
            }

    return repo.validate(api_key)


def verify_jwt_token(token: str) -> dict | None:
    if not token:
        return None

    auth_service = get_auth_service()
    payload = auth_service.validate_access_token(token)

    if not payload:
        return None

    return {
        "id": payload.get("sub"),
        "username": payload.get("username"),
        "email": payload.get("email"),
        "is_superuser": payload.get("is_superuser", False),
        "scopes": [Scope(s) for s in payload.get("scopes", ["read"])],
    }


def is_jwt_token(token: str) -> bool:
    parts = token.split(".")
    return len(parts) == 3


# Public tools that don't require authentication
PUBLIC_TOOLS: set[str] = {
    "user_register_tool",
    "user_login_tool",
    "promote_to_admin_tool",
}

# MCP protocol methods that don't require authentication
PUBLIC_PROTOCOL_METHODS: set[str] = {
    "initialize",
    "notifications/initialized",
    "ping",
}


def is_public_tool(tool_name: str) -> bool:
    return tool_name in PUBLIC_TOOLS


class AuthMiddleware(Middleware):
    """Authentication middleware for FastMCP."""

    async def on_initialize(self, context: MiddlewareContext, call_next):
        """Allow initialize requests without auth."""
        return await call_next(context)

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Handle authentication for tool calls."""
        # Get tool name from the message (message IS the CallToolRequestParams)
        message = context.message
        tool_name = getattr(message, 'name', None)

        # For public tools, allow without auth
        if tool_name and tool_name in PUBLIC_TOOLS:
            return await call_next(context)

        # Check auth header for all other tools
        headers = get_http_headers(include={"authorization"})
        auth_header = headers.get("authorization", "")

        if not auth_header.startswith("Bearer "):
            raise ValueError("Missing or invalid Authorization header")

        token = auth_header[7:].strip()

        if not token:
            raise ValueError("Missing token in Authorization header")

        if is_pat_token(token):
            pat_info = verify_pat_token(token)
            if not pat_info:
                raise ValueError("Invalid or expired PAT token")
            set_pat_info(pat_info)
            set_auth_type("pat")
        elif is_jwt_token(token):
            user_info = verify_jwt_token(token)
            if not user_info:
                raise ValueError("Invalid or expired JWT token")
            set_user_info(user_info)
            set_auth_type("jwt")
        else:
            api_key_info = verify_api_key(token)
            if not api_key_info:
                raise ValueError("Invalid API key")
            set_api_key_info(api_key_info)
            set_auth_type("api_key")

        try:
            return await call_next(context)
        finally:
            clear_all_auth()

    async def on_list_tools(self, context: MiddlewareContext, call_next):
        """Allow listing tools without auth (for discovery)."""
        # NOTE: Tools are listed without auth, but calling protected tools still requires auth
        return await call_next(context)


def require_scope(required_scope: Scope) -> Callable:
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            from .context import get_api_key_info, get_pat_info, get_user_info, has_write_permission

            user_info = get_user_info()
            if user_info:
                if user_info.get("is_superuser"):
                    return await func(*args, **kwargs)
                scopes = user_info.get("scopes", [])
                if required_scope in scopes:
                    return await func(*args, **kwargs)

            pat_info = get_pat_info()
            if pat_info:
                if pat_info.get("is_superuser"):
                    return await func(*args, **kwargs)
                scopes = pat_info.get("scopes", [])
                if required_scope in scopes:
                    return await func(*args, **kwargs)

            api_key_info = get_api_key_info()
            if api_key_info:
                if api_key_info.get("is_admin"):
                    return await func(*args, **kwargs)
                if required_scope == Scope.WRITE:
                    if has_write_permission():
                        return await func(*args, **kwargs)
                elif required_scope == Scope.READ:
                    return await func(*args, **kwargs)

            raise ValueError(f"Insufficient permissions: requires '{required_scope.value}' scope")

        return wrapper
    return decorator


def require_write_permission(func: Callable) -> Callable:
    async def wrapper(*args, **kwargs):
        from .context import has_write_permission

        if not has_write_permission():
            raise ValueError("Insufficient permissions: write access required")
        return await func(*args, **kwargs)

    return wrapper


def setup_auth(mcp: FastMCP):
    mcp.add_middleware(AuthMiddleware())
