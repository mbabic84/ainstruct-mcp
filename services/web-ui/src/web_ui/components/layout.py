from nicegui import ui

from web_ui.components.navbar import render_nav


def render_page(content_fn):
    with ui.column().classes("w-full max-w-6xl mx-auto p-4"):
        render_nav()
        with ui.card().classes("w-full mt-4"):
            content_fn()
