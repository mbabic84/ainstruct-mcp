from nicegui import APIRouter, ui
from shared.config import settings

from web_ui.auth import load_tokens_from_storage, require_admin
from web_ui.components import (
    add_table_action_buttons,
    build_sort_url,
    create_sort_handler,
    create_table_pagination,
    make_columns_sortable,
    render_page,
)
from web_ui.utils import format_date, handle_api_error

router = APIRouter(prefix="")


@router.page("/admin")
async def admin_page(offset: int = 0, sort_by: str = "", sort_desc: bool = False):
    await load_tokens_from_storage()

    if not require_admin():
        return

    limit = settings.web_records_per_page

    def content():
        from web_ui.auth import get_api_client

        api_client = get_api_client()

        ui.label("User Administration").classes("text-2xl font-bold mb-4")

        user_count_label = ui.label("").classes("text-sm text-grey-7")
        pagination_label = ui.label("").classes("text-sm text-grey-7")

        with ui.dialog() as stats_dialog, ui.card().classes("w-[400px]"):
            stats_user_label = ui.label("").classes("text-xl font-bold")
            with ui.row().classes("w-full gap-4 mt-4"):
                stats_collections = ui.label("").classes("text-lg")
                stats_pats = ui.label("").classes("text-lg")
                stats_cats = ui.label("").classes("text-lg")

        async def show_user_stats(user_id: int, username: str):
            response = api_client.get_user(str(user_id))
            if response.status_code == 200:
                user = response.json()
                stats_user_label.set_text(f"User: {username}")
                stats_collections.set_text(f"Collections: {user.get('collection_count', 0)}")
                stats_pats.set_text(f"PATs: {user.get('pat_count', 0)}")
                stats_cats.set_text(f"CATs: {user.get('cat_count', 0)}")
                stats_dialog.open()
            else:
                ui.notify(f"Error loading user stats: {response.text}", type="negative")

        async def toggle_active(user_id: int, current_active: bool):
            response = api_client.update_user(str(user_id), is_active=not current_active)
            if handle_api_error(response, "Failed to update user"):
                ui.notify(f"User {'activated' if not current_active else 'deactivated'}")
                ui.navigate.reload()

        async def toggle_superuser(user_id: int, current_superuser: bool):
            response = api_client.update_user(str(user_id), is_superuser=not current_superuser)
            if handle_api_error(response, "Failed to update user"):
                ui.notify(
                    f"User {'promoted to' if not current_superuser else 'demoted from'} superuser"
                )
                ui.navigate.reload()

        async def delete_user(user_id: int, username: str):
            response = api_client.delete_user(str(user_id))
            if handle_api_error(response, "Failed to delete user"):
                ui.notify(f"User '{username}' deleted successfully", type="positive")
                ui.navigate.reload()

        columns = make_columns_sortable(
            [
                {"name": "username", "label": "Username", "field": "username", "align": "left"},
                {"name": "email", "label": "Email", "field": "email", "align": "left"},
                {"name": "is_active", "label": "Status", "field": "is_active", "align": "center"},
                {
                    "name": "is_superuser",
                    "label": "Role",
                    "field": "is_superuser",
                    "align": "center",
                },
                {"name": "created_at", "label": "Created", "field": "created_at", "align": "left"},
                {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
            ]
        )

        pagination = {"rowsPerPage": limit, **create_table_pagination(sort_by, sort_desc)}

        rows = []
        total = 0
        current_offset = offset

        response = api_client.list_users(limit=limit, offset=offset)
        if response.status_code == 200:
            data = response.json()
            users = data.get("users", [])
            total = data.get("total", 0)
            current_offset = data.get("offset", 0)

            user_count_label.set_text(f"Total users: {total}")

            for u in users:
                rows.append(
                    {
                        "id": u["user_id"],
                        "username": u["username"],
                        "email": u.get("email", ""),
                        "is_active": u.get("is_active", True),
                        "is_superuser": u.get("is_superuser", False),
                        "created_at": format_date(u.get("created_at")),
                    }
                )

            def handle_stats(item):
                user_id = item["id"]
                username = item.get("label", "")
                return show_user_stats(user_id, username)

            def handle_toggle_active(item):
                user_id = item["id"]
                is_active = item.get("is_active", True)
                return toggle_active(user_id, is_active)

            def handle_toggle_superuser(item):
                user_id = item["id"]
                is_superuser = item.get("is_superuser", False)
                return toggle_superuser(user_id, is_superuser)

            def handle_delete_user(item):
                user_id = item["id"]
                username = item.get("username", "")
                return delete_user(user_id, username)

            table = ui.table(
                columns=columns, rows=rows, row_key="id", pagination=pagination
            ).classes("w-full")

            table.on(
                "update:pagination",
                create_sort_handler(
                    "/admin", lambda: {"offset": current_offset}, sort_by, sort_desc
                ),
            )

            table.add_slot(
                "body-cell-is_active",
                """<q-td :props="props">
                    <q-badge :color="props.value ? 'positive' : 'negative'">
                        {{ props.value ? 'Active' : 'Inactive' }}
                    </q-badge>
                </q-td>""",
            )

            table.add_slot(
                "body-cell-is_superuser",
                """<q-td :props="props">
                    <q-badge :color="props.value ? 'purple' : 'grey'">
                        {{ props.value ? 'Superuser' : 'User' }}
                    </q-badge>
                </q-td>""",
            )

            add_table_action_buttons(
                table,
                "actions",
                [
                    {
                        "icon": "analytics",
                        "color": "primary",
                        "on_click": handle_stats,
                        "label_field": "username",
                    },
                    {
                        "icon": "block",
                        "color": "warning",
                        "on_click": handle_toggle_active,
                        "label_field": "username",
                        "extra_fields": {"is_active": "is_active"},
                        "confirm": True,
                        "confirm_message": "This will change {name} active status.",
                        "confirm_label": "Toggle Status",
                    },
                    {
                        "icon": "admin_panel_settings",
                        "color": "purple",
                        "on_click": handle_toggle_superuser,
                        "label_field": "username",
                        "extra_fields": {"is_superuser": "is_superuser"},
                        "confirm": True,
                        "confirm_message": "This will change {name} superuser privileges.",
                        "confirm_label": "Change Role",
                    },
                    {
                        "icon": "delete",
                        "color": "negative",
                        "on_click": handle_delete_user,
                        "label_field": "username",
                        "confirm": True,
                        "confirm_message": "This will permanently delete user '{name}'. This action cannot be undone.",
                        "confirm_label": "Delete User",
                    },
                ],
            )

            current_page = (current_offset // limit) + 1
            total_pages = (total + limit - 1) // limit
            pagination_label.set_text(f"Page {current_page} of {total_pages}")

            with ui.row().classes("w-full justify-center gap-2 mt-4"):
                if current_offset > 0:
                    ui.button(
                        "Previous",
                        on_click=lambda: ui.navigate.to(
                            build_sort_url(
                                "/admin",
                                sort_by,
                                sort_desc,
                                {"offset": max(0, current_offset - limit)},
                            )
                        ),
                    ).props("flat")
                if current_offset + limit < total:
                    ui.button(
                        "Next",
                        on_click=lambda: ui.navigate.to(
                            build_sort_url(
                                "/admin", sort_by, sort_desc, {"offset": current_offset + limit}
                            )
                        ),
                    ).props("flat")
        else:
            ui.notify(f"Error loading users: {response.text}", type="negative")

    render_page(content)
