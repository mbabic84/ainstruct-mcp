import os

from nicegui import app, ui
from shared.config import settings

from web_ui.pages import (
    admin_router,
    auth_router,
    collections_router,
    dashboard_router,
    documents_router,
    tokens_router,
)


@ui.page("/")
def index_page():
    ui.navigate.to("/login")


app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(collections_router)
app.include_router(documents_router)
app.include_router(tokens_router)
app.include_router(admin_router)


def main():
    port = int(os.environ.get("PORT", settings.port))
    ui.run(
        title="AI Document Memory - Dashboard",
        port=port,
        reload=False,
        show=False,
        storage_secret=settings.jwt_secret_key,
        dark=True,
    )


if __name__ == "__main__":
    main()
