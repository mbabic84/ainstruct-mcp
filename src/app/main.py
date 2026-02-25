import asyncio
import logging
import os
import sys
import threading

from .config import settings
from .mcp.server import mcp

logger = logging.getLogger(__name__)


class CancelledErrorFilter(logging.Filter):
    def filter(self, record):
        if "CancelledError" in record.getMessage():
            return False
        return True


def run_mcp():
    logging.getLogger().addFilter(CancelledErrorFilter())

    db_dir = os.path.dirname(settings.db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    try:
        mcp.run(transport="streamable-http", host=settings.host, port=settings.port)
    except asyncio.CancelledError:
        logger.info("MCP Server shutdown complete")
        sys.exit(0)


def run_rest():
    import uvicorn

    from .rest.app import create_app

    app = create_app()
    rest_port = settings.port + 1

    uvicorn.run(
        app,
        host=settings.host,
        port=rest_port,
        log_level="info",
    )


if __name__ == "__main__":
    logging.getLogger().addFilter(CancelledErrorFilter())

    db_dir = os.path.dirname(settings.db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    rest_port = settings.port + 1

    print(f"Starting MCP server on port {settings.port}...")
    print(f"Starting REST API on port {rest_port}...")

    rest_thread = threading.Thread(target=run_rest, daemon=True)
    rest_thread.start()

    try:
        mcp.run(transport="streamable-http", host=settings.host, port=settings.port)
    except asyncio.CancelledError:
        logger.info("Server shutdown complete")
        sys.exit(0)
