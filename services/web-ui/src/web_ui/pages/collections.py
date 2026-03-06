from datetime import datetime

from nicegui import APIRouter, ui

from web_ui.auth import load_tokens_from_storage, require_auth
from web_ui.components import render_page

router = APIRouter(prefix="")


@router.page("/collections")
async def collections_page():
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
                    if response.status_code == 201:
                        ui.notify("Collection created")
                        new_name_input.set_value("")
                        ui.navigate.reload()
                    else:
                        ui.notify(f"Error: {response.text}", type="negative")

            ui.button("Create", on_click=create_collection).props("color=primary")

        response = api_client.list_collections()
        if response.status_code == 200:
            collections = response.json().get("collections", [])
            if collections:
                with ui.card().classes("w-full"):
                    columns = [
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
                    rows = []
                    for c in collections:
                        rows.append(
                            {
                                "name": c["name"],
                                "document_count": c.get("document_count", 0),
                                "cat_count": c.get("cat_count", 0),
                                "created_at": datetime.fromisoformat(
                                    c["created_at"].replace("Z", "+00:00")
                                ).strftime("%Y-%m-%d"),
                                "id": c["collection_id"],
                            }
                        )

                    def handle_view(e):
                        collection_id = e.args[1]["id"]
                        ui.navigate.to(f"/documents?collection_id={collection_id}")

                    def handle_delete(e):
                        collection_id = e.args["id"]
                        collection_name = e.args.get("name", "this collection")
                        with ui.dialog() as dialog, ui.card():
                            ui.label(f"Delete '{collection_name}'?").classes("text-lg font-bold")
                            ui.label("This action cannot be undone.").classes("text-sm text-grey-7")
                            with ui.row().classes("w-full justify-end gap-2"):
                                ui.button("Cancel", on_click=dialog.close).props("flat")
                                ui.button(
                                    "Delete",
                                    on_click=lambda: [dialog.close(), _do_delete(collection_id)],
                                ).props("color=negative")

                        def _do_delete(collection_id):
                            response = api_client.delete_collection(collection_id)
                            if response.status_code == 200:
                                ui.notify("Collection deleted")
                                ui.navigate.reload()
                            else:
                                ui.notify(f"Error: {response.text}", type="negative")

                        dialog.open()

                    table = (
                        ui.table(columns=columns, rows=rows, row_key="id")
                        .classes("w-full")
                        .on("rowClick", handle_view)
                        .on("row-delete", handle_delete)
                    )
                    table.add_slot(
                        "body-cell-actions",
                        """
                        <q-td :props="props">
                            <q-btn flat round color="negative" icon="delete" @click.stop="$parent.$emit('row-delete', props.row)" />
                        </q-td>
                    """,
                    )
            else:
                ui.label("No collections yet. Create one above!")
        else:
            ui.notify(f"Error loading collections: {response.text}", type="negative")

    render_page(content)
