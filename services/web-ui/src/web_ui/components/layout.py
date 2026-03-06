import os

from nicegui import ui

from web_ui.components.navbar import render_nav

CSS = """
body, html { margin: 0; padding: 0; }
.q-page-container { margin: 0 !important; padding: 0 !important; }
.q-layout { margin: 0 !important; }
"""

JS_PATH = os.path.join(os.path.dirname(__file__), "..", "static", "js", "token_refresh.js")
with open(JS_PATH) as f:
    TOKEN_REFRESH_JS = f.read()


def render_page(content_fn):
    ui.add_css(CSS, shared=True)
    ui.add_head_html(f"<script>{TOKEN_REFRESH_JS}</script>", shared=True)
    with ui.column().classes("w-full max-w-6xl mx-auto p-4"):
        render_nav()
        with ui.card().classes("w-full mt-4"):
            content_fn()
