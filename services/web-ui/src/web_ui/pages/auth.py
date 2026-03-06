from nicegui import APIRouter, ui

from web_ui.auth import login_user, register_user

router = APIRouter(prefix="")


@router.page("/login")
def login_page():
    from web_ui.auth import load_tokens_from_storage

    async def try_login():
        if not username_input.value:
            error_label.set_text("Username is required")
            return
        if not password_input.value:
            error_label.set_text("Password is required")
            return

        success, error = await login_user(username_input.value, password_input.value)
        if success:
            ui.navigate.to("/dashboard")
        else:
            error_label.set_text(error)

    ui.timer(0.1, load_tokens_from_storage, once=True)

    with ui.column().classes("w-full h-screen justify-center items-center"):
        with ui.card().classes("w-full max-w-md p-8"):
            ui.label("Welcome Back").classes("text-2xl font-bold text-center w-full mb-6")

            username_input = (
                ui.input(
                    "Username",
                    placeholder="Enter your username",
                )
                .classes("w-full")
                .on("keydown.enter", try_login)
            )

            password_input = (
                ui.input(
                    "Password",
                    password=True,
                    password_toggle_button=True,
                    placeholder="Enter your password",
                )
                .classes("w-full")
                .on("keydown.enter", try_login)
            )

            error_label = ui.label("").classes("text-red-500 text-center w-full mt-2")

            ui.button("Login", on_click=try_login).classes("w-full mt-4").props("color=primary")

            with ui.row().classes("w-full justify-center gap-2 mt-4"):
                ui.label("Don't have an account?")
                ui.button("Register", on_click=lambda: ui.navigate.to("/register")).props(
                    "flat color=primary"
                )


@router.page("/register")
def register_page():
    from web_ui.auth import load_tokens_from_storage

    async def try_register():
        if password_input.value != confirm_password_input.value:
            error_label.set_text("Passwords do not match")
            return

        success, error = await register_user(
            username_input.value, email_input.value, password_input.value
        )
        if success:
            ui.notify("Registration successful! Please login.")
            ui.navigate.to("/login")
        else:
            error_label.set_text(error)

    ui.timer(0.1, load_tokens_from_storage, once=True)

    with ui.column().classes("w-full h-screen justify-center items-center"):
        with ui.card().classes("w-full max-w-md p-8"):
            ui.label("Register").classes("text-2xl font-bold text-center w-full mb-6")

            username_input = ui.input("Username", placeholder="Enter your username").classes(
                "w-full"
            )
            email_input = ui.input("Email", placeholder="Enter your email").classes("w-full")
            password_input = ui.input(
                "Password",
                password=True,
                password_toggle_button=True,
                placeholder="Enter your password",
            ).classes("w-full")
            confirm_password_input = ui.input(
                "Confirm Password",
                password=True,
                password_toggle_button=True,
                placeholder="Confirm your password",
            ).classes("w-full")
            error_label = ui.label("").classes("text-red-500 text-center w-full mt-2")

            username_input.on("keydown.enter", try_register)
            email_input.on("keydown.enter", try_register)
            password_input.on("keydown.enter", try_register)
            confirm_password_input.on("keydown.enter", try_register)

            ui.button("Register", on_click=try_register).classes("w-full mt-4").props(
                "color=primary"
            )

            with ui.row().classes("w-full justify-center gap-2 mt-4"):
                ui.label("Already have an account?")
                ui.button("Login", on_click=lambda: ui.navigate.to("/login")).props(
                    "flat color=primary"
                )
