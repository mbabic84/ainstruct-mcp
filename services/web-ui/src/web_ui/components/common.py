import json

from nicegui import ui

from web_ui.utils import handle_api_error


async def document_dialog(doc_id: str, api_client):
    response = api_client.get_document(doc_id)
    if not handle_api_error(response, "Failed to load document"):
        return

    doc = response.json()

    supported_types = ["markdown", "text", "html", "json", "yaml", "xml", "python", "javascript"]

    with ui.dialog() as dialog, ui.card().classes("w-[800px] max-w-none h-[800px] flex flex-col"):
        # State management without ui.state (for broader compatibility)
        state = {"mode": "view"}

        # We use a dict to hold the current values so they can be easily updated
        current_doc = {
            "title": doc["title"],
            "document_type": doc["document_type"],
            "content": doc.get("content", ""),
        }

        with ui.row().classes("w-full items-center justify-between mb-2"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("description", size="md")
                ui.label().bind_text_from(current_doc, "title").classes("text-xl font-bold")

            with ui.row().classes("items-center gap-2"):
                edit_btn = ui.button(
                    icon="edit",
                    on_click=lambda: [state.update({"mode": "edit"}), update_visibility()],
                ).props("flat round")
                view_btn = ui.button(
                    icon="visibility",
                    on_click=lambda: [
                        state.update({"mode": "view"}),
                        update_visibility(),
                        update_viewer(),
                    ],
                ).props("flat round")
                ui.button(icon="close", on_click=dialog.close).props("flat round")

        ui.separator()

        # Viewer Section
        viewer_scroll = ui.scroll_area().classes("flex-grow w-full mt-4")
        with viewer_scroll:
            viewer_container = ui.column().classes("w-full")

            def update_viewer():
                viewer_container.clear()
                with viewer_container:
                    content = current_doc["content"]
                    doc_type = current_doc["document_type"]

                    if doc_type == "markdown":
                        ui.markdown(content).classes("w-full")
                    elif doc_type == "json":
                        try:
                            data = json.loads(content)
                            ui.json_editor(
                                {"content": {"json": data}}, properties={"readOnly": True}
                            ).classes("w-full")
                        except Exception:
                            ui.code(content, language="json").classes("w-full font-mono")
                    elif doc_type in ["yaml", "xml", "html", "python", "javascript"]:
                        ui.code(content, language=doc_type).classes("w-full font-mono")
                    else:
                        ui.pre(content).classes("whitespace-pre-wrap w-full font-mono text-sm")

        # Editor Section
        editor_scroll = ui.scroll_area().classes("flex-grow w-full mt-4")
        with editor_scroll:
            editor_container = ui.column().classes("w-full gap-4")
            with editor_container:
                ui.input("Title").classes("w-full").bind_value(current_doc, "title")
                ui.select(options=supported_types, label="Document Type").classes(
                    "w-full"
                ).bind_value(current_doc, "document_type")

                # Use codemirror if available, fallback to textarea
                try:
                    # We use a container to allow swapping if needed, though here we just try-except
                    content_editor = ui.codemirror(current_doc["content"]).classes(
                        "w-full flex-grow border min-h-[400px]"
                    )
                    content_editor.bind_value(current_doc, "content")
                except Exception:
                    content_editor = (
                        ui.textarea("Content")
                        .classes("w-full flex-grow min-h-[400px]")
                        .props("filled")
                    )
                    content_editor.bind_value(current_doc, "content")

                with ui.row().classes("w-full justify-end gap-2 mt-2"):

                    async def save():
                        resp = api_client.update_document(
                            doc_id,
                            title=current_doc["title"],
                            document_type=current_doc["document_type"],
                            content=current_doc["content"],
                        )
                        if handle_api_error(resp, "Failed to update document"):
                            ui.notify("Document updated successfully")
                            state["mode"] = "view"
                            update_visibility()
                            update_viewer()
                            # Signal that we might need to refresh the background table
                            dialog.submit(True)

                    ui.button("Save Changes", on_click=save).props("color=primary")
                    ui.button(
                        "Cancel",
                        on_click=lambda: [
                            state.update({"mode": "view"}),
                            update_visibility(),
                            update_viewer(),
                        ],
                    ).props("flat")

        def update_visibility():
            is_view = state["mode"] == "view"
            viewer_scroll.set_visibility(is_view)
            edit_btn.set_visibility(is_view)
            editor_scroll.set_visibility(not is_view)
            view_btn.set_visibility(not is_view)

        # Initial render
        update_viewer()
        update_visibility()

    dialog.open()
    return await dialog


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
