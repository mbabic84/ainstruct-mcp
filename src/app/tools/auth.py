import hashlib
from typing import Optional
from fastmcp import FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.dependencies import get_http_headers

from ..config import settings
from ..db import get_api_key_repository
from .context import set_api_key_info, clear_api_key_info


def _key_to_collection(key: str) -> str:
    key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
    return f"docs_{key_hash}"


def verify_api_key(api_key: str) -> Optional[dict]:
    if not api_key:
        return None
    
    if api_key == settings.admin_api_key:
        return {
            "id": "admin",
            "label": "admin",
            "qdrant_collection": None,
            "is_admin": True,
        }
    
    repo = get_api_key_repository()
    
    for valid_key in settings.api_keys_list:
        if valid_key == api_key:
            return {
                "id": f"env_{hashlib.sha256(api_key.encode()).hexdigest()[:8]}",
                "label": "env",
                "qdrant_collection": _key_to_collection(api_key),
                "is_admin": False,
            }
    
    return repo.validate(api_key)


class AuthMiddleware(Middleware):
    async def on_request(self, context: MiddlewareContext, call_next):
        headers = get_http_headers()
        auth_header = headers.get("authorization", "")
        
        if not auth_header.startswith("Bearer "):
            raise ValueError("Missing or invalid Authorization header")
        
        api_key = auth_header[7:].strip()
        api_key_info = verify_api_key(api_key)
        
        if not api_key_info:
            raise ValueError("Invalid API key")
        
        set_api_key_info(api_key_info)
        
        try:
            return await call_next(context)
        finally:
            clear_api_key_info()


def setup_auth(mcp: FastMCP):
    mcp.add_middleware(AuthMiddleware())
