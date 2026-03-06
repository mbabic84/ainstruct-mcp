from nicegui import APIRouter, ui

from web_ui.auth import load_tokens_from_storage, require_auth
from web_ui.components import render_page
from web_ui.components.common import add_table_actions, confirm_action
from web_ui.utils import format_date, handle_api_error

router = APIRouter(prefix="")


@router.page("/documents")
async def documents_page(collection_id: str | None = None):
    await load_tokens_from_storage()

    if not require_auth():
        return

    def content():
        from web_ui.auth import get_api_client

        api_client = get_api_client()

        ui.label("Documents").classes("text-2xl font-bold")

        collection_response = api_client.list_collections()
        collections = (
            collection_response.json().get("collections", [])
            if collection_response.status_code == 200
            else []
        )
        collection_options = {"__all__": "All Collections"}
        collection_options.update({c["collection_id"]: c["name"] for c in collections})

        initial_value = collection_id if collection_id else "__all__"

        selected_collection = ui.select(
            label="Filter by Collection",
            options=collection_options,
            value=initial_value,
        ).classes("w-full mb-4")
        selected_collection.on_value_change(
            lambda e: ui.navigate.to(f"/documents?collection_id={e.value}")
        )

        params = {}
        if selected_collection.value and selected_collection.value != "__all__":
            params["collection_id"] = selected_collection.value

        response = api_client.list_documents(**params)
        if response.status_code == 200:
            docs_data = response.json()
            documents = docs_data.get("documents", [])
            if documents:
                with ui.card().classes("w-full"):
                    columns = [
                        {"name": "title", "label": "Title", "field": "title", "align": "left"},
                        {
                            "name": "collection_name",
                            "label": "Collection",
                            "field": "collection_name",
                            "align": "left",
                        },
                        {
                            "name": "document_type",
                            "label": "Type",
                            "field": "document_type",
                            "align": "left",
                        },
                        {
                            "name": "created_at",
                            "label": "Created",
                            "field": "created_at",
                            "align": "left",
                        },
                        {
                            "name": "actions",
                            "label": "Actions",
                            "field": "actions",
                            "align": "center",
                        },
                    ]
                    rows = []
                    for d in documents:
                        rows.append(
                            {
                                "title": d["title"],
                                "collection_name": d.get("collection_name", ""),
                                "document_type": d["document_type"],
                                "created_at": format_date(d.get("created_at")),
                                "id": d["document_id"],
                                "content": d.get("content", ""),
                            }
                        )

                    def handle_edit(e):
                        doc_id = e.args[1]["id"]
                        ui.navigate.to(f"/documents/{doc_id}/edit")

                    def handle_delete(e):
                        doc_id = e.args[0]["id"]
                        doc_title = e.args[0].get("title", "this document")

                        async def do_delete():
                            response = api_client.delete_document(doc_id)
                            if handle_api_error(response, "Failed to delete document"):
                                ui.notify("Document deleted")
                                ui.navigate.reload()

                        confirm_action(
                            f"Delete '{doc_title}'?",
                            "This action cannot be undone.",
                            do_delete,
                            "Cancel",
                            "Delete",
                        )

                    table = (
                        ui.table(columns=columns, rows=rows, row_key="id")
                        .classes("w-full")
                        .on("rowClick", handle_edit)
                        .on("row-delete", handle_delete)
                    )
                    add_table_actions(
                        table,
                        [{"color": "negative", "icon": "delete", "emit": "row-delete"}],
                    )
            else:
                ui.label("No documents yet.")
        else:
            ui.notify(f"Error loading documents: {response.text}", type="negative")

    render_page(content)


@router.page("/documents/{doc_id}/edit")
async def document_edit_page(doc_id: str):
    await load_tokens_from_storage()

    if not require_auth():
        return

    def content():
        from web_ui.auth import get_api_client

        api_client = get_api_client()

        response = api_client.get_document(doc_id)
        if response.status_code != 200:
            ui.notify("Document not found", type="negative")
            ui.navigate.to("/documents")
            return

        doc = response.json()

        title_input = ui.input("Title", value=doc["title"]).classes("w-full")
        doc_type_input = ui.select(
            options=["markdown", "text", "html"],
            label="Document Type",
            value=doc["document_type"],
        ).classes("w-full")
        content_input = ui.textarea("Content", value=doc.get("content", "")).classes("w-full h-64")

        with ui.row().classes("gap-2 mt-4"):

            def save_document():
                update_data = {
                    "title": title_input.value,
                    "document_type": doc_type_input.value,
                    "content": content_input.value,
                }
                response = api_client.update_document(doc_id, **update_data)
                if handle_api_error(response, "Failed to save document"):
                    ui.notify("Document saved")
                    ui.navigate.to("/documents")

            ui.button("Save", on_click=save_document).props("color=primary")
            ui.button("Cancel", on_click=lambda: ui.navigate.to("/documents")).props("flat")

    render_page(content)
