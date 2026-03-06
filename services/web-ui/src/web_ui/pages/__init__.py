from web_ui.pages.admin import router as admin_router
from web_ui.pages.auth import router as auth_router
from web_ui.pages.collections import router as collections_router
from web_ui.pages.dashboard import router as dashboard_router
from web_ui.pages.documents import router as documents_router
from web_ui.pages.editor import router as editor_router
from web_ui.pages.tokens import router as tokens_router
from web_ui.pages.viewer import router as viewer_router

__all__ = [
    "auth_router",
    "dashboard_router",
    "collections_router",
    "documents_router",
    "tokens_router",
    "admin_router",
    "viewer_router",
    "editor_router",
]
