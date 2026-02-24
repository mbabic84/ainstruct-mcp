import asyncio
import logging
import os
import sys

from .config import settings
from .mcp.server import mcp

logger = logging.getLogger(__name__)


class CancelledErrorFilter(logging.Filter):
    def filter(self, record):
        if "CancelledError" in record.getMessage():
            return False
        return True


if __name__ == "__main__":
    logging.getLogger().addFilter(CancelledErrorFilter())

    db_dir = os.path.dirname(settings.db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    try:
        mcp.run(transport="streamable-http", host=settings.host, port=settings.port)
    except asyncio.CancelledError:
        logger.info("Server shutdown complete")
        sys.exit(0)
