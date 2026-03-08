import json

from nicegui import APIRouter, ui

from web_ui.auth import load_tokens_from_storage, require_auth
from web_ui.components import render_page
from web_ui.utils import handle_api_error

router = APIRouter(prefix="")


@router.page("/viewer/{doc_id}")
async def viewer_page(doc_id: str, collection_id: str | None = None):
    await load_tokens_from_storage()

    if not require_auth():
        return

    def content():
        from web_ui.auth import get_api_client

        api_client = get_api_client()

        response = api_client.get_document(doc_id)
        if not handle_api_error(response, "Failed to load document"):
            ui.navigate.to("/documents")
            return

        doc = response.json()

        with ui.row().classes("w-full items-center justify-between mb-4"):
            with ui.row().classes("items-center gap-2"):
                back_url = (
                    f"/documents?collection_id={collection_id}"
                    if collection_id and collection_id != "__all__"
                    else "/documents"
                )
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to(back_url)).props(
                    "flat round"
                )
                ui.icon("description", size="md")
                ui.label(doc["title"]).classes("text-xl font-bold")

            with ui.row().classes("items-center gap-2"):
                ui.button(
                    icon="edit",
                    on_click=lambda: ui.navigate.to(f"/editor/{doc_id}"),
                ).props("flat round")
                ui.label(doc["document_type"]).classes("text-sm text-grey-7")

        ui.separator()

        content = doc.get("content", "")
        doc_type = doc["document_type"]

        if doc_type == "markdown":
            ui.markdown(content).classes("w-full")
        elif doc_type == "json":
            try:
                data = json.loads(content)
                ui.json_editor({"content": {"json": data}}, properties={"readOnly": True}).classes(
                    "w-full"
                )
            except Exception:
                ui.code(content, language="json").classes("w-full font-mono")
        elif doc_type in ["yaml", "xml", "html", "python", "javascript"]:
            ui.code(content, language=doc_type).classes("w-full font-mono")
        else:
            ui.pre(content).classes("whitespace-pre-wrap w-full font-mono text-sm")

    render_page(content)
