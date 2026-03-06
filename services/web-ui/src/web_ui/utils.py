from datetime import datetime


def format_date(iso_str: str | None) -> str:
    if not iso_str:
        return ""
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).strftime("%Y-%m-%d")


def handle_api_error(response, default_msg: str = "An error occurred") -> bool:
    from nicegui import ui

    if response.status_code >= 200 and response.status_code < 300:
        return True
    ui.notify(f"Error: {response.text}", type="negative")
    return False
