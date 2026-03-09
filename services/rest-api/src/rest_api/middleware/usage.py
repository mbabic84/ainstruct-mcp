import logging
from collections.abc import Callable

from fastapi import Request, Response
from shared.db import get_usage_repository
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

TRACKED_PREFIXES = [
    "/api/v1/documents",
    "/api/v1/collections",
]

SKIP_PATHS = [
    "/health",
    "/api/v1/auth",
    "/api/v1/admin",
    "/api/v1/pat",
    "/api/v1/cat",
]


def should_track_path(path: str) -> bool:
    for skip_path in SKIP_PATHS:
        if path.startswith(skip_path):
            return False

    for prefix in TRACKED_PREFIXES:
        if path.startswith(prefix):
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

        if not should_track_path(path):
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
