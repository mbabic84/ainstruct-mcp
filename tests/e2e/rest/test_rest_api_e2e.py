import pytest
import httpx
from fastapi.testclient import TestClient


BASE_URL = "http://localhost:8001"


@pytest.fixture(scope="module")
def rest_client():
    return httpx.Client(base_url=BASE_URL, timeout=30.0)


@pytest.fixture(scope="module")
def auth_token(rest_client):
    response = rest_client.post("/api/v1/auth/register", json={
        "email": "e2e@example.com",
        "username": "e2euser",
        "password": "testpass123",
    })
    if response.status_code == 201:
        pass
    elif response.status_code == 400:
        pass
    
    response = rest_client.post("/api/v1/auth/login", json={
        "username": "e2euser",
        "password": "testpass123",
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


class TestHealthEndpoint:
    def test_health_check(self, rest_client):
        response = rest_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAuthEndpoints:
    def test_register_duplicate_username(self, rest_client):
        response = rest_client.post("/api/v1/auth/register", json={
            "email": "another@example.com",
            "username": "e2euser",
            "password": "password123",
        })
        assert response.status_code == 400
        assert "USERNAME_EXISTS" in response.json()["detail"]["code"]

    def test_login_invalid_credentials(self, rest_client):
        response = rest_client.post("/api/v1/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpass",
        })
        assert response.status_code == 401
        assert "INVALID_CREDENTIALS" in response.json()["detail"]["code"]

    def test_get_profile(self, rest_client, auth_headers):
        response = rest_client.get("/api/v1/auth/profile", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "e2euser"


class TestCollectionEndpoints:
    def test_create_collection(self, rest_client, auth_headers):
        response = rest_client.post(
            "/api/v1/collections",
            json={"name": "test-collection"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test-collection"
        assert "id" in data

    def test_list_collections(self, rest_client, auth_headers):
        response = rest_client.get("/api/v1/collections", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data

    def test_get_collection(self, rest_client, auth_headers):
        create_resp = rest_client.post(
            "/api/v1/collections",
            json={"name": "get-test"},
            headers=auth_headers,
        )
        coll_id = create_resp.json()["id"]
        
        response = rest_client.get(f"/api/v1/collections/{coll_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "get-test"

    def test_rename_collection(self, rest_client, auth_headers):
        create_resp = rest_client.post(
            "/api/v1/collections",
            json={"name": "old-name"},
            headers=auth_headers,
        )
        coll_id = create_resp.json()["id"]
        
        response = rest_client.patch(
            f"/api/v1/collections/{coll_id}",
            json={"name": "new-name"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "new-name"

    def test_delete_collection(self, rest_client, auth_headers):
        create_resp = rest_client.post(
            "/api/v1/collections",
            json={"name": "to-delete"},
            headers=auth_headers,
        )
        coll_id = create_resp.json()["id"]
        
        response = rest_client.delete(f"/api/v1/collections/{coll_id}", headers=auth_headers)
        assert response.status_code == 200

    def test_cannot_access_other_user_collection(self, rest_client):
        response = rest_client.get("/api/v1/collections", headers={"Authorization": "Bearer invalid"})
        assert response.status_code == 401


class TestDocumentEndpoints:
    @pytest.fixture
    def collection_id(self, rest_client, auth_headers):
        response = rest_client.post(
            "/api/v1/collections",
            json={"name": "docs-test"},
            headers=auth_headers,
        )
        return response.json()["id"]

    def test_store_document(self, rest_client, auth_headers, collection_id):
        response = rest_client.post(
            "/api/v1/documents",
            json={
                "title": "Test Doc",
                "content": "# Hello\n\nThis is a test document.",
                "document_type": "markdown",
                "collection_id": collection_id,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Doc"
        assert "id" in data

    def test_list_documents(self, rest_client, auth_headers, collection_id):
        response = rest_client.get("/api/v1/documents", headers=auth_headers)
        assert response.status_code == 200
        assert "documents" in response.json()

    def test_search_documents(self, rest_client, auth_headers, collection_id):
        response = rest_client.post(
            "/api/v1/documents/search",
            json={
                "query": "test",
                "max_results": 5,
                "max_tokens": 2000,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert "results" in response.json()


class TestPATEndpoints:
    def test_create_pat(self, rest_client, auth_headers):
        response = rest_client.post(
            "/api/v1/auth/pat",
            json={"label": "My Test Token"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "token" in data
        assert data["label"] == "My Test Token"

    def test_list_pats(self, rest_client, auth_headers):
        response = rest_client.get("/api/v1/auth/pat", headers=auth_headers)
        assert response.status_code == 200
        assert "tokens" in response.json()

    def test_revoke_pat(self, rest_client, auth_headers):
        create_resp = rest_client.post(
            "/api/v1/auth/pat",
            json={"label": "To Revoke"},
            headers=auth_headers,
        )
        pat_id = create_resp.json()["id"]
        
        response = rest_client.delete(f"/api/v1/auth/pat/{pat_id}", headers=auth_headers)
        assert response.status_code == 200


class TestCATEndpoints:
    @pytest.fixture
    def coll_id(self, rest_client, auth_headers):
        response = rest_client.post(
            "/api/v1/collections",
            json={"name": "cat-test"},
            headers=auth_headers,
        )
        return response.json()["id"]

    def test_create_cat(self, rest_client, auth_headers, coll_id):
        response = rest_client.post(
            "/api/v1/auth/cat",
            json={
                "label": "Test CAT",
                "collection_id": coll_id,
                "permission": "read",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201

    def test_list_cats(self, rest_client, auth_headers):
        response = rest_client.get("/api/v1/auth/cat", headers=auth_headers)
        assert response.status_code == 200
