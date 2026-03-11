import logging
from collections.abc import Callable

from fastapi import Request, Response
from shared.db import get_usage_repository
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


def should_track_path(path: str, method: str) -> bool:
    # Skip admin, auth, PAT, CAT endpoints
    skip_paths = [
        "/health",
        "/api/v1/auth",
        "/api/v1/admin",
        "/api/v1/pat",
        "/api/v1/cat",
    ]
    for skip_path in skip_paths:
        if path.startswith(skip_path):
            return False

    # Only track endpoints that require embedding
    # POST /api/v1/documents (store)
    # PATCH /api/v1/documents/{id} (update)
    # POST /api/v1/documents/search (search)
    if path.startswith("/api/v1/documents"):
        if path == "/api/v1/documents" and method == "POST":
            return True
        if path.startswith("/api/v1/documents/") and method == "PATCH":
            return True
        if path == "/api/v1/documents/search" and method == "POST":
            return True

    return False


def extract_user_id_from_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header[7:].strip()
    if not token:
        return None

    try:
        from shared.services import get_auth_service

        auth_service = get_auth_service()
        payload = auth_service.validate_access_token(token)

        if payload and payload.get("type") == "access":
            return payload.get("sub")
    except Exception as e:
        logger.warning(f"Failed to extract user_id from token: {e}")

    return None


class UsageMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        method = request.method

        if not should_track_path(path, method):
            return await call_next(request)

        user_id = extract_user_id_from_token(request)

        if not user_id:
            return await call_next(request)

        try:
            usage_repo = get_usage_repository()
            await usage_repo.increment(user_id, "api")
        except Exception as e:
            logger.warning(f"Failed to track usage: {e}")

        return await call_next(request)
