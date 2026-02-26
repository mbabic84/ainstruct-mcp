from contextvars import ContextVar

from ..db.models import Permission, Scope

cat_context: ContextVar[dict | None] = ContextVar("cat_context", default=None)
user_context: ContextVar[dict | None] = ContextVar("user_context", default=None)
auth_type_context: ContextVar[str | None] = ContextVar("auth_type_context", default=None)
pat_context: ContextVar[dict | None] = ContextVar("pat_context", default=None)


def set_pat_info(info: dict):
    pat_context.set(info)


def get_pat_info() -> dict | None:
    return pat_context.get()


def clear_pat_info():
    pat_context.set(None)


def set_cat_info(info: dict):
    cat_context.set(info)


def get_cat_info() -> dict | None:
    return cat_context.get()


def clear_cat_info():
    cat_context.set(None)


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
    cat_info = get_cat_info()
    if cat_info:
        return cat_info.get("user_id")
    pat_info = get_pat_info()
    if pat_info:
        return pat_info.get("user_id")
    return None


def has_scope(required_scope: Scope) -> bool:
    user_info = get_user_info()
    if user_info and user_info.get("is_superuser"):
        return True

    cat_info = get_cat_info()
    if cat_info and cat_info.get("is_admin"):
        return True

    pat_info = get_pat_info()
    if pat_info and pat_info.get("is_superuser"):
        return True

    user_scopes = []
    if user_info:
        user_scopes = user_info.get("scopes", [])
    elif cat_info:
        user_scopes = cat_info.get("scopes", [])
    elif pat_info:
        user_scopes = pat_info.get("scopes", [])

    return required_scope in user_scopes


def has_write_permission() -> bool:
    user_info = get_user_info()
    if user_info:
        if user_info.get("is_superuser"):
            return True
        return True

    cat_info = get_cat_info()
    if cat_info:
        if cat_info.get("is_admin"):
            return True
        permission = cat_info.get("permission")
        return permission == Permission.READ_WRITE

    pat_info = get_pat_info()
    if pat_info:
        if pat_info.get("is_superuser"):
            return True
        scopes = pat_info.get("scopes", [])
        return Scope.WRITE in scopes

    return False


def get_collection_repository():
    from ..db.repository import get_collection_repository as _get_collection_repo
    return _get_collection_repo()


def get_auth_context() -> dict:
    import asyncio

    user_info = get_user_info()
    cat_info = get_cat_info()
    pat_info = get_pat_info()

    if user_info:
        collection_repo = get_collection_repository()
        user_id = user_info.get("id")
        user_collections = asyncio.get_event_loop().run_until_complete(
            collection_repo.list_by_user(user_id)
        ) if user_id else []

        return {
            "id": user_info.get("id"),
            "user_id": user_info.get("id"),
            "username": user_info.get("username"),
            "email": user_info.get("email"),
            "scopes": user_info.get("scopes", []),
            "is_admin": user_info.get("is_superuser", False),
            "is_superuser": user_info.get("is_superuser", False),
            "auth_type": "jwt",
            "collection_ids": [c["id"] for c in user_collections],
            "qdrant_collections": [c["qdrant_collection"] for c in user_collections],
        }

    if pat_info:
        collection_repo = get_collection_repository()
        user_id = pat_info.get("user_id")
        user_collections = asyncio.get_event_loop().run_until_complete(
            collection_repo.list_by_user(user_id)
        ) if user_id else []

        return {
            "id": pat_info.get("id"),
            "user_id": pat_info.get("user_id"),
            "username": pat_info.get("username"),
            "email": pat_info.get("email"),
            "scopes": pat_info.get("scopes", []),
            "is_admin": pat_info.get("is_superuser", False),
            "is_superuser": pat_info.get("is_superuser", False),
            "auth_type": "pat",
            "collection_ids": [c["id"] for c in user_collections],
            "qdrant_collections": [c["qdrant_collection"] for c in user_collections],
        }

    if cat_info:
        return {
            "id": cat_info.get("id"),
            "user_id": cat_info.get("user_id"),
            "collection_id": cat_info.get("collection_id"),
            "collection_name": cat_info.get("collection_name"),
            "qdrant_collection": cat_info.get("qdrant_collection"),
            "permission": cat_info.get("permission"),
            "is_admin": cat_info.get("is_admin", False),
            "is_superuser": False,
            "auth_type": "cat",
        }

    return {}


def is_authenticated() -> bool:
    return bool(get_user_info() or get_cat_info() or get_pat_info())


def clear_all_auth():
    clear_cat_info()
    clear_user_info()
    clear_pat_info()
    clear_auth_type()
