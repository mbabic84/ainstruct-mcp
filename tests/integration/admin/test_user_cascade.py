"""
Integration tests for user deletion with related entities.
Tests that user deletion properly handles cascading deletes of collections,
API keys, PAT tokens, and documents.

This test uses real database operations to catch ORM cascade configuration bugs.
"""
import os
import tempfile
import pytest

from sqlalchemy import create_engine

from app.db.models import (
    Base,
    DocumentCreate,
    Permission,
    Scope,
)


@pytest.fixture
def temp_db():
    """Create a temporary database for each test."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    
    yield engine
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def user_repo(temp_db):
    from app.db.repository import UserRepository
    return UserRepository(temp_db)


@pytest.fixture
def collection_repo(temp_db):
    from app.db.repository import CollectionRepository
    return CollectionRepository(temp_db)


@pytest.fixture
def api_key_repo(temp_db):
    from app.db.repository import ApiKeyRepository
    return ApiKeyRepository(temp_db)


@pytest.fixture
def pat_token_repo(temp_db):
    from app.db.repository import PatTokenRepository
    return PatTokenRepository(temp_db)


@pytest.fixture
def document_repo(temp_db):
    from app.db.repository import DocumentRepository
    return DocumentRepository(temp_db)


class TestUserDeletionWithRelatedEntities:
    """
    Test that deleting a user properly handles related entities.
    
    These tests catch bugs in cascade delete configuration that mocked
    unit tests cannot detect.
    """

    def test_delete_user_with_no_related_entities(self, user_repo):
        """Deleting a user with no related entities should succeed."""
        # Create user
        user = user_repo.create(
            email="test@example.com",
            username="testuser",
            password_hash="hash123",
        )
        
        # Delete user
        result = user_repo.delete(user.id)
        
        assert result is True
        assert user_repo.get_by_id(user.id) is None

    def test_delete_user_with_collection_raises_error_without_cascade(
        self, user_repo, collection_repo
    ):
        """
        Deleting a user with collections should fail if cascade is not configured.
        
        This test documents the expected behavior: either the ORM should cascade
        delete the collections, or an explicit error should be raised.
        
        Current behavior: IntegrityError due to NOT NULL constraint.
        Expected behavior: Either cascade delete or proper error handling.
        """
        # Create user
        user = user_repo.create(
            email="test@example.com",
            username="testuser",
            password_hash="hash123",
        )
        
        # Create collection owned by user
        collection = collection_repo.create(
            user_id=user.id,
            name="test-collection",
        )
        
        # Attempt to delete user - this should either:
        # 1. Succeed with cascade delete of collection, OR
        # 2. Raise a clear error about existing collections
        # Currently it raises IntegrityError which is a bug
        try:
            result = user_repo.delete(user.id)
            # If cascade is configured, deletion should succeed
            assert result is True
            # Collection should be deleted too
            assert collection_repo.get_by_id(collection.id) is None
        except Exception as e:
            # If cascade is not configured, should raise a clear error
            # (not IntegrityError)
            error_msg = str(e).lower()
            assert "not null" not in error_msg, (
                f"Got IntegrityError due to missing cascade config: {e}"
            )
            # Should mention the constraint issue explicitly
            assert "collection" in error_msg or "constraint" in error_msg, (
                f"Error message should explain the constraint: {e}"
            )

    def test_delete_user_with_api_key_raises_error_without_cascade(
        self, user_repo, collection_repo, api_key_repo
    ):
        """
        Deleting a user with API keys should handle cascade properly.
        
        API keys have a nullable user_id, so they can exist without a user.
        But the test verifies the relationship works correctly.
        """
        # Create user
        user = user_repo.create(
            email="test@example.com",
            username="testuser",
            password_hash="hash123",
        )
        
        # Create collection
        collection = collection_repo.create(
            user_id=user.id,
            name="test-collection",
        )
        
        # Create API key owned by user
        api_key_id, _ = api_key_repo.create(
            label="Test Key",
            collection_id=collection.id,
            user_id=user.id,
        )
        
        # Attempt to delete user
        try:
            result = user_repo.delete(user.id)
            # If cascade works, should succeed
            assert result is True
        except Exception as e:
            error_msg = str(e).lower()
            assert "not null" not in error_msg, (
                f"Got IntegrityError due to missing cascade config: {e}"
            )

    def test_delete_user_with_pat_token_raises_error_without_cascade(
        self, user_repo, pat_token_repo
    ):
        """
        Deleting a user with PAT tokens should handle cascade properly.
        
        PAT tokens have non-nullable user_id, so they must be deleted
        when the user is deleted.
        """
        # Create user
        user = user_repo.create(
            email="test@example.com",
            username="testuser",
            password_hash="hash123",
        )
        
        # Create PAT token for user
        pat_id, _ = pat_token_repo.create(
            label="Test PAT",
            user_id=user.id,
            scopes=[Scope.READ.value, Scope.WRITE.value],
        )
        
        # Attempt to delete user
        try:
            result = user_repo.delete(user.id)
            # If cascade works, should succeed
            assert result is True
            # PAT token should be deleted
            tokens = pat_token_repo.list_all(user_id=user.id)
            assert len(tokens) == 0
        except Exception as e:
            error_msg = str(e).lower()
            assert "not null" not in error_msg, (
                f"Got IntegrityError due to missing cascade config: {e}"
            )

    def test_delete_user_with_all_related_entities(
        self, user_repo, collection_repo, api_key_repo, pat_token_repo, document_repo
    ):
        """
        Deleting a user with all related entities should cascade properly.
        
        This is the comprehensive test that catches the cascade delete bug.
        """
        # Create user
        user = user_repo.create(
            email="test@example.com",
            username="testuser",
            password_hash="hash123",
        )
        
        # Create collection
        collection = collection_repo.create(
            user_id=user.id,
            name="test-collection",
        )
        
        # Create document in collection
        document = document_repo.create(DocumentCreate(
            collection_id=collection.id,
            title="Test Document",
            content="Test content",
            document_type="markdown",
        ))
        
        # Create API key
        api_key_id, _ = api_key_repo.create(
            label="Test Key",
            collection_id=collection.id,
            user_id=user.id,
        )
        
        # Create PAT token
        pat_id, _ = pat_token_repo.create(
            label="Test PAT",
            user_id=user.id,
            scopes=[Scope.READ.value, Scope.WRITE.value],
        )
        
        # Attempt to delete user - this should cascade delete everything
        try:
            result = user_repo.delete(user.id)
            
            # If cascade is properly configured, user and all related entities
            # should be deleted
            assert result is True
            assert user_repo.get_by_id(user.id) is None
            assert collection_repo.get_by_id(collection.id) is None
            assert document_repo.get_by_id(document.id) is None
            
        except Exception as e:
            # Bug: Currently raises IntegrityError due to missing cascade
            error_msg = str(e)
            if "NOT NULL" in error_msg:
                pytest.fail(
                    f"ORM cascade delete not configured properly. "
                    f"Got IntegrityError: {error_msg}\n"
                    f"Fix: Add cascade='all, delete-orphan' to UserModel relationships"
                )
            raise


class TestCollectionDeletionWithDocuments:
    """
    Test that deleting a collection properly handles related documents.
    """

    def test_delete_collection_with_documents(
        self, user_repo, collection_repo, document_repo
    ):
        """Deleting a collection should cascade delete its documents."""
        # Create user
        user = user_repo.create(
            email="test@example.com",
            username="testuser",
            password_hash="hash123",
        )
        
        # Create collection
        collection = collection_repo.create(
            user_id=user.id,
            name="test-collection",
        )
        
        # Create document
        document = document_repo.create(DocumentCreate(
            collection_id=collection.id,
            title="Test Document",
            content="Test content",
            document_type="markdown",
        ))
        
        # Delete collection
        try:
            result = collection_repo.delete(collection.id)
            
            assert result is True
            assert collection_repo.get_by_id(collection.id) is None
            assert document_repo.get_by_id(document.id) is None
            
        except Exception as e:
            error_msg = str(e)
            if "NOT NULL" in error_msg or "FOREIGN KEY" in error_msg:
                pytest.fail(
                    f"Collection deletion should cascade to documents. "
                    f"Got error: {error_msg}"
                )
            raise


class TestApiKeyDeletion:
    """
    Test that API key deletion works correctly.
    """

    def test_delete_api_key(self, user_repo, collection_repo, api_key_repo):
        """Deleting an API key should work without affecting collection."""
        # Create user
        user = user_repo.create(
            email="test@example.com",
            username="testuser",
            password_hash="hash123",
        )
        
        # Create collection
        collection = collection_repo.create(
            user_id=user.id,
            name="test-collection",
        )
        
        # Create API key
        api_key_id, _ = api_key_repo.create(
            label="Test Key",
            collection_id=collection.id,
            user_id=user.id,
        )
        
        # Delete API key (revoke it)
        result = api_key_repo.revoke(api_key_id)
        assert result is True
        
        # Collection should still exist
        assert collection_repo.get_by_id(collection.id) is not None
