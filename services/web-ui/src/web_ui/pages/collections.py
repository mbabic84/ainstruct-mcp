from nicegui import APIRouter, ui

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


@router.page("/collections")
async def collections_page(sort_by: str = "", sort_desc: bool = False):
    await load_tokens_from_storage()

    if not require_auth():
        return

    def content():
        from web_ui.auth import get_api_client

        api_client = get_api_client()

        ui.label("Collections").classes("text-2xl font-bold")

        with ui.row().classes("w-full gap-2 mb-4"):
            new_name_input = ui.input("New Collection Name").classes("flex-1")

            def create_collection():
                if new_name_input.value:
                    response = api_client.create_collection(new_name_input.value)
                    if handle_api_error(response, "Failed to create collection"):
                        ui.notify("Collection created")
                        new_name_input.set_value("")
                        ui.navigate.reload()

            ui.button("Create", on_click=create_collection).props("color=primary")

        response = api_client.list_collections()
        if response.status_code == 200:
            collections = response.json().get("collections", [])
            if collections:
                with ui.card().classes("w-full"):
                    columns = make_columns_sortable(
                        [
                            {"name": "name", "label": "Name", "field": "name", "align": "left"},
                            {
                                "name": "document_count",
                                "label": "Documents",
                                "field": "document_count",
                                "align": "left",
                            },
                            {
                                "name": "cat_count",
                                "label": "CATs",
                                "field": "cat_count",
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

                    pagination = create_table_pagination(sort_by, sort_desc)

                    rows = []
                    for c in collections:
                        rows.append(
                            {
                                "name": c["name"],
                                "document_count": c.get("document_count", 0),
                                "cat_count": c.get("cat_count", 0),
                                "created_at": format_date(c.get("created_at")),
                                "id": c["collection_id"],
                            }
                        )

                    def handle_view(e):
                        collection_id = e.args[1]["id"]
                        ui.navigate.to(f"/documents?collection_id={collection_id}")

                    async def _delete_collection(item_id: str):
                        response = api_client.delete_collection(item_id)
                        if handle_api_error(response, "Failed to delete collection"):
                            ui.notify("Collection deleted")
                            ui.navigate.reload()

                    def handle_delete(item):
                        item_id = item["id"]
                        return _delete_collection(item_id)

                    table = (
                        ui.table(columns=columns, rows=rows, row_key="id", pagination=pagination)
                        .classes("w-full")
                        .on("rowClick", handle_view)
                        .on(
                            "update:pagination",
                            create_sort_handler("/collections", None, sort_by, sort_desc),
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
                                "label_field": "name",
                                "confirm": True,
                                "confirm_message": "Deleting a collection will remove all documents within it. This action cannot be undone.",
                                "confirm_label": "Delete",
                            }
                        ],
                    )
            else:
                ui.label("No collections yet. Create one above!")
        else:
            ui.notify(f"Error loading collections: {response.text}", type="negative")

    render_page(content)
