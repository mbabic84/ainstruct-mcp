from nicegui import APIRouter, ui

from web_ui.auth import get_user, load_tokens_from_storage, require_auth
from web_ui.components import render_page

router = APIRouter(prefix="")


@router.page("/dashboard")
async def dashboard_page():
    await load_tokens_from_storage()

    if not require_auth():
        return

    def content():
        from web_ui.auth import get_api_client

        api_client = get_api_client()

        user = get_user()
        if user:
            ui.label(f"Welcome, {user.get('username', 'User')}!").classes("text-2xl font-bold")
        else:
            ui.label("Welcome!").classes("text-2xl font-bold")

        with ui.row().classes("w-full gap-4 mt-4"):
            response = api_client.list_collections()
            collections = (
                response.json().get("collections", []) if response.status_code == 200 else []
            )
            with ui.card().classes("flex-1"):
                ui.label("Collections").classes("text-lg font-bold")
                ui.label(str(len(collections))).classes("text-4xl")

            response = api_client.list_documents()
            docs_data = response.json() if response.status_code == 200 else {"total": 0}
            with ui.card().classes("flex-1"):
                ui.label("Documents").classes("text-lg font-bold")
                ui.label(str(docs_data.get("total", 0))).classes("text-4xl")

            response = api_client.list_pats()
            pats = response.json().get("tokens", []) if response.status_code == 200 else []
            active_pats = [p for p in pats if p.get("is_active", True)]
            with ui.card().classes("flex-1"):
                ui.label("PATs").classes("text-lg font-bold")
                ui.label(str(len(active_pats))).classes("text-4xl")

            response = api_client.list_cats()
            cats = response.json().get("tokens", []) if response.status_code == 200 else []
            active_cats = [c for c in cats if c.get("is_active", True)]
            with ui.card().classes("flex-1"):
                ui.label("CATs").classes("text-lg font-bold")
                ui.label(str(len(active_cats))).classes("text-4xl")

    render_page(content)
