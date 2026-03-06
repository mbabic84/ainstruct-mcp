from nicegui import app, ui

from web_ui.api_client import API_HOSTNAME, ApiClient

api_client = ApiClient(hostname=API_HOSTNAME)


async def set_api_origin():
    try:
        origin = await ui.run_javascript("window.location.origin")
        if origin:
            ApiClient.set_cached_origin(origin)
    except TimeoutError:
        pass


async def load_tokens_from_storage():
    await set_api_origin()

    try:
        access_token = await ui.run_javascript("localStorage.getItem('access_token')")
        refresh_token = await ui.run_javascript("localStorage.getItem('refresh_token')")
        if access_token:
            api_client.set_tokens(access_token, refresh_token)

        await ui.run_javascript("window.__forceRefreshToken()")

        access_token = await ui.run_javascript("localStorage.getItem('access_token')")
        if access_token:
            api_client.set_tokens(access_token, refresh_token)
            profile_response = api_client.get_profile()
            if profile_response.status_code == 200:
                profile = profile_response.json()
                app.storage.user["is_superuser"] = profile.get("is_superuser", False)
    except TimeoutError:
        pass


async def save_tokens_to_storage(access_token: str, refresh_token: str):
    try:
        await ui.run_javascript(f"localStorage.setItem('access_token', '{access_token}')")
        await ui.run_javascript(f"localStorage.setItem('refresh_token', '{refresh_token}')")
    except TimeoutError:
        pass


async def clear_tokens_from_storage():
    try:
        await ui.run_javascript("localStorage.removeItem('access_token')")
        await ui.run_javascript("localStorage.removeItem('refresh_token')")
    except TimeoutError:
        pass


def get_user():
    return None


def is_logged_in():
    return bool(api_client.access_token)


def is_admin():
    return app.storage.user.get("is_superuser", False)


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
    await clear_tokens_from_storage()
    ui.navigate.to("/login")


async def login_user(username: str, password: str) -> tuple[bool, str]:
    response = api_client.login(username, password)
    if response.status_code == 200:
        data = response.json()
        api_client.set_tokens(data["access_token"], data["refresh_token"])
        await save_tokens_to_storage(data["access_token"], data["refresh_token"])
        profile_response = api_client.get_profile()
        if profile_response.status_code == 200:
            profile = profile_response.json()
            app.storage.user["is_superuser"] = profile.get("is_superuser", False)
        return True, ""
    elif response.status_code == 401:
        return False, "Invalid username or password"
    elif response.status_code == 403:
        return False, "Account is disabled"
    else:
        return False, f"Login failed: {response.status_code}"


async def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
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


def get_api_client() -> ApiClient:
    return api_client
