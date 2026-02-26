import asyncio
import logging
import os
import sys

from shared.config import settings

from mcp_server.server import mcp

logger = logging.getLogger(__name__)


class CancelledErrorFilter(logging.Filter):
    def filter(self, record):
        if "CancelledError" in record.getMessage():
            return False
        return True


def main():
    logging.getLogger().addFilter(CancelledErrorFilter())

    db_dir = os.path.dirname(settings.db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    port = int(os.getenv("PORT", str(settings.port)))

    try:
        mcp.run(transport="streamable-http", host=settings.host, port=port)
    except asyncio.CancelledError:
        logger.info("MCP Server shutdown complete")
        sys.exit(0)


if __name__ == "__main__":
    main()
