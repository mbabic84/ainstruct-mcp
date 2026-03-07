from nicegui import ui

from web_ui.auth import get_user, is_admin, is_logged_in, logout


def render_nav():
    with ui.row().classes("w-full justify-between items-center p-2"):
        with ui.row().classes("items-center gap-2"):
            ui.image("/static/favicon.svg").classes("w-10 h-10")
            ui.label("Ainstruct").classes("text-xl font-bold")
        with ui.row().classes("items-center gap-4"):
            if is_logged_in():
                if is_admin():
                    ui.button("Admin", on_click=lambda: ui.navigate.to("/admin")).props("flat")
                ui.button("Dashboard", on_click=lambda: ui.navigate.to("/dashboard")).props("flat")
                ui.button("Collections", on_click=lambda: ui.navigate.to("/collections")).props(
                    "flat"
                )
                ui.button("Documents", on_click=lambda: ui.navigate.to("/documents")).props("flat")
                ui.button("Tokens", on_click=lambda: ui.navigate.to("/tokens")).props("flat")
                user = get_user()
                if user:
                    ui.label(f"Hello, {user.get('username', 'User')}").classes("text-sm")
                ui.button("Logout", on_click=logout).props("flat color=negative")
