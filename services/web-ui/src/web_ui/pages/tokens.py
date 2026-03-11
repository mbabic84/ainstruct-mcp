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
from web_ui.components.common import mcp_token_dialog
from web_ui.utils import format_time_remaining, handle_api_error

router = APIRouter(prefix="")


@router.page("/tokens")
async def tokens_page(tab: str = "pat", sort_by: str = "", sort_desc: bool = False):
    await load_tokens_from_storage()

    if not require_auth():
        return

    def content():
        from web_ui.auth import get_api_client

        api_client = get_api_client()

        with ui.tabs().classes("w-full") as tabs:
            pat_tab = ui.tab("Personal Access Tokens")
            cat_tab = ui.tab("Collection Access Tokens")

        default_tab = cat_tab if tab == "cat" else pat_tab

        with ui.tab_panels(tabs, value=default_tab).classes("w-full"):
            with ui.tab_panel(pat_tab):
                _render_pat_panel(api_client, sort_by, sort_desc)
            with ui.tab_panel(cat_tab):
                _render_cat_panel(api_client, sort_by, sort_desc)

    render_page(content)


def _render_pat_panel(api_client, sort_by: str = "", sort_desc: bool = False):
    ui.label("Personal Access Tokens").classes("text-xl font-bold mb-4")

    pat_label = ui.input("Token Label").classes("w-full")
    pat_expires = ui.input("Expires in (days, optional)").classes("w-full")

    async def create_pat():
        expires_days = None
        if pat_expires.value:
            try:
                expires_days = int(pat_expires.value)
            except ValueError:
                ui.notify("Invalid expires value", type="negative")
                return
        response = api_client.create_pat(pat_label.value, expires_days)
        if response.status_code == 201:
            data = response.json()
            token = data.get("token", "N/A")
            await mcp_token_dialog(token, "Token Created")
            pat_label.set_value("")
            pat_expires.set_value("")
        else:
            ui.notify(f"Error: {response.text}", type="negative")

    ui.button("Create PAT", on_click=create_pat).props("color=primary")

    response = api_client.list_pats()
    if response.status_code == 200:
        pats = response.json().get("tokens", [])
        if pats:
            _render_pat_table(api_client, pats, sort_by, sort_desc)
        else:
            ui.label("No PATs yet.")
    else:
        ui.notify(f"Error loading PATs: {response.text}", type="negative")


def _render_pat_table(api_client, pats, sort_by: str = "", sort_desc: bool = False):
    if not sort_by:
        sort_by = "is_active"
        sort_desc = True
    columns = make_columns_sortable(
        [
            {"name": "label", "label": "Label", "field": "label", "align": "left"},
            {"name": "scopes", "label": "Scopes", "field": "scopes", "align": "left"},
            {"name": "is_active", "label": "Active", "field": "is_active", "align": "left"},
            {"name": "expires_at", "label": "Expires", "field": "expires_at", "align": "left"},
            {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
        ]
    )

    pagination = create_table_pagination(sort_by, sort_desc, settings.web_records_per_page)

    rows = []
    for p in pats:
        expires = p.get("expires_at")
        if expires:
            expires = format_time_remaining(expires)
        rows.append(
            {
                "label": p["label"],
                "scopes": ", ".join(p.get("scopes", [])),
                "is_active": p.get("is_active", False),
                "expires_at": expires or "Never",
                "id": p["pat_id"],
            }
        )

    async def _rotate_pat(item_id: str):
        response = api_client.rotate_pat(item_id)
        if response.status_code == 200:
            data = response.json()
            token = data.get("token", "N/A")
            await mcp_token_dialog(token, "Token Rotated")
        else:
            ui.notify(f"Error: {response.text}", type="negative")

    async def _revoke_pat(item_id: str):
        response = api_client.revoke_pat(item_id)
        if handle_api_error(response, "Failed to revoke PAT"):
            ui.notify("PAT revoked")
            ui.navigate.reload()

    def rotate_pat(item):
        if not item.get("is_active", False):
            ui.notify("Inactive PATs cannot be rotated", type="warning")
            return None
        item_id = item["id"]
        return _rotate_pat(item_id)

    def revoke_pat(item):
        if not item.get("is_active", False):
            ui.notify("PAT is already inactive", type="warning")
            return None
        item_id = item["id"]
        return _revoke_pat(item_id)

    table = ui.table(columns=columns, rows=rows, row_key="id", pagination=pagination).classes(
        "w-full"
    )
    table.on(
        "update:pagination",
        create_sort_handler("/tokens", lambda: {"tab": "pat"}, sort_by, sort_desc),
    )

    table.add_slot(
        "body-cell-is_active",
        """<q-td :props="props">
            <q-badge :color="props.value ? 'positive' : 'negative'">
                {{ props.value ? 'Active' : 'Inactive' }}
            </q-badge>
        </q-td>""",
    )

    table.add_slot(
        "body-cell-label",
        """<q-td :props="props">
            <div :class="props.row.is_active ? '' : 'text-grey text-italic'">
                {{ props.value }}
            </div>
        </q-td>""",
    )

    add_table_action_buttons(
        table,
        "actions",
        [
            {
                "icon": "refresh",
                "color": "warning",
                "on_click": rotate_pat,
                "extra_fields": {"is_active": "is_active"},
                "confirm": True,
                "confirm_message": "A new token will be generated and the old one will be invalidated.",
                "confirm_label": "Rotate",
            },
            {
                "icon": "delete",
                "color": "negative",
                "on_click": revoke_pat,
                "extra_fields": {"is_active": "is_active"},
                "confirm": True,
                "confirm_message": "This action cannot be undone.",
                "confirm_label": "Revoke",
            },
        ],
    )


def _render_cat_panel(api_client, sort_by: str = "", sort_desc: bool = False):
    ui.label("Collection Access Tokens").classes("text-xl font-bold mb-4")

    cat_label = ui.input("Token Label").classes("w-full")
    collection_list = api_client.list_collections().json().get("collections", [])
    collection_options = {"__all__": "All Collections"}
    collection_options.update({c["collection_id"]: c["name"] for c in collection_list})
    cat_collection = ui.select(
        label="Collection",
        options=collection_options,
        value="__all__",
    ).classes("w-full")
    cat_permission = ui.select(
        options={"read": "Read", "read_write": "Read/Write"},
        label="Permission",
        value="read_write",
    ).classes("w-full")
    cat_expires = ui.input("Expires in (days, optional)").classes("w-full")

    async def create_cat():
        expires_days = None
        if cat_expires.value:
            try:
                expires_days = int(cat_expires.value)
            except ValueError:
                ui.notify("Invalid expires value", type="negative")
                return

        def _val(x):
            if isinstance(x, dict):
                return x.get("value")
            return x

        collection_id = _val(cat_collection.value)
        if collection_id == "__all__":
            collection_id = None
        permission_id = _val(cat_permission.value) or "read"
        response = api_client.create_cat(
            cat_label.value,
            collection_id,
            permission_id,
            expires_days,
        )
        if response.status_code == 201:
            data = response.json()
            token = data.get("token", "N/A")
            await mcp_token_dialog(token, "Token Created")
            cat_label.set_value("")
            cat_expires.set_value("")
        else:
            ui.notify(f"Error: {response.text}", type="negative")

    ui.button("Create CAT", on_click=create_cat).props("color=primary")

    response = api_client.list_cats()
    if response.status_code == 200:
        cats = response.json().get("tokens", [])
        if cats:
            _render_cat_table(api_client, cats, sort_by, sort_desc)
        else:
            ui.label("No CATs yet.")
    else:
        ui.notify(f"Error loading CATs: {response.text}", type="negative")


def _render_cat_table(api_client, cats, sort_by: str = "", sort_desc: bool = False):
    if not sort_by:
        sort_by = "is_active"
        sort_desc = True
    columns = make_columns_sortable(
        [
            {"name": "label", "label": "Label", "field": "label", "align": "left"},
            {
                "name": "collection_name",
                "label": "Collection",
                "field": "collection_name",
                "align": "left",
            },
            {"name": "permission", "label": "Permission", "field": "permission", "align": "left"},
            {"name": "is_active", "label": "Active", "field": "is_active", "align": "left"},
            {"name": "expires_at", "label": "Expires", "field": "expires_at", "align": "left"},
            {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
        ]
    )

    pagination = create_table_pagination(sort_by, sort_desc, settings.web_records_per_page)

    rows = []
    for c in cats:
        expires = c.get("expires_at")
        if expires:
            expires = format_time_remaining(expires)
        rows.append(
            {
                "label": c["label"],
                "collection_name": c.get("collection_name", "N/A"),
                "permission": c.get("permission", "read"),
                "is_active": c.get("is_active", False),
                "expires_at": expires or "Never",
                "id": c["cat_id"],
            }
        )

    async def _rotate_cat(item_id: str):
        response = api_client.rotate_cat(item_id)
        if response.status_code == 200:
            data = response.json()
            token = data.get("token", "N/A")
            await mcp_token_dialog(token, "Token Rotated")
        else:
            ui.notify(f"Error: {response.text}", type="negative")

    async def _revoke_cat(item_id: str):
        response = api_client.revoke_cat(item_id)
        if handle_api_error(response, "Failed to revoke CAT"):
            ui.notify("CAT revoked")
            ui.navigate.to("/tokens?tab=cat")

    def rotate_cat(item):
        if not item.get("is_active", False):
            ui.notify("Inactive CATs cannot be rotated", type="warning")
            return None
        item_id = item["id"]
        return _rotate_cat(item_id)

    def revoke_cat(item):
        if not item.get("is_active", False):
            ui.notify("CAT is already inactive", type="warning")
            return None
        item_id = item["id"]
        return _revoke_cat(item_id)

    table = ui.table(columns=columns, rows=rows, row_key="id", pagination=pagination).classes(
        "w-full"
    )
    table.on(
        "update:pagination",
        create_sort_handler("/tokens", lambda: {"tab": "cat"}, sort_by, sort_desc),
    )

    table.add_slot(
        "body-cell-is_active",
        """<q-td :props="props">
            <q-badge :color="props.value ? 'positive' : 'negative'">
                {{ props.value ? 'Active' : 'Inactive' }}
            </q-badge>
        </q-td>""",
    )

    table.add_slot(
        "body-cell-label",
        """<q-td :props="props">
            <div :class="props.row.is_active ? '' : 'text-grey text-italic'">
                {{ props.value }}
            </div>
        </q-td>""",
    )

    add_table_action_buttons(
        table,
        "actions",
        [
            {
                "icon": "refresh",
                "color": "warning",
                "on_click": rotate_cat,
                "extra_fields": {"is_active": "is_active"},
                "confirm": True,
                "confirm_message": "A new token will be generated and the old one will be invalidated.",
                "confirm_label": "Rotate",
            },
            {
                "icon": "delete",
                "color": "negative",
                "on_click": revoke_cat,
                "extra_fields": {"is_active": "is_active"},
                "confirm": True,
                "confirm_message": "This action cannot be undone.",
                "confirm_label": "Revoke",
            },
        ],
    )
