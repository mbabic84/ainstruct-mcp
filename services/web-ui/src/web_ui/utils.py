from datetime import UTC, datetime


def format_date(iso_str: str | None) -> str:
    if not iso_str:
        return ""
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")


def format_time_remaining(iso_str: str | None) -> str:
    if not iso_str:
        return "Never"
    try:
        expires_at = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        now = datetime.now(UTC)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        delta = expires_at - now
        if delta.total_seconds() <= 0:
            return "Expired"
        total_seconds = int(delta.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        if days >= 30:
            months = days // 30
            return f"in {months} month" if months == 1 else f"in {months} months"
        if days > 0:
            return f"in {days} day" if days == 1 else f"in {days} days"
        if hours > 0:
            return f"in {hours} hour" if hours == 1 else f"in {hours} hours"
        if minutes > 0:
            return f"in {minutes} minute" if minutes == 1 else f"in {minutes} minutes"
        return "in less than a minute"
    except ValueError, OSError:
        return "Invalid"


def handle_api_error(response, default_msg: str = "An error occurred") -> bool:
    from nicegui import ui

    if response.status_code >= 200 and response.status_code < 300:
        return True
    ui.notify(f"Error: {response.text}", type="negative")
    return False
