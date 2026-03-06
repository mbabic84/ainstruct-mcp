from datetime import datetime

from nicegui import APIRouter, ui

from web_ui.auth import load_tokens_from_storage, require_auth
from web_ui.components import render_page

router = APIRouter(prefix="")


@router.page("/tokens")
async def tokens_page(tab: str = "pat"):
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
                        origin = await ui.run_javascript("window.location.origin")
                        mcp_url = f"{origin}/mcp"
                        with ui.dialog() as dialog, ui.card().classes("w-[500px]"):
                            ui.label("Token Created").classes("text-xl font-bold mb-2")
                            ui.label(
                                "Please copy your token now. You won't be able to see it again!"
                            ).classes("text-sm text-grey-7 mb-4")
                            token_input = ui.input(value=token).classes("w-full font-mono")
                            token_input.props("readonly")
                            ui.label("MCP Configuration (OpenCode format)").classes(
                                "text-sm font-bold mt-4 mb-2"
                            )
                            mcp_config = f'''{{
  "ainstruct": {{
    "type": "remote",
    "url": "{mcp_url}",
    "headers": {{
      "Authorization": "Bearer {token}"
    }},
    "enabled": true
  }}
}}'''
                            mcp_input = ui.textarea(value=mcp_config).classes(
                                "w-full font-mono text-sm"
                            )
                            mcp_input.props("readonly rows=8")
                            with ui.row().classes("w-full justify-end gap-2"):
                                ui.button(
                                    "Copy",
                                    on_click=lambda: ui.navigate.to(
                                        f"javascript:navigator.clipboard.writeText('{token}')"
                                    ),
                                ).props("flat")
                                ui.button(
                                    "Close", on_click=lambda: [dialog.close(), ui.navigate.reload()]
                                ).props("color=primary")
                        dialog.open()
                        pat_label.set_value("")
                        pat_expires.set_value("")
                    else:
                        ui.notify(f"Error: {response.text}", type="negative")

                ui.button("Create PAT", on_click=create_pat).props("color=primary")

                response = api_client.list_pats()
                if response.status_code == 200:
                    pats = response.json().get("tokens", [])
                    if pats:
                        with ui.card().classes("w-full mt-4"):
                            columns = [
                                {
                                    "name": "label",
                                    "label": "Label",
                                    "field": "label",
                                    "align": "left",
                                },
                                {
                                    "name": "scopes",
                                    "label": "Scopes",
                                    "field": "scopes",
                                    "align": "left",
                                },
                                {
                                    "name": "is_active",
                                    "label": "Active",
                                    "field": "is_active",
                                    "align": "left",
                                },
                                {
                                    "name": "created_at",
                                    "label": "Created",
                                    "field": "created_at",
                                    "align": "left",
                                },
                                {
                                    "name": "expires_at",
                                    "label": "Expires",
                                    "field": "expires_at",
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
                            for p in pats:
                                if not p.get("is_active"):
                                    continue
                                expires = p.get("expires_at")
                                if expires:
                                    expires = datetime.fromisoformat(
                                        expires.replace("Z", "+00:00")
                                    ).strftime("%Y-%m-%d")
                                rows.append(
                                    {
                                        "label": p["label"],
                                        "scopes": ", ".join(p.get("scopes", [])),
                                        "is_active": "Yes" if p.get("is_active") else "No",
                                        "created_at": datetime.fromisoformat(
                                            p["created_at"].replace("Z", "+00:00")
                                        ).strftime("%Y-%m-%d"),
                                        "expires_at": expires or "Never",
                                        "id": p["pat_id"],
                                    }
                                )

                            def revoke_pat(e):
                                pat_id = e.args["id"]
                                pat_label_text = e.args.get("label", "this PAT")
                                with ui.dialog() as dialog, ui.card():
                                    ui.label(f"Are you sure you want to revoke '{pat_label_text}'?")
                                    ui.label("This action cannot be undone.").classes(
                                        "text-sm text-grey-7"
                                    )
                                    with ui.row().classes("w-full justify-end gap-2"):
                                        ui.button("Cancel", on_click=dialog.close).props("flat")
                                        ui.button(
                                            "Revoke",
                                            on_click=lambda: [
                                                dialog.close(),
                                                _do_revoke_pat(pat_id),
                                            ],
                                        ).props("color=negative")
                                dialog.open()

                            def _do_revoke_pat(pat_id):
                                response = api_client.revoke_pat(pat_id)
                                if response.status_code == 200:
                                    ui.notify("PAT revoked")
                                    ui.navigate.reload()
                                else:
                                    ui.notify(f"Error: {response.text}", type="negative")

                            def rotate_pat(e):
                                pat_id = e.args["id"]
                                pat_label_text = e.args.get("label", "this PAT")
                                with ui.dialog() as dialog, ui.card():
                                    ui.label(f"Are you sure you want to rotate '{pat_label_text}'?")
                                    ui.label(
                                        "A new token will be generated and the old one will be invalidated."
                                    ).classes("text-sm text-grey-7")
                                    with ui.row().classes("w-full justify-end gap-2"):
                                        ui.button("Cancel", on_click=dialog.close).props("flat")
                                        ui.button(
                                            "Rotate",
                                            on_click=lambda: [
                                                dialog.close(),
                                                _do_rotate_pat(pat_id),
                                            ],
                                        ).props("color=warning")
                                dialog.open()

                            def _do_rotate_pat(pat_id):
                                response = api_client.rotate_pat(pat_id)
                                if response.status_code == 200:
                                    data = response.json()
                                    token = data.get("token", "N/A")
                                    with ui.dialog() as dialog, ui.card().classes("w-[500px]"):
                                        ui.label("Token Rotated").classes("text-xl font-bold mb-2")
                                        ui.label(
                                            "Please copy your new token now. You won't be able to see it again!"
                                        ).classes("text-sm text-grey-7 mb-4")
                                        token_input = ui.input(value=token).classes(
                                            "w-full font-mono"
                                        )
                                        token_input.props("readonly")
                                        with ui.row().classes("w-full justify-end gap-2"):
                                            ui.button(
                                                "Copy",
                                                on_click=lambda: ui.navigate.to(
                                                    f"javascript:navigator.clipboard.writeText('{token}')"
                                                ),
                                            ).props("flat")
                                            ui.button(
                                                "Close",
                                                on_click=lambda: [
                                                    dialog.close(),
                                                    ui.navigate.reload(),
                                                ],
                                            ).props("color=primary")
                                    dialog.open()
                                else:
                                    ui.notify(f"Error: {response.text}", type="negative")

                            pat_table = (
                                ui.table(columns=columns, rows=rows, row_key="id")
                                .classes("w-full")
                                .on("rotate-click", rotate_pat)
                                .on("revoke-click", revoke_pat)
                            )
                            pat_table.add_slot(
                                "body-cell-actions",
                                """<q-td :props="props">
                                    <q-btn flat round color="warning" icon="refresh" @click.stop="$parent.$emit('rotate-click', props.row)" />
                                    <q-btn flat round color="negative" icon="delete" @click.stop="$parent.$emit('revoke-click', props.row)" />
                                </q-td>""",
                            )
                    else:
                        ui.label("No PATs yet.")
                else:
                    ui.notify(f"Error loading PATs: {response.text}", type="negative")

            with ui.tab_panel(cat_tab):
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
                        origin = await ui.run_javascript("window.location.origin")
                        mcp_url = f"{origin}/mcp"
                        with ui.dialog() as dialog, ui.card().classes("w-[500px]"):
                            ui.label("Token Created").classes("text-xl font-bold mb-2")
                            ui.label(
                                "Please copy your token now. You won't be able to see it again!"
                            ).classes("text-sm text-grey-7 mb-4")
                            token_input = ui.input(value=token).classes("w-full font-mono")
                            token_input.props("readonly")
                            ui.label("MCP Configuration (OpenCode format)").classes(
                                "text-sm font-bold mt-4 mb-2"
                            )
                            mcp_config = f'''{{
  "ainstruct": {{
    "type": "remote",
    "url": "{mcp_url}",
    "headers": {{
      "Authorization": "Bearer {token}"
    }},
    "enabled": true
  }}
}}'''
                            mcp_input = ui.textarea(value=mcp_config).classes(
                                "w-full font-mono text-sm"
                            )
                            mcp_input.props("readonly rows=8")
                            with ui.row().classes("w-full justify-end gap-2"):
                                ui.button(
                                    "Copy",
                                    on_click=lambda: ui.navigate.to(
                                        f"javascript:navigator.clipboard.writeText('{token}')"
                                    ),
                                ).props("flat")
                                ui.button(
                                    "Close",
                                    on_click=lambda: [
                                        dialog.close(),
                                        ui.navigate.to("/tokens?tab=cat"),
                                    ],
                                ).props("color=primary")
                        dialog.open()
                        cat_label.set_value("")
                        cat_expires.set_value("")
                    else:
                        ui.notify(f"Error: {response.text}", type="negative")

                ui.button("Create CAT", on_click=create_cat).props("color=primary")

                response = api_client.list_cats()
                if response.status_code == 200:
                    cats = response.json().get("tokens", [])
                    if cats:
                        with ui.card().classes("w-full mt-4"):
                            columns = [
                                {
                                    "name": "label",
                                    "label": "Label",
                                    "field": "label",
                                    "align": "left",
                                },
                                {
                                    "name": "collection_name",
                                    "label": "Collection",
                                    "field": "collection_name",
                                    "align": "left",
                                },
                                {
                                    "name": "permission",
                                    "label": "Permission",
                                    "field": "permission",
                                    "align": "left",
                                },
                                {
                                    "name": "is_active",
                                    "label": "Active",
                                    "field": "is_active",
                                    "align": "left",
                                },
                                {
                                    "name": "created_at",
                                    "label": "Created",
                                    "field": "created_at",
                                    "align": "left",
                                },
                                {
                                    "name": "expires_at",
                                    "label": "Expires",
                                    "field": "expires_at",
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
                            for c in cats:
                                if not c.get("is_active"):
                                    continue
                                expires = c.get("expires_at")
                                if expires:
                                    expires = datetime.fromisoformat(
                                        expires.replace("Z", "+00:00")
                                    ).strftime("%Y-%m-%d")
                                rows.append(
                                    {
                                        "label": c["label"],
                                        "collection_name": c.get("collection_name", "N/A"),
                                        "permission": c.get("permission", "read"),
                                        "is_active": "Yes" if c.get("is_active") else "No",
                                        "created_at": datetime.fromisoformat(
                                            c["created_at"].replace("Z", "+00:00")
                                        ).strftime("%Y-%m-%d"),
                                        "expires_at": expires or "Never",
                                        "id": c["cat_id"],
                                    }
                                )

                            def revoke_cat(e):
                                cat_id = e.args["id"]
                                cat_label_text = e.args.get("label", "this CAT")
                                with ui.dialog() as dialog, ui.card():
                                    ui.label(f"Are you sure you want to revoke '{cat_label_text}'?")
                                    ui.label("This action cannot be undone.").classes(
                                        "text-sm text-grey-7"
                                    )
                                    with ui.row().classes("w-full justify-end gap-2"):
                                        ui.button("Cancel", on_click=dialog.close).props("flat")
                                        ui.button(
                                            "Revoke",
                                            on_click=lambda: [
                                                dialog.close(),
                                                _do_revoke_cat(cat_id),
                                            ],
                                        ).props("color=negative")
                                dialog.open()

                            def _do_revoke_cat(cat_id):
                                response = api_client.revoke_cat(cat_id)
                                if response.status_code == 200:
                                    ui.notify("CAT revoked")
                                    ui.navigate.to("/tokens?tab=cat")
                                else:
                                    ui.notify(f"Error: {response.text}", type="negative")

                            def rotate_cat(e):
                                cat_id = e.args["id"]
                                cat_label_text = e.args.get("label", "this CAT")
                                with ui.dialog() as dialog, ui.card():
                                    ui.label(f"Are you sure you want to rotate '{cat_label_text}'?")
                                    ui.label(
                                        "A new token will be generated and the old one will be invalidated."
                                    ).classes("text-sm text-grey-7")
                                    with ui.row().classes("w-full justify-end gap-2"):
                                        ui.button("Cancel", on_click=dialog.close).props("flat")
                                        ui.button(
                                            "Rotate",
                                            on_click=lambda: [
                                                dialog.close(),
                                                _do_rotate_cat(cat_id),
                                            ],
                                        ).props("color=warning")
                                dialog.open()

                            def _do_rotate_cat(cat_id):
                                response = api_client.rotate_cat(cat_id)
                                if response.status_code == 200:
                                    data = response.json()
                                    token = data.get("token", "N/A")
                                    with ui.dialog() as dialog, ui.card().classes("w-[500px]"):
                                        ui.label("Token Rotated").classes("text-xl font-bold mb-2")
                                        ui.label(
                                            "Please copy your new token now. You won't be able to see it again!"
                                        ).classes("text-sm text-grey-7 mb-4")
                                        token_input = ui.input(value=token).classes(
                                            "w-full font-mono"
                                        )
                                        token_input.props("readonly")
                                        with ui.row().classes("w-full justify-end gap-2"):
                                            ui.button(
                                                "Copy",
                                                on_click=lambda: ui.navigate.to(
                                                    f"javascript:navigator.clipboard.writeText('{token}')"
                                                ),
                                            ).props("flat")
                                            ui.button(
                                                "Close",
                                                on_click=lambda: [
                                                    dialog.close(),
                                                    ui.navigate.to("/tokens?tab=cat"),
                                                ],
                                            ).props("color=primary")
                                    dialog.open()
                                else:
                                    ui.notify(f"Error: {response.text}", type="negative")

                            cat_table = (
                                ui.table(columns=columns, rows=rows, row_key="id")
                                .classes("w-full")
                                .on("rotate-click", rotate_cat)
                                .on("revoke-click", revoke_cat)
                            )
                            cat_table.add_slot(
                                "body-cell-actions",
                                """<q-td :props="props">
                                    <q-btn flat round color="warning" icon="refresh" @click.stop="$parent.$emit('rotate-click', props.row)" />
                                    <q-btn flat round color="negative" icon="delete" @click.stop="$parent.$emit('revoke-click', props.row)" />
                                </q-td>""",
                            )
                    else:
                        ui.label("No CATs yet.")
                else:
                    ui.notify(f"Error loading CATs: {response.text}", type="negative")

    render_page(content)
