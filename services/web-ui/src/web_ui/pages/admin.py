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

        with ui.dialog() as stats_dialog, ui.card().classes("w-[700px]"):
            with ui.row().classes("w-full items-center justify-between"):
                stats_user_label = ui.label("").classes("text-xl font-bold")
                stats_status_badge = ui.badge("").props("color='positive'")
            with ui.grid().classes("w-full grid-cols-2 gap-6 mt-4"):
                with ui.column().classes("gap-2"):
                    ui.label("Resources").classes("text-lg font-semibold")
                    stats_collections = ui.label("").classes("text-base")
                    stats_documents = ui.label("").classes("text-base")
                    stats_pats = ui.label("").classes("text-base")
                    stats_cats = ui.label("").classes("text-base")
                with ui.column().classes("gap-2"):
                    ui.label("This Month's Usage").classes("text-lg font-semibold")
                    with ui.row().classes("w-full gap-2"):
                        stats_api_card = ui.card().classes("flex-1 p-2 text-center")
                        with stats_api_card:
                            stats_api_label = ui.label("").classes("text-2xl font-bold")
                            ui.label("API").classes("text-xs text-grey-7")
                        stats_mcp_card = ui.card().classes("flex-1 p-2 text-center")
                        with stats_mcp_card:
                            stats_mcp_label = ui.label("").classes("text-2xl font-bold")
                            ui.label("MCP").classes("text-xs text-grey-7")
                        stats_total_card = ui.card().classes("flex-1 p-2 text-center")
                        with stats_total_card:
                            stats_total_label = ui.label("").classes("text-2xl font-bold")
                            ui.label("Total").classes("text-xs text-grey-7")
                    ui.label("History").classes("text-lg font-semibold mt-2")
                    history_table = ui.table(
                        columns=[
                            {"name": "month", "label": "Month", "field": "month", "align": "left"},
                            {"name": "api", "label": "API", "field": "api", "align": "center"},
                            {"name": "mcp", "label": "MCP", "field": "mcp", "align": "center"},
                            {
                                "name": "total",
                                "label": "Total",
                                "field": "total",
                                "align": "center",
                            },
                        ],
                        rows=[],
                        row_key="month",
                    ).classes("w-full")

        async def show_user_stats(user_id: int, username: str, is_active: bool = True):
            response = api_client.get_user(str(user_id))
            if response.status_code == 200:
                user = response.json()
                stats_user_label.set_text(f"👤 {username}")
                stats_status_badge.set_text("Active" if is_active else "Inactive")
                stats_status_badge.props(f"color={'positive' if is_active else 'negative'}")
                stats_collections.set_text(f"📁 Collections: {user.get('collection_count', 0)}")
                stats_documents.set_text(f"📄 Documents: {user.get('document_count', 0)}")
                pat_active = user.get("pat_active_count", 0)
                pat_inactive = user.get("pat_inactive_count", 0)
                stats_pats.set_text(f"🔑 PATs: {pat_active} active, {pat_inactive} inactive")
                cat_active = user.get("cat_active_count", 0)
                cat_inactive = user.get("cat_inactive_count", 0)
                stats_cats.set_text(f"🔐 CATs: {cat_active} active, {cat_inactive} inactive")

                usage_response = api_client.get_user_usage(str(user_id))
                if usage_response.status_code == 200:
                    usage = usage_response.json()
                    stats_api_label.set_text(str(usage.get("api_requests", 0)))
                    stats_mcp_label.set_text(str(usage.get("mcp_requests", 0)))
                    stats_total_label.set_text(str(usage.get("total_requests", 0)))
                else:
                    stats_api_label.set_text("0")
                    stats_mcp_label.set_text("0")
                    stats_total_label.set_text("0")

                history_response = api_client.get_user_usage_history(str(user_id), months=6)
                if history_response.status_code == 200:
                    history_data = history_response.json()
                    history_rows = [
                        {
                            "month": h.get("year_month", ""),
                            "api": h.get("api_requests", 0),
                            "mcp": h.get("mcp_requests", 0),
                            "total": h.get("total", 0),
                        }
                        for h in history_data.get("history", [])
                    ]
                    history_table.update_rows(history_rows)
                else:
                    history_table.update_rows([])

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
                username = item.get("username", "")
                is_active = item.get("is_active", True)
                return show_user_stats(user_id, username, is_active)

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
