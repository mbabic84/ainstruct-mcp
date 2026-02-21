import os

from .config import settings
from .mcp.server import mcp

if __name__ == "__main__":
    db_dir = os.path.dirname(settings.db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    mcp.run(transport="http", host=settings.host, port=settings.port)
