import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from rest_api.middleware.usage import UsageMiddleware
from rest_api.routes import admin, auth, cat, collections, documents, pat

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("REST API starting up...")
    yield
    logger.info("REST API shutting down...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="ainstruct API",
        description="REST API for ainstruct - Document management with semantic search",
        version="1.0.0",
        lifespan=lifespan,
    )

    if app.openapi_schema:
        app.openapi_schema["components"]["securitySchemes"] = {
            "HTTPBearer": {"type": "http", "scheme": "bearer"},
            "AdminApiKey": {"type": "apiKey", "in": "header", "name": "X-Admin-Api-Key"},
        }

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(UsageMiddleware)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                }
            },
        )

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(pat.router, prefix="/api/v1")
    app.include_router(cat.router, prefix="/api/v1")
    app.include_router(collections.router, prefix="/api/v1")
    app.include_router(documents.router, prefix="/api/v1")
    app.include_router(admin.router, prefix="/api/v1")

    @app.get("/health", include_in_schema=False)
    async def health():
        return {"status": "healthy"}

    return app


app = create_app()
