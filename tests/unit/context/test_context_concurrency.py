"""
Concurrency and isolation tests for auth context variables.
Tests that context vars are properly isolated between concurrent requests.
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch

from app.tools.context import (
    set_user_info,
    get_user_info,
    clear_all_auth,
    set_api_key_info,
    get_api_key_info,
    set_pat_info,
    get_pat_info,
    get_current_user_id,
)
from app.db.models import Scope, Permission


@pytest.fixture
def mock_user_info_1():
    return {
        "id": "user-1",
        "username": "user1",
        "email": "user1@example.com",
        "is_superuser": False,
        "scopes": [Scope.READ, Scope.WRITE],
    }


@pytest.fixture
def mock_user_info_2():
    return {
        "id": "user-2",
        "username": "user2",
        "email": "user2@example.com",
        "is_superuser": True,
        "scopes": [Scope.ADMIN],
    }


@pytest.fixture
def mock_api_key_info():
    return {
        "id": "api-key-1",
        "user_id": "user-api-1",
        "collection_id": "collection-1",
        "permission": Permission.READ_WRITE,
        "is_admin": False,
        "auth_type": "api_key",
    }


@pytest.fixture
def mock_pat_info():
    return {
        "id": "pat-1",
        "user_id": "user-pat-1",
        "username": "patuser",
        "email": "pat@example.com",
        "scopes": [Scope.READ, Scope.WRITE],
        "is_superuser": False,
    }


class TestContextIsolation:
    """Test that context variables are isolated between async tasks."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    @pytest.mark.asyncio
    async def test_concurrent_user_contexts(self, mock_user_info_1, mock_user_info_2):
        """
        Concurrent async tasks with different user contexts should not interfere.
        Context vars should be task-local.
        """
        async def task1():
            set_user_info(mock_user_info_1)
            await asyncio.sleep(0.01)  # Allow context switch
            return get_user_info()

        async def task2():
            set_user_info(mock_user_info_2)
            await asyncio.sleep(0.01)
            return get_user_info()

        results = await asyncio.gather(task1(), task2())

        # Each task should see its own context
        assert results[0]["id"] == "user-1"
        assert results[1]["id"] == "user-2"

        # Main context should be clean (no auth)
        assert get_user_info() is None

    @pytest.mark.asyncio
    async def test_concurrent_api_key_contexts(self, mock_api_key_info):
        """Concurrent API key contexts should be isolated."""
        api_key_info_2 = mock_api_key_info.copy()
        api_key_info_2["user_id"] = "user-api-2"

        async def task1():
            set_api_key_info(mock_api_key_info)
            await asyncio.sleep(0.01)
            return get_api_key_info()

        async def task2():
            set_api_key_info(api_key_info_2)
            await asyncio.sleep(0.01)
            return get_api_key_info()

        results = await asyncio.gather(task1(), task2())

        assert results[0]["user_id"] == "user-api-1"
        assert results[1]["user_id"] == "user-api-2"

        assert get_api_key_info() is None

    @pytest.mark.asyncio
    async def test_concurrent_pat_contexts(self, mock_pat_info):
        """Concurrent PAT contexts should be isolated."""
        pat_info_2 = mock_pat_info.copy()
        pat_info_2["user_id"] = "user-pat-2"

        async def task1():
            set_pat_info(mock_pat_info)
            await asyncio.sleep(0.01)
            return get_pat_info()

        async def task2():
            set_pat_info(pat_info_2)
            await asyncio.sleep(0.01)
            return get_pat_info()

        results = await asyncio.gather(task1(), task2())

        assert results[0]["user_id"] == "user-pat-1"
        assert results[1]["user_id"] == "user-pat-2"

        assert get_pat_info() is None

    @pytest.mark.asyncio
    async def test_concurrent_mixed_auth_types(self, mock_user_info_1, mock_api_key_info):
        """Concurrent requests with different auth types (JWT vs API key) should not mix."""
        async def jwt_task():
            set_user_info(mock_user_info_1)
            await asyncio.sleep(0.01)
            return get_user_info()

        async def api_key_task():
            set_api_key_info(mock_api_key_info)
            await asyncio.sleep(0.01)
            return get_api_key_info()

        results = await asyncio.gather(jwt_task(), api_key_task())

        assert results[0]["id"] == "user-1"
        assert results[1]["user_id"] == "user-api-1"

        assert get_user_info() is None
        assert get_api_key_info() is None

    @pytest.mark.asyncio
    async def test_concurrent_get_current_user_id(self, mock_user_info_1, mock_api_key_info, mock_pat_info):
        """get_current_user_id should return correct ID based on active auth context."""
        async def user_task():
            set_user_info(mock_user_info_1)
            await asyncio.sleep(0.01)
            return get_current_user_id()

        async def api_key_task():
            set_api_key_info(mock_api_key_info)
            await asyncio.sleep(0.01)
            return get_current_user_id()

        async def pat_task():
            set_pat_info(mock_pat_info)
            await asyncio.sleep(0.01)
            return get_current_user_id()

        results = await asyncio.gather(user_task(), api_key_task(), pat_task())

        assert results[0] == "user-1"
        assert results[1] == "user-api-1"
        assert results[2] == "user-pat-1"

        assert get_current_user_id() is None

    @pytest.mark.asyncio
    async def test_context_isolation_across_nested_calls(self, mock_user_info_1):
        """Nested async calls with context changes should not leak."""
        async def inner_task():
            set_user_info(mock_user_info_1)
            await asyncio.sleep(0.01)
            return get_user_info()

        async def outer_task():
            set_user_info({"id": "outer-user", "username": "outer"})
            result = await inner_task()
            # After inner task returns, outer context should still be active
            outer_info = get_user_info()
            return result, outer_info

        inner_result, outer_result = await outer_task()

        assert inner_result["id"] == "user-1"
        assert outer_result["id"] == "outer-user"

    @pytest.mark.asyncio
    async def test_clear_all_auth_isolation(self, mock_user_info_1, mock_api_key_info):
        """clear_all_auth should only clear current task's context."""
        async def task1():
            set_user_info(mock_user_info_1)
            set_api_key_info(mock_api_key_info)
            clear_all_auth()
            return get_user_info(), get_api_key_info()

        async def task2():
            await asyncio.sleep(0.01)
            # task2 should still have its context intact
            return get_user_info(), get_api_key_info()

        # Set up task2's context before awaiting
        async def setup_task2():
            set_user_info(mock_user_info_1)
            set_api_key_info(mock_api_key_info)

        # Run setup and then both tasks concurrently
        await setup_task2()
        results = await asyncio.gather(task1(), task2())

        # task1 cleared its context
        assert results[0][0] is None
        assert results[0][1] is None

        # task2 still has its context
        assert results[1][0] is not None
        assert results[1][1] is not None

    @pytest.mark.asyncio
    async def test_large_concurrent_load(self):
        """Stress test with many concurrent requests to ensure no cross-contamination."""
        user_infos = [
            {"id": f"user-{i}", "username": f"user{i}"}
            for i in range(100)
        ]

        async def worker(user_info):
            set_user_info(user_info)
            await asyncio.sleep(0.001)  # Simulate some work
            result = get_user_info()
            clear_all_auth()
            return result

        tasks = [worker(ui) for ui in user_infos]
        results = await asyncio.gather(*tasks)

        for i, result in enumerate(results):
            assert result["id"] == f"user-{i}"

        # Main context should be clean
        assert get_user_info() is None

    @pytest.mark.asyncio
    async def test_context_survival_across_await(self, mock_user_info_1):
        """Context should survive across await points in the same task."""
        set_user_info(mock_user_info_1)
        
        # Multiple awaits should preserve context
        await asyncio.sleep(0)
        assert get_user_info()["id"] == "user-1"
        
        await asyncio.sleep(0)
        assert get_user_info()["id"] == "user-1"
        
        clear_all_auth()
        assert get_user_info() is None


class TestAuthHelperFunctions:
    """Test auth helper functions in isolation."""

    def setup_method(self):
        clear_all_auth()

    def teardown_method(self):
        clear_all_auth()

    def test_has_write_permission_with_api_key_read(self):
        """READ permission returns False for has_write_permission."""
        api_key_info = {
            "permission": Permission.READ,
            "is_admin": False,
        }
        set_api_key_info(api_key_info)
        
        assert not has_write_permission()  # Uses API because API key is set

    def test_has_write_permission_with_api_key_write(self):
        """WRITE permission returns True for has_write_permission."""
        api_key_info = {
            "permission": Permission.READ_WRITE,
            "is_admin": False,
        }
        set_api_key_info(api_key_info)
        
        assert has_write_permission()

    def test_has_write_permission_with_pat_write_scope(self):
        """PAT with WRITE scope returns True."""
        pat_info = {
            "scopes": [Scope.READ, Scope.WRITE],
            "is_superuser": False,
        }
        set_pat_info(pat_info)
        
        assert has_write_permission()

    def test_has_write_permission_with_pat_read_only(self):
        """PAT with only READ scope returns False."""
        pat_info = {
            "scopes": [Scope.READ],
            "is_superuser": False,
        }
        set_pat_info(pat_info)
        
        assert not has_write_permission()

    def test_has_write_permission_admin_bypass(self):
        """Admin or superuser bypasses permission check."""
        user_info = {
            "is_superuser": True,
        }
        set_user_info(user_info)
        
        assert has_write_permission()

    def test_has_scope_with_user_scopes(self):
        """has_scope checks user scopes correctly."""
        user_info = {
            "scopes": [Scope.READ, Scope.WRITE],
            "is_superuser": False,
        }
        set_user_info(user_info)
        
        assert has_scope(Scope.READ)
        assert has_scope(Scope.WRITE)
        assert not has_scope(Scope.ADMIN)

    def test_has_scope_admin_bypass(self):
        """Superuser bypasses scope checks."""
        user_info = {
            "scopes": [Scope.READ],
            "is_superuser": True,
        }
        set_user_info(user_info)
        
        assert has_scope(Scope.ADMIN)  # Admin bypasses scope check

    def test_has_scope_with_pat_scopes(self):
        """has_scope checks PAT scopes correctly."""
        pat_info = {
            "scopes": [Scope.READ, Scope.WRITE, Scope.ADMIN],
            "is_superuser": False,
        }
        set_pat_info(pat_info)
        
        assert has_scope(Scope.ADMIN)

    def test_has_scope_with_api_key_is_admin(self):
        """API key with is_admin flag bypasses scope checks."""
        api_key_info = {
            "is_admin": True,
        }
        set_api_key_info(api_key_info)
        
        assert has_scope(Scope.ADMIN)

    def test_get_current_user_id_from_user(self):
        """get_current_user_id extracts from user context."""
        user_info = {"id": "user-123"}
        set_user_info(user_info)
        
        assert get_current_user_id() == "user-123"

    def test_get_current_user_id_from_api_key(self):
        """get_current_user_id extracts from API key context."""
        api_key_info = {"user_id": "api-user-456"}
        set_api_key_info(api_key_info)
        
        assert get_current_user_id() == "api-user-456"

    def test_get_current_user_id_from_pat(self):
        """get_current_user_id extracts from PAT context."""
        pat_info = {"user_id": "pat-user-789"}
        set_pat_info(pat_info)
        
        assert get_current_user_id() == "pat-user-789"

    def test_get_current_user_id_no_auth(self):
        """get_current_user_id returns None when no auth."""
        clear_all_auth()
        
        assert get_current_user_id() is None

    def test_get_current_user_id_priority(self):
        """Test priority: user > api_key > pat when multiple contexts set."""
        # This is an unnatural scenario but tests the lookup order
        user_info = {"id": "user-main"}
        api_key_info = {"user_id": "api-key-main"}
        pat_info = {"user_id": "pat-main"}
        
        set_user_info(user_info)
        set_api_key_info(api_key_info)
        set_pat_info(pat_info)
        
        # Should prefer user_info
        assert get_current_user_id() == "user-main"
        
        clear_user_info()
        # Now should use api_key
        assert get_current_user_id() == "api-key-main"
        
        clear_api_key_info()
        # Now should use pat
        assert get_current_user_id() == "pat-main"

    def test_is_authenticated(self):
        """is_authenticated returns True if any auth context is set."""
        assert not is_authenticated()
        
        set_user_info({"id": "user"})
        assert is_authenticated()
        
        clear_user_info()
        set_api_key_info({"user_id": "api"})
        assert is_authenticated()
        
        clear_api_key_info()
        set_pat_info({"user_id": "pat"})
        assert is_authenticated()
        
        clear_all_auth()
        assert not is_authenticated()
