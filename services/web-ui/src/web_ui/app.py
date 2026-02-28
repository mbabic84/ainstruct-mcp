import os
from datetime import datetime

from nicegui import app, ui

from web_ui.api_client import API_HOSTNAME, ApiClient

ui.add_css(
    """
body, html { margin: 0; padding: 0; }
.q-page-container { margin: 0 !important; padding: 0 !important; }
.q-layout { margin: 0 !important; }
""",
    shared=True,
)

api_client = ApiClient(hostname=API_HOSTNAME)


def update_storage_tokens(access_token: str, refresh_token: str):
    app.storage.user["access_token"] = access_token
    app.storage.user["refresh_token"] = refresh_token


async def init_client():
    if not api_client.hostname:
        origin = await ui.run_javascript("window.location.origin")
        api_client.set_cached_origin(origin)


api_client.set_token_refresh_callback(update_storage_tokens)


def get_user():
    return app.storage.user.get("user")


def is_logged_in():
    return bool(app.storage.user.get("access_token"))


def is_admin():
    return app.storage.user.get("user", {}).get("is_superuser", False)


def require_auth():
    if not is_logged_in():
        ui.navigate.to("/login")
        return False
    return True


def require_admin():
    if not require_auth():
        return False
    if not is_admin():
        ui.navigate.to("/dashboard")
        return False
    return True


async def logout():
    api_client.clear_tokens()
    app.storage.user.clear()
    ui.navigate.to("/login")


async def login_user(username: str, password: str) -> tuple[bool, str]:
    await init_client()
    response = api_client.login(username, password)
    if response.status_code == 200:
        data = response.json()
        api_client.set_tokens(data["access_token"], data["refresh_token"])

        profile_response = api_client.get_profile()
        if profile_response.status_code == 200:
            user_data = profile_response.json()
            app.storage.user["user"] = user_data
            app.storage.user["access_token"] = data["access_token"]
            app.storage.user["refresh_token"] = data["refresh_token"]
            return True, ""
        else:
            return False, "Failed to get user profile"
    elif response.status_code == 401:
        return False, "Invalid username or password"
    elif response.status_code == 403:
        return False, "Account is disabled"
    else:
        return False, f"Login failed: {response.status_code}"


async def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    await init_client()
    response = api_client.register(username, email, password)
    if response.status_code == 201:
        return True, ""
    elif response.status_code == 400:
        detail = response.json().get("detail", {})
        code = detail.get("code", "")
        if code == "USERNAME_EXISTS":
            return False, "Username already exists"
        elif code == "EMAIL_EXISTS":
            return False, "Email already exists"
        else:
            return False, detail.get("message", "Registration failed")
    else:
        return False, f"Registration failed: {response.status_code}"


def render_nav():
    with ui.row().classes("w-full justify-between items-center p-2"):
        with ui.row().classes("items-center gap-4"):
            ui.label("AI Document Memory").classes("text-xl font-bold")
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
                ui.label(f"Hello, {user['username']}").classes("text-sm")
                ui.button("Logout", on_click=logout).props("flat color=negative")


def render_page(content_fn):
    with ui.column().classes("w-full max-w-6xl mx-auto p-4"):
        render_nav()
        with ui.card().classes("w-full mt-4"):
            content_fn()


@ui.page("/login")
def login_page():

    async def try_login():
        if not username_input.value:
            error_label.set_text("Username is required")
            return
        if not password_input.value:
            error_label.set_text("Password is required")
            return

        success, error = await login_user(username_input.value, password_input.value)
        if success:
            if remember_me_checkbox.value:
                app.storage.user["remember_me"] = True
            ui.navigate.to("/dashboard")
        else:
            error_label.set_text(error)

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

            remember_me_checkbox = ui.checkbox("Remember me").classes("mt-2")

            error_label = ui.label("").classes("text-red-500 text-center w-full mt-2")

            ui.button("Login", on_click=try_login).classes("w-full mt-4").props("color=primary")

            with ui.row().classes("w-full justify-center gap-2 mt-4"):
                ui.label("Don't have an account?")
                ui.button("Register", on_click=lambda: ui.navigate.to("/register")).props(
                    "flat color=primary"
                )


@ui.page("/")
def index_page():
    if is_logged_in():
        ui.navigate.to("/dashboard")
    else:
        ui.navigate.to("/login")


@ui.page("/register")
def register_page():
    with ui.column().classes("w-full h-screen justify-center items-center"):
        with ui.card().classes("w-full max-w-md p-8"):
            ui.label("Register").classes("text-2xl font-bold text-center w-full mb-6")

            username_input = ui.input("Username").classes("w-full")
            email_input = ui.input("Email").classes("w-full")
            password_input = ui.input(
                "Password", password=True, password_toggle_button=True
            ).classes("w-full")
            confirm_password_input = ui.input(
                "Confirm Password", password=True, password_toggle_button=True
            ).classes("w-full")
            error_label = ui.label("").classes("text-red-500")

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

    ui.button("Register", on_click=try_register).classes("w-full")
    ui.label("Already have an account?").classes("mt-4")
    ui.button("Login", on_click=lambda: ui.navigate.to("/login")).props("flat color=primary")


@ui.page("/dashboard")
def dashboard_page():

    if not require_auth():
        return

    def content():
        user = get_user()
        ui.label(f"Welcome, {user['username']}!").classes("text-2xl font-bold")

        with ui.row().classes("w-full gap-4 mt-4"):
            response = api_client.list_collections()
            collections = (
                response.json().get("collections", []) if response.status_code == 200 else []
            )
            with ui.card().classes("flex-1"):
                ui.label("Collections").classes("text-lg font-bold")
                ui.label(str(len(collections))).classes("text-4xl")

            response = api_client.list_documents()
            docs_data = response.json() if response.status_code == 200 else {"total": 0}
            with ui.card().classes("flex-1"):
                ui.label("Documents").classes("text-lg font-bold")
                ui.label(str(docs_data.get("total", 0))).classes("text-4xl")

            response = api_client.list_pats()
            pats = response.json().get("tokens", []) if response.status_code == 200 else []
            with ui.card().classes("flex-1"):
                ui.label("PATs").classes("text-lg font-bold")
                ui.label(str(len(pats))).classes("text-4xl")

            response = api_client.list_cats()
            cats = response.json().get("tokens", []) if response.status_code == 200 else []
            with ui.card().classes("flex-1"):
                ui.label("CATs").classes("text-lg font-bold")
                ui.label(str(len(cats))).classes("text-4xl")

    render_page(content)


@ui.page("/collections")
def collections_page():

    if not require_auth():
        return

    def content():
        ui.label("Collections").classes("text-2xl font-bold")

        with ui.row().classes("w-full gap-2 mb-4"):
            new_name_input = ui.input("New Collection Name").classes("flex-1")

            def create_collection():
                if new_name_input.value:
                    response = api_client.create_collection(new_name_input.value)
                    if response.status_code == 201:
                        ui.notify("Collection created")
                        new_name_input.set_value("")
                        ui.navigate.reload()
                    else:
                        ui.notify(f"Error: {response.text}", type="negative")

            ui.button("Create", on_click=create_collection).props("color=primary")

        response = api_client.list_collections()
        if response.status_code == 200:
            collections = response.json().get("collections", [])
            if collections:
                with ui.card().classes("w-full"):
                    columns = [
                        {"name": "name", "label": "Name", "field": "name", "align": "left"},
                        {
                            "name": "document_count",
                            "label": "Documents",
                            "field": "document_count",
                            "align": "left",
                        },
                        {
                            "name": "cat_count",
                            "label": "CATs",
                            "field": "cat_count",
                            "align": "left",
                        },
                        {
                            "name": "created_at",
                            "label": "Created",
                            "field": "created_at",
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
                    for c in collections:
                        rows.append(
                            {
                                "name": c["name"],
                                "document_count": c.get("document_count", 0),
                                "cat_count": c.get("cat_count", 0),
                                "created_at": datetime.fromisoformat(
                                    c["created_at"].replace("Z", "+00:00")
                                ).strftime("%Y-%m-%d"),
                                "id": c["id"],
                            }
                        )

                    def handle_delete(e):
                        collection_id = e.args["id"]
                        if ui.confirm("Are you sure you want to delete this collection?"):
                            response = api_client.delete_collection(collection_id)
                            if response.status_code == 200:
                                ui.notify("Collection deleted")
                                ui.navigate.reload()
                            else:
                                ui.notify(f"Error: {response.text}", type="negative")

                    table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")
                    table.add_slot(
                        "body-cell-actions",
                        """
                        <q-td :props="props">
                            <q-btn flat round color="negative" icon="delete" @click.stop="$emit('row-click', props.row)" />
                        </q-td>
                    """,
                    )
            else:
                ui.label("No collections yet. Create one above!")
        else:
            ui.notify(f"Error loading collections: {response.text}", type="negative")

    render_page(content)


@ui.page("/documents")
def documents_page(collection_id: str | None = None):

    if not require_auth():
        return

    def content():
        ui.label("Documents").classes("text-2xl font-bold")

        collection_response = api_client.list_collections()
        collections = (
            collection_response.json().get("collections", [])
            if collection_response.status_code == 200
            else []
        )
        collection_options = {"__all__": "All Collections"}
        collection_options.update({c["id"]: c["name"] for c in collections})

        initial_value = collection_id if collection_id else "__all__"

        selected_collection = ui.select(
            label="Filter by Collection",
            options=collection_options,
            value=initial_value,
        ).classes("w-full mb-4")
        selected_collection.on_value_change(
            lambda e: ui.navigate.to(f"/documents?collection_id={e.value}")
        )

        params = {}
        if selected_collection.value and selected_collection.value != "__all__":
            params["collection_id"] = selected_collection.value

        response = api_client.list_documents(**params)
        if response.status_code == 200:
            docs_data = response.json()
            documents = docs_data.get("documents", [])
            if documents:
                with ui.card().classes("w-full"):
                    columns = [
                        {"name": "title", "label": "Title", "field": "title", "align": "left"},
                        {
                            "name": "document_type",
                            "label": "Type",
                            "field": "document_type",
                            "align": "left",
                        },
                        {
                            "name": "created_at",
                            "label": "Created",
                            "field": "created_at",
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
                    for d in documents:
                        rows.append(
                            {
                                "title": d["title"],
                                "document_type": d["document_type"],
                                "created_at": datetime.fromisoformat(
                                    d["created_at"].replace("Z", "+00:00")
                                ).strftime("%Y-%m-%d"),
                                "id": d["id"],
                                "content": d.get("content", ""),
                            }
                        )

                    def handle_delete(e):
                        doc_id = e.args["id"]
                        if ui.confirm("Are you sure you want to delete this document?"):
                            response = api_client.delete_document(doc_id)
                            if response.status_code == 200:
                                ui.notify("Document deleted")
                                ui.navigate.reload()
                            else:
                                ui.notify(f"Error: {response.text}", type="negative")

                    def handle_edit(e):
                        doc = e.args
                        ui.navigate.to(f"/documents/{doc['id']}/edit")

                    table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")
                    table.add_slot(
                        "body-cell-actions",
                        """
                        <q-td :props="props">
                            <q-btn flat round color="negative" icon="delete" @click.stop="$emit('row-click', props.row)" />
                        </q-td>
                    """,
                    )
            else:
                ui.label("No documents yet.")
        else:
            ui.notify(f"Error loading documents: {response.text}", type="negative")

    render_page(content)


@ui.page("/documents/{doc_id}/edit")
def document_edit_page(doc_id: str):

    if not require_auth():
        return

    def content():
        response = api_client.get_document(doc_id)
        if response.status_code != 200:
            ui.notify("Document not found", type="negative")
            ui.navigate.to("/documents")
            return

        doc = response.json()

        title_input = ui.input("Title", value=doc["title"]).classes("w-full")
        doc_type_input = ui.select(
            options=["markdown", "text", "html"],
            label="Document Type",
            value=doc["document_type"],
        ).classes("w-full")
        content_input = ui.textarea("Content", value=doc.get("content", "")).classes("w-full h-64")

        with ui.row().classes("gap-2 mt-4"):

            def save_document():
                update_data = {
                    "title": title_input.value,
                    "document_type": doc_type_input.value,
                    "content": content_input.value,
                }
                response = api_client.update_document(doc_id, **update_data)
                if response.status_code == 200:
                    ui.notify("Document saved")
                    ui.navigate.to("/documents")
                else:
                    ui.notify(f"Error: {response.text}", type="negative")

            ui.button("Save", on_click=save_document).props("color=primary")
            ui.button("Cancel", on_click=lambda: ui.navigate.to("/documents")).props("flat")

    render_page(content)


@ui.page("/tokens")
def tokens_page():

    if not require_auth():
        return

    def content():
        with ui.tabs().classes("w-full") as tabs:
            pat_tab = ui.tab("Personal Access Tokens")
            cat_tab = ui.tab("Collection Access Tokens")

        with ui.tab_panels(tabs, value=pat_tab).classes("w-full"):
            with ui.tab_panel(pat_tab):
                ui.label("Personal Access Tokens").classes("text-xl font-bold mb-4")

                pat_label = ui.input("Token Label").classes("w-full")
                pat_expires = ui.input("Expires in (days, optional)").classes("w-full")

                def create_pat():
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
                        ui.notify(f"Token created: {data.get('token', 'N/A')}")
                        pat_label.set_value("")
                        pat_expires.set_value("")
                        ui.navigate.reload()
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
                                        "id": p["id"],
                                    }
                                )

                            def revoke_pat(e):
                                pat_id = e.args["id"]
                                if ui.confirm("Are you sure you want to revoke this PAT?"):
                                    response = api_client.revoke_pat(pat_id)
                                    if response.status_code == 200:
                                        ui.notify("PAT revoked")
                                        ui.navigate.reload()
                                    else:
                                        ui.notify(f"Error: {response.text}", type="negative")

                            def rotate_pat(e):
                                pat_id = e.args["id"]
                                response = api_client.rotate_pat(pat_id)
                                if response.status_code == 200:
                                    data = response.json()
                                    ui.notify(f"New token: {data.get('token', 'N/A')}")
                                    ui.navigate.reload()
                                else:
                                    ui.notify(f"Error: {response.text}", type="negative")

                            ui.table(columns=columns, rows=rows, row_key="id").classes(
                                "w-full"
                            ).add_slot(
                                "body-cell-actions",
                                """<q-td :props="props">
                                    <q-btn flat round color="warning" icon="refresh" @click.stop="$emit('row-click', props.row)" />
                                    <q-btn flat round color="negative" icon="delete" @click.stop="$emit('row-click', props.row)" />
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
                collection_options.update({c["id"]: c["name"] for c in collection_list})
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

                def create_cat():
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
                        ui.notify(f"Token created: {data.get('token', 'N/A')}")
                        cat_label.set_value("")
                        cat_expires.set_value("")
                        ui.navigate.reload()
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
                                        "id": c["id"],
                                    }
                                )

                            def revoke_cat(e):
                                cat_id = e.args["id"]
                                if ui.confirm("Are you sure you want to revoke this CAT?"):
                                    response = api_client.revoke_cat(cat_id)
                                    if response.status_code == 200:
                                        ui.notify("CAT revoked")
                                        ui.navigate.reload()
                                    else:
                                        ui.notify(f"Error: {response.text}", type="negative")

                            def rotate_cat(e):
                                cat_id = e.args["id"]
                                response = api_client.rotate_cat(cat_id)
                                if response.status_code == 200:
                                    data = response.json()
                                    ui.notify(f"New token: {data.get('token', 'N/A')}")
                                    ui.navigate.reload()
                                else:
                                    ui.notify(f"Error: {response.text}", type="negative")

                            ui.table(columns=columns, rows=rows, row_key="id").classes(
                                "w-full"
                            ).add_slot(
                                "body-cell-actions",
                                """<q-td :props="props">
                                    <q-btn flat round color="warning" icon="refresh" @click.stop="$emit('row-click', props.row)" />
                                    <q-btn flat round color="negative" icon="delete" @click.stop="$emit('row-click', props.row)" />
                                </q-td>""",
                            )
                    else:
                        ui.label("No CATs yet.")
                else:
                    ui.notify(f"Error loading CATs: {response.text}", type="negative")

    render_page(content)


def main():
    port = int(os.environ.get("PORT", 8080))
    ui.run(
        title="AI Document Memory - Dashboard",
        port=port,
        reload=False,
        show=False,
        storage_secret="ainstruct-mcp-secret-key",
        dark=True,
    )


if __name__ == "__main__":
    main()
