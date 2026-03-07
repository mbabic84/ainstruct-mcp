import asyncio
from inspect import iscoroutinefunction

from nicegui import ui


async def confirm_action(
    title: str,
    message: str,
    on_confirm,
    cancel_label: str = "Cancel",
    confirm_label: str = "Confirm",
    color: str = "negative",
):
    async def handle_confirm():
        dialog.close()
        if asyncio.iscoroutinefunction(on_confirm):
            await on_confirm()
        else:
            on_confirm()

    with ui.dialog() as dialog, ui.card():
        ui.label(title).classes("text-lg font-bold")
        ui.label(message).classes("text-sm text-grey-7")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button(cancel_label, on_click=dialog.close).props("flat")
            ui.button(
                confirm_label,
                on_click=handle_confirm,
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


def add_table_action_buttons(
    table,
    action: str,
    buttons: list[dict],
):
    with table.add_slot(f"body-cell-{action}"):
        with table.cell(action):
            for btn in buttons:
                icon = btn.get("icon", "add")
                color = btn.get("color", "primary")
                id_field = btn.get("id_field", "id")
                label_field = btn.get("label_field", "label")
                extra_fields = btn.get("extra_fields") or {}
                on_click = btn.get("on_click")

                extra = ""
                for key, field in extra_fields.items():
                    extra += f", {key}: props.row.{field}"

                def make_handler(handler):
                    async def handler_wrapper(e):
                        if iscoroutinefunction(handler):
                            await handler(e.args)
                        else:
                            handler(e.args)

                    return handler_wrapper

                ui.button().props(f"icon={icon} flat round color={color}").on(
                    "click",
                    js_handler=f"""(e) => {{ e.stopPropagation(); emit({{ id: props.row.{id_field}, label: props.row.{label_field}{extra} }}) }}""",
                    handler=make_handler(on_click),
                )
