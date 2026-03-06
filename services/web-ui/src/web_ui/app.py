import os

from nicegui import app, ui
from shared.config import settings

from web_ui.pages import (  # noqa: E402
    admin_router,
    auth_router,
    collections_router,
    dashboard_router,
    documents_router,
    editor_router,
    tokens_router,
    viewer_router,
)

# VS Code Dark color palette
app.colors(
    primary="#007acc",  # Blue (VS Code blue)
    secondary="#4ec9b0",  # Teal
    accent="#ce9178",  # Orange
    dark="#1e1e1e",  # Background
    dark_page="#1e1e1e",
)

# Custom CSS for full VS Code Dark theme
ui.add_css(
    """
:root {
    --q-primary: #007acc;
    --q-secondary: #4ec9b0;
    --q-accent: #ce9178;
    --q-dark: #1e1e1e;
    --q-dark-page: #1e1e1e;
}
body {
    background-color: #1e1e1e;
    color: #d4d4d4;
}
.q-card {
    background-color: #252526;
    color: #d4d4d4;
}
.q-btn {
    background-color: #3c3c3c;
    color: #cccccc;
}
.q-input .q-field__control {
    background-color: #3c3c3c;
}
.q-table {
    background-color: #1e1e1e;
}
.q-table th, .q-table td {
    color: #cccccc;
}
.q-dialog__backdrop {
    background-color: rgba(0, 0, 0, 0.5);
}
.q-menu {
    background-color: #252526;
}
""",
    shared=True,
)


app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(collections_router)
app.include_router(documents_router)
app.include_router(tokens_router)
app.include_router(admin_router)
app.include_router(viewer_router)
app.include_router(editor_router)


@ui.page("/")
def index():
    ui.navigate.to("/login")


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
