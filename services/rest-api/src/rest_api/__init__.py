"""
Entry point for running REST API as a standalone service.
"""

import os

import uvicorn
from shared.config import settings

from rest_api.app import create_app


def main():
    app = create_app()
    port = int(os.getenv("PORT", str(settings.port)))

    uvicorn.run(
        app,
        host=settings.host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
