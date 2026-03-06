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

ui.add_css(
    """
body, html { margin: 0; padding: 0; }
.q-page-container { margin: 0 !important; padding: 0 !important; }
.q-layout { margin: 0 !important; }
""",
    shared=True,
)

js_path = os.path.join(os.path.dirname(__file__), "static", "js", "token_refresh.js")
with open(js_path) as f:
    token_refresh_js = f.read()

ui.add_head_html(
    f"<script>{token_refresh_js}</script>",
    shared=True,
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
        storage_secret="ainstruct-mcp-secret-key",
        dark=True,
    )


if __name__ == "__main__":
    main()
