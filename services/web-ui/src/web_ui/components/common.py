import asyncio
from collections.abc import Callable

from nicegui import ui


def make_columns_sortable(columns: list[dict], exclude: list[str] | None = None) -> list[dict]:
    """Add sortable=True to all columns except excluded ones."""
    exclude = exclude or ["actions"]
    return [{**col, "sortable": True} if col.get("name") not in exclude else col for col in columns]


def create_table_pagination(sort_by: str = "", sort_desc: bool = False) -> dict:
    """Create pagination dict for table with optional sort params."""
    pagination = {}
    if sort_by:
        pagination["sortBy"] = sort_by
        pagination["descending"] = sort_desc
    return pagination


def build_sort_url(
    base_url: str,
    sort_by: str,
    sort_desc: bool,
    extra_params: dict | None = None,
) -> str:
    """Build URL with sort params. extra_params for non-sort params like collection_id or tab."""
    params = []
    if extra_params:
        for k, v in extra_params.items():
            if v is not None:
                params.append(f"{k}={v}")
    if sort_by:
        params.append(f"sort_by={sort_by}")
        if sort_desc:
            params.append("sort_desc=true")
    query = "&".join(params)
    return f"{base_url}?{query}" if query else base_url


def create_sort_handler(
    base_url: str,
    get_extra_params: Callable[[], dict | None] | None = None,
    current_sort_by: str = "",
    current_sort_desc: bool = False,
) -> Callable:
    """Create a sort handler that updates URL with sort params."""

    def handle_sort(e):
        sort_data = e.args
        if sort_data:
            new_sort_by = sort_data.get("sortBy", "") or ""
            new_sort_desc = bool(sort_data.get("descending", False))
            if new_sort_by != current_sort_by or new_sort_desc != current_sort_desc:
                extra = get_extra_params() if get_extra_params else None
                ui.navigate.to(build_sort_url(base_url, new_sort_by, new_sort_desc, extra))

    return handle_sort


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
            with ui.row().classes("gap-2 justify-center"):
                for btn in buttons:
                    icon = btn.get("icon", "add")
                    color = btn.get("color", "primary")
                    id_field = btn.get("id_field", "id")
                    label_field = btn.get("label_field", "label")
                    extra_fields = btn.get("extra_fields") or {}
                    on_click = btn.get("on_click")
                    confirm = btn.get("confirm")
                    confirm_message = btn.get("confirm_message", "Are you sure?")
                    confirm_label = btn.get("confirm_label", "Confirm")

                    extra = ""
                    for key, field in extra_fields.items():
                        extra += f", {key}: props.row.{field}"

                    def make_handler(
                        handler,
                        use_confirm=False,
                        confirm_msg="",
                        confirm_lbl="Confirm",
                        btn_color="primary",
                        label_field_name="label",
                    ):
                        async def handler_wrapper(e):
                            item_data = e.args
                            item_label = item_data.get(label_field_name) or item_data.get("label")
                            if not item_label:
                                item_label = "Item"
                            if use_confirm:

                                async def do_action():
                                    result = handler(item_data)
                                    if asyncio.iscoroutine(result):
                                        await result

                                message = confirm_msg.replace("{name}", f"'{item_label}'")
                                await confirm_action(
                                    f"{confirm_lbl} {item_label}?",
                                    message,
                                    do_action,
                                    "Cancel",
                                    confirm_lbl,
                                    color=btn_color,
                                )
                            else:
                                result = handler(item_data)
                                if asyncio.iscoroutine(result):
                                    await result

                        return handler_wrapper

                    handler = (
                        make_handler(
                            on_click,
                            use_confirm=confirm,
                            confirm_msg=confirm_message,
                            confirm_lbl=confirm_label,
                            btn_color=color,
                            label_field_name=label_field,
                        )
                        if on_click
                        else None
                    )

                    ui.button().props(f"icon={icon} flat round color={color}").on(
                        "click",
                        js_handler=f"""(e) => {{ e.stopPropagation(); emit({{ id: props.row.{id_field}, label: props.row.{label_field}{extra} }}) }}""",
                        handler=handler,
                    )
