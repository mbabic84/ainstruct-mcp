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


# Auth type constants
class AuthLevel:
    NONE = "none"           # No auth required (public)
    JWT_OR_PAT = "jwt_or_pat"  # JWT or PAT token required
    API_KEY = "api_key"     # API key OR JWT/PAT (documents)
    ADMIN = "admin"         # JWT or PAT + admin scope


# Public tools that don't require authentication
PUBLIC_TOOLS: set[str] = {
    "user_register_tool",
    "user_login_tool",
    "user_refresh_tool",
}

# Tools requiring JWT or PAT authentication (user-level access)
USER_TOOLS: set[str] = {
    "user_profile_tool",
}

# Tools requiring JWT or PAT authentication (collection management)
COLLECTION_TOOLS: set[str] = {
    "create_collection_tool",
    "list_collections_tool",
    "get_collection_tool",
    "delete_collection_tool",
    "rename_collection_tool",
}

# Tools requiring JWT or PAT authentication (keys and PATs)
KEY_PAT_TOOLS: set[str] = {
    "create_api_key_tool",
    "list_api_keys_tool",
    "revoke_api_key_tool",
    "rotate_api_key_tool",
    "create_pat_token_tool",
    "list_pat_tokens_tool",
    "revoke_pat_token_tool",
    "rotate_pat_token_tool",
}

# Tools accepting API key or JWT/PAT (document operations)
DOCUMENT_TOOLS: set[str] = {
    "store_document_tool",
    "search_documents_tool",
    "get_document_tool",
    "list_documents_tool",
    "delete_document_tool",
    "update_document_tool",
}

# Tools requiring admin scope (JWT or PAT with admin)
ADMIN_TOOLS: set[str] = {
    "list_users_tool",
    "search_users_tool",
    "get_user_tool",
    "update_user_tool",
    "delete_user_tool",
}


def get_tool_auth_level(tool_name: str) -> str:
    """Get the required auth level for a tool.

    Unknown tools default to ADMIN level for security - this ensures
    new tools are not accidentally exposed without explicit authorization.
    """
    if tool_name in PUBLIC_TOOLS:
        return AuthLevel.NONE
    if tool_name in ADMIN_TOOLS:
        return AuthLevel.ADMIN
    if tool_name in DOCUMENT_TOOLS:
        return AuthLevel.API_KEY
    if tool_name in KEY_PAT_TOOLS:
        return AuthLevel.JWT_OR_PAT
    if tool_name in COLLECTION_TOOLS:
        return AuthLevel.JWT_OR_PAT
    if tool_name in USER_TOOLS:
        return AuthLevel.JWT_OR_PAT
    # Default to ADMIN for unknown tools - fail closed for security
    return AuthLevel.ADMIN

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

        # Check auth header for all other tools - try multiple approaches for compatibility
        auth_header = None

        # Approach 1: Try get_http_headers (works with SSE)
        try:
            headers = get_http_headers(include={"authorization"})
            auth_header = headers.get("authorization")
        except Exception:
            pass

        # Approach 2: Try context.fastmcp_context (works with Streamable HTTP)
        if not auth_header:
            try:
                fastmcp_ctx = getattr(context, 'fastmcp_context', None)
                if fastmcp_ctx and hasattr(fastmcp_ctx, 'request_context'):
                    request_ctx = fastmcp_ctx.request_context
                    if request_ctx and hasattr(request_ctx, 'request'):
                        auth_header = request_ctx.request.headers.get("Authorization")
            except Exception:
                pass

        if not auth_header or not auth_header.startswith("Bearer "):
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
        """Filter tools based on authentication context."""
        result = await call_next(context)

        # If result is not a list of tools, return as-is
        if not isinstance(result, list):
            return result

        # Extract auth from headers - try multiple approaches for compatibility
        auth_header = None

        # Approach 1: Try get_http_headers (works with SSE)
        try:
            headers = get_http_headers(include={"authorization"})
            auth_header = headers.get("authorization") if headers else None
        except Exception:
            pass

        # Approach 2: Try context.fastmcp_context (works with Streamable HTTP)
        if not auth_header:
            try:
                fastmcp_ctx = getattr(context, 'fastmcp_context', None)
                if fastmcp_ctx and hasattr(fastmcp_ctx, 'request_context'):
                    request_ctx = fastmcp_ctx.request_context
                    if request_ctx and hasattr(request_ctx, 'request'):
                        auth_header = request_ctx.request.headers.get("Authorization")
            except Exception:
                pass

        # If no auth header, only return public tools
        if not auth_header or not auth_header.startswith("Bearer "):
            return [tool for tool in result if get_tool_auth_level(tool.name) == AuthLevel.NONE]

        token = auth_header[7:].strip()
        if not token:
            return [tool for tool in result if get_tool_auth_level(tool.name) == AuthLevel.NONE]

        auth_level = AuthLevel.NONE
        user_info = None
        pat_info = None
        api_key_info = None

        if is_pat_token(token):
            pat_info = verify_pat_token(token)
            if pat_info:
                auth_level = AuthLevel.JWT_OR_PAT
        elif is_jwt_token(token):
            user_info = verify_jwt_token(token)
            if user_info:
                auth_level = AuthLevel.JWT_OR_PAT
        else:
            api_key_info = verify_api_key(token)
            if api_key_info:
                auth_level = AuthLevel.API_KEY

        # Service admin (admin_api_key): only allow update_user_tool
        if api_key_info and api_key_info.get("is_admin"):
            return [tool for tool in result if tool.name == "update_user_tool"]

        def can_access_tool(tool) -> bool:
            required = get_tool_auth_level(tool.name)

            # Public tools always accessible
            if required == AuthLevel.NONE:
                return True

            # If no valid auth, can't access
            if auth_level == AuthLevel.NONE:
                return False

            # Admin tools require admin scope
            if required == AuthLevel.ADMIN:
                if user_info and user_info.get("is_superuser"):
                    return True
                if pat_info and pat_info.get("is_superuser"):
                    return True
                return False

            # Document tools: API key or JWT/PAT works
            if required == AuthLevel.API_KEY:
                return True

            # JWT/PAT tools: require valid JWT or PAT
            if required == AuthLevel.JWT_OR_PAT:
                return bool(user_info or pat_info)

            return False

        return [tool for tool in result if can_access_tool(tool)]


def require_scope(required_scope: Scope) -> Callable:
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            from .context import get_api_key_info, get_pat_info, get_user_info, has_write_permission, is_authenticated

            if not is_authenticated():
                raise ValueError("Not authenticated")

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
