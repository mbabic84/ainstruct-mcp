from contextvars import ContextVar

from ..db.models import Permission, Scope

api_key_context: ContextVar[dict | None] = ContextVar("api_key_context", default=None)
user_context: ContextVar[dict | None] = ContextVar("user_context", default=None)
auth_type_context: ContextVar[str | None] = ContextVar("auth_type_context", default=None)


def set_api_key_info(info: dict):
    api_key_context.set(info)


def get_api_key_info() -> dict | None:
    return api_key_context.get()


def clear_api_key_info():
    api_key_context.set(None)


def set_user_info(info: dict):
    user_context.set(info)


def get_user_info() -> dict | None:
    return user_context.get()


def clear_user_info():
    user_context.set(None)


def set_auth_type(auth_type: str):
    auth_type_context.set(auth_type)


def get_auth_type() -> str | None:
    return auth_type_context.get()


def clear_auth_type():
    auth_type_context.set(None)


def get_current_user_id() -> str | None:
    user_info = get_user_info()
    if user_info:
        return user_info.get("id")
    api_key_info = get_api_key_info()
    if api_key_info:
        return api_key_info.get("user_id")
    return None


def has_scope(required_scope: Scope) -> bool:
    user_info = get_user_info()
    if user_info and user_info.get("is_superuser"):
        return True

    api_key_info = get_api_key_info()
    if api_key_info and api_key_info.get("is_admin"):
        return True

    user_scopes = []
    if user_info:
        user_scopes = user_info.get("scopes", [])
    elif api_key_info:
        user_scopes = api_key_info.get("scopes", [])

    return required_scope in user_scopes


def has_write_permission() -> bool:
    user_info = get_user_info()
    if user_info and user_info.get("is_superuser"):
        return True

    api_key_info = get_api_key_info()
    if api_key_info:
        if api_key_info.get("is_admin"):
            return True
        permission = api_key_info.get("permission")
        return permission == Permission.READ_WRITE

    return False


def get_auth_context() -> dict:
    user_info = get_user_info()
    api_key_info = get_api_key_info()

    if user_info:
        return {
            "id": user_info.get("id"),
            "user_id": user_info.get("id"),
            "username": user_info.get("username"),
            "email": user_info.get("email"),
            "scopes": user_info.get("scopes", []),
            "is_admin": user_info.get("is_superuser", False),
            "is_superuser": user_info.get("is_superuser", False),
            "auth_type": "jwt",
        }

    if api_key_info:
        return {
            "id": api_key_info.get("id"),
            "user_id": api_key_info.get("user_id"),
            "collection_id": api_key_info.get("collection_id"),
            "collection_name": api_key_info.get("collection_name"),
            "qdrant_collection": api_key_info.get("qdrant_collection"),
            "permission": api_key_info.get("permission"),
            "is_admin": api_key_info.get("is_admin", False),
            "is_superuser": False,
            "auth_type": "api_key",
        }

    return {}


def is_authenticated() -> bool:
    return bool(get_user_info() or get_api_key_info())


def clear_all_auth():
    clear_api_key_info()
    clear_user_info()
    clear_auth_type()
