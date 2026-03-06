from nicegui import ui


async def confirm_action(
    title: str,
    message: str,
    on_confirm,
    cancel_label: str = "Cancel",
    confirm_label: str = "Confirm",
    color: str = "negative",
):
    with ui.dialog() as dialog, ui.card():
        ui.label(title).classes("text-lg font-bold")
        ui.label(message).classes("text-sm text-grey-7")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(cancel_label, on_click=dialog.close).props("flat")
            ui.button(
                confirm_label,
                on_click=lambda: [dialog.close(), on_confirm()],
            ).props(f"color={color}")
    dialog.open()


async def mcp_token_dialog(token: str, title: str = "Token Created"):
    origin = await ui.run_javascript("window.location.origin")
    mcp_url = f"{origin}/mcp"
    with ui.dialog() as dialog, ui.card().classes("w-[500px]"):
        ui.label(title).classes("text-xl font-bold mb-2")
        ui.label("Please copy your token now. You won't be able to see it again!").classes(
            "text-sm text-grey-7 mb-4"
        )
        token_input = ui.input(value=token).classes("w-full font-mono")
        token_input.props("readonly")
        ui.label("MCP Configuration (OpenCode format)").classes("text-sm font-bold mt-4 mb-2")
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
        mcp_input = ui.textarea(value=mcp_config).classes("w-full font-mono text-sm")
        mcp_input.props("readonly rows=8")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(
                "Copy",
                on_click=lambda: ui.navigate.to(
                    f"javascript:navigator.clipboard.writeText('{token}')"
                ),
            ).props("flat")
            ui.button("Close", on_click=lambda: [dialog.close(), ui.navigate.reload()]).props(
                "color=primary"
            )
    dialog.open()


def create_table_actions_slot(buttons: list[dict]):
    slot_content = '<q-td :props="props">'
    for btn in buttons:
        color = btn.get("color", "primary")
        icon = btn.get("icon", "add")
        emit = btn.get("emit", "click")
        slot_content += f'\n                            <q-btn flat round color="{color}" icon="{icon}" @click.stop="$parent.$emit(\'{emit}\', props.row)" />'
    slot_content += "\n                        </q-td>"
    return slot_content


def add_table_actions(table, buttons: list[dict]):
    slot_content = create_table_actions_slot(buttons)
    table.add_slot("body-cell-actions", slot_content)
    return table
