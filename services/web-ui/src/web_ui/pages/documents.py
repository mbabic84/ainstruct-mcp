from nicegui import APIRouter, ui
from shared.config import settings

from web_ui.auth import load_tokens_from_storage, require_auth
from web_ui.components import (
    add_table_action_buttons,
    create_sort_handler,
    create_table_pagination,
    make_columns_sortable,
    render_page,
)
from web_ui.utils import format_date, handle_api_error

router = APIRouter(prefix="")


@router.page("/documents")
async def documents_page(
    collection_id: str | None = None, sort_by: str = "", sort_desc: bool = False
):
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
                    columns = make_columns_sortable(
                        [
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
                    )

                    pagination = create_table_pagination(
                        sort_by, sort_desc, settings.web_records_per_page
                    )

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

                    def handle_view(e):
                        row = e.args[1]
                        doc_id = row["id"]
                        if collection_id and collection_id != "__all__":
                            ui.navigate.to(f"/viewer/{doc_id}?collection_id={collection_id}")
                        else:
                            ui.navigate.to(f"/viewer/{doc_id}")

                    async def _delete_document(item_id: str):
                        response = api_client.delete_document(item_id)
                        if handle_api_error(response, "Failed to delete document"):
                            ui.notify("Document deleted")
                            ui.navigate.reload()

                    def handle_delete(item):
                        item_id = item["id"]
                        return _delete_document(item_id)

                    table = (
                        ui.table(columns=columns, rows=rows, row_key="id", pagination=pagination)
                        .classes("w-full")
                        .on("rowClick", handle_view)
                        .on(
                            "update:pagination",
                            create_sort_handler(
                                "/documents",
                                lambda: {"collection_id": selected_collection.value},
                                sort_by,
                                sort_desc,
                            ),
                        )
                    )
                    add_table_action_buttons(
                        table,
                        "actions",
                        [
                            {
                                "icon": "delete",
                                "color": "negative",
                                "on_click": handle_delete,
                                "label_field": "title",
                                "confirm": True,
                                "confirm_message": "Deleting a document removes it permanently. This action cannot be undone.",
                                "confirm_label": "Delete",
                            }
                        ],
                    )
            else:
                ui.label("No documents yet.")
        else:
            ui.notify(f"Error loading documents: {response.text}", type="negative")

    render_page(content)
