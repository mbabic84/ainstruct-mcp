import os

import httpx

API_HOSTNAME = os.environ.get("API_HOSTNAME")


class ApiClient:
    _cached_origin: str | None = None

    def __init__(self, hostname: str | None = None):
        self._hostname = hostname or API_HOSTNAME
        self._client = httpx.Client(timeout=30.0)
        self.access_token: str | None = None
        self.refresh_token: str | None = None

    @classmethod
    def set_cached_origin(cls, origin: str):
        cls._cached_origin = origin

    @property
    def hostname(self) -> str | None:
        return self._hostname

    @hostname.setter
    def hostname(self, value: str | None):
        self._hostname = value

    def _get_url(self, path: str) -> str:
        if self._hostname:
            return f"{self._hostname}{path}"
        if self._cached_origin:
            return f"{self._cached_origin}{path}"
        raise RuntimeError(
            "API_HOSTNAME not set and browser origin not available. "
            "Ensure the page has loaded before making API calls."
        )

    def set_tokens(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token

    def clear_tokens(self):
        self.access_token = None
        self.refresh_token = None

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        params: dict | None = None,
        _retry: bool = False,
    ) -> httpx.Response:
        url = self._get_url(path)
        response = self._client.request(
            method=method,
            url=url,
            json=json,
            params=params,
            headers=self._get_headers(),
        )
        return response

    def register(self, username: str, email: str, password: str) -> httpx.Response:
        return self._request(
            "POST",
            "/api/v1/auth/register",
            json={"username": username, "email": email, "password": password},
        )

    def login(self, username: str, password: str) -> httpx.Response:
        return self._request(
            "POST",
            "/api/v1/auth/login",
            json={"username": username, "password": password},
        )

    def refresh(self, refresh_token: str) -> httpx.Response:
        return self._request(
            "POST",
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

    def get_profile(self) -> httpx.Response:
        return self._request("GET", "/api/v1/auth/profile")

    def list_collections(self) -> httpx.Response:
        return self._request("GET", "/api/v1/collections")

    def create_collection(self, name: str) -> httpx.Response:
        return self._request("POST", "/api/v1/collections", json={"name": name})

    def get_collection(self, collection_id: str) -> httpx.Response:
        return self._request("GET", f"/api/v1/collections/{collection_id}")

    def rename_collection(self, collection_id: str, name: str) -> httpx.Response:
        return self._request("PATCH", f"/api/v1/collections/{collection_id}", json={"name": name})

    def delete_collection(self, collection_id: str) -> httpx.Response:
        return self._request("DELETE", f"/api/v1/collections/{collection_id}")

    def list_documents(
        self, collection_id: str | None = None, limit: int = 50, offset: int = 0
    ) -> httpx.Response:
        params: dict = {"limit": limit, "offset": offset}
        if collection_id:
            params["collection_id"] = collection_id
        return self._request("GET", "/api/v1/documents", params=params)

    def create_document(
        self,
        title: str,
        content: str,
        collection_id: str,
        document_type: str = "markdown",
        metadata: dict | None = None,
    ) -> httpx.Response:
        return self._request(
            "POST",
            "/api/v1/documents",
            json={
                "title": title,
                "content": content,
                "collection_id": collection_id,
                "document_type": document_type,
                "metadata": metadata,
            },
        )

    def get_document(self, document_id: str) -> httpx.Response:
        return self._request("GET", f"/api/v1/documents/{document_id}")

    def update_document(
        self,
        document_id: str,
        title: str | None = None,
        content: str | None = None,
        document_type: str | None = None,
        metadata: dict | None = None,
    ) -> httpx.Response:
        body: dict = {}
        if title is not None:
            body["title"] = title
        if content is not None:
            body["content"] = content
        if document_type is not None:
            body["document_type"] = document_type
        if metadata is not None:
            body["metadata"] = metadata
        return self._request("PATCH", f"/api/v1/documents/{document_id}", json=body)

    def delete_document(self, document_id: str) -> httpx.Response:
        return self._request("DELETE", f"/api/v1/documents/{document_id}")

    def list_pats(self) -> httpx.Response:
        return self._request("GET", "/api/v1/auth/pat")

    def create_pat(self, label: str, expires_in_days: int | None = None) -> httpx.Response:
        body: dict = {"label": label}
        if expires_in_days is not None:
            body["expires_in_days"] = expires_in_days
        return self._request("POST", "/api/v1/auth/pat", json=body)

    def revoke_pat(self, pat_id: str) -> httpx.Response:
        return self._request("DELETE", f"/api/v1/auth/pat/{pat_id}")

    def rotate_pat(self, pat_id: str) -> httpx.Response:
        return self._request("POST", f"/api/v1/auth/pat/{pat_id}/rotate")

    def list_cats(self, collection_id: str | None = None) -> httpx.Response:
        params: dict = {}
        if collection_id:
            params["collection_id"] = collection_id
        return self._request("GET", "/api/v1/auth/cat", params=params)

    def create_cat(
        self,
        label: str,
        collection_id: str,
        permission: str = "read_write",
        expires_in_days: int | None = None,
    ) -> httpx.Response:
        body: dict = {
            "label": label,
            "collection_id": collection_id,
            "permission": permission,
        }
        if expires_in_days is not None:
            body["expires_in_days"] = expires_in_days
        return self._request("POST", "/api/v1/auth/cat", json=body)

    def revoke_cat(self, cat_id: str) -> httpx.Response:
        return self._request("DELETE", f"/api/v1/auth/cat/{cat_id}")

    def rotate_cat(self, cat_id: str) -> httpx.Response:
        return self._request("POST", f"/api/v1/auth/cat/{cat_id}/rotate")

    def list_users(self, limit: int = 50, offset: int = 0) -> httpx.Response:
        return self._request(
            "GET", "/api/v1/admin/users", params={"limit": limit, "offset": offset}
        )

    def get_user(self, user_id: str) -> httpx.Response:
        return self._request("GET", f"/api/v1/admin/users/{user_id}")

    def update_user(
        self,
        user_id: str,
        email: str | None = None,
        username: str | None = None,
        password: str | None = None,
        is_active: bool | None = None,
        is_superuser: bool | None = None,
    ) -> httpx.Response:
        body: dict = {}
        if email is not None:
            body["email"] = email
        if username is not None:
            body["username"] = username
        if password is not None:
            body["password"] = password
        if is_active is not None:
            body["is_active"] = is_active
        if is_superuser is not None:
            body["is_superuser"] = is_superuser
        return self._request("PATCH", f"/api/v1/admin/users/{user_id}", json=body)

    def delete_user(self, user_id: str) -> httpx.Response:
        return self._request("DELETE", f"/api/v1/admin/users/{user_id}")

    def close(self):
        self._client.close()
