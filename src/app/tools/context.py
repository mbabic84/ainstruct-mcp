from contextvars import ContextVar
from typing import Optional

api_key_context: ContextVar[Optional[dict]] = ContextVar("api_key_context", default=None)


def set_api_key_info(info: dict):
    api_key_context.set(info)


def get_api_key_info() -> Optional[dict]:
    return api_key_context.get()


def clear_api_key_info():
    api_key_context.set(None)
