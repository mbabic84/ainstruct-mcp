import hashlib
from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, sessionmaker

from ..config import settings
from .models import (
    ApiKeyModel,
    CollectionModel,
    CollectionResponse,
    DocumentCreate,
    DocumentModel,
    DocumentResponse,
    PatTokenModel,
    Permission,
    Scope,
    UserModel,
    UserResponse,
    compute_content_hash,
    generate_api_key,
    generate_pat_token,
    hash_api_key,
    hash_pat_token,
    init_db,
    parse_scopes,
    scopes_to_str,
)


class DocumentRepository:
    def __init__(self, engine, collection_id: str | None = None):
        self.SessionLocal = sessionmaker(bind=engine)
        self.collection_id = collection_id

    def _get_session(self) -> Session:
        return self.SessionLocal()

    def create(self, doc: DocumentCreate) -> DocumentResponse:
        session = self._get_session()
        try:
            content_hash = compute_content_hash(doc.content)

            existing = session.execute(
                select(DocumentModel).where(
                    DocumentModel.content_hash == content_hash,
                    DocumentModel.collection_id == doc.collection_id,
                )
            ).scalar_one_or_none()

            if existing:
                return DocumentResponse(
                    id=existing.id,
                    collection_id=existing.collection_id,
                    title=existing.title,
                    content=existing.content,
                    document_type=existing.document_type,
                    created_at=existing.created_at,
                    updated_at=existing.updated_at,
                    doc_metadata=existing.doc_metadata or {},
                )

            db_doc = DocumentModel(
                collection_id=doc.collection_id,
                title=doc.title,
                content=doc.content,
                content_hash=content_hash,
                document_type=doc.document_type,
                doc_metadata=doc.doc_metadata,
            )
            session.add(db_doc)
            session.commit()
            session.refresh(db_doc)

            return DocumentResponse(
                id=db_doc.id,
                collection_id=db_doc.collection_id,
                title=db_doc.title,
                content=db_doc.content,
                document_type=db_doc.document_type,
                created_at=db_doc.created_at,
                updated_at=db_doc.updated_at,
                doc_metadata=db_doc.doc_metadata or {},
            )
        finally:
            session.close()

    def get_by_id(self, doc_id: str) -> DocumentResponse | None:
        session = self._get_session()
        try:
            query = select(DocumentModel).where(DocumentModel.id == doc_id)
            if self.collection_id:
                query = query.where(DocumentModel.collection_id == self.collection_id)

            db_doc = session.execute(query).scalar_one_or_none()
            if not db_doc:
                return None
            return DocumentResponse(
                id=db_doc.id,
                collection_id=db_doc.collection_id,
                title=db_doc.title,
                content=db_doc.content,
                document_type=db_doc.document_type,
                created_at=db_doc.created_at,
                updated_at=db_doc.updated_at,
                doc_metadata=db_doc.doc_metadata or {},
            )
        finally:
            session.close()

    def list_all(self, limit: int = 50, offset: int = 0) -> list[DocumentResponse]:
        session = self._get_session()
        try:
            query = select(DocumentModel).order_by(DocumentModel.created_at.desc())
            if self.collection_id:
                query = query.where(DocumentModel.collection_id == self.collection_id)

            docs = session.execute(
                query.limit(limit).offset(offset)
            ).scalars().all()

            return [
                DocumentResponse(
                    id=d.id,
                    collection_id=d.collection_id,
                    title=d.title,
                    content=d.content,
                    document_type=d.document_type,
                    created_at=d.created_at,
                    updated_at=d.updated_at,
                    doc_metadata=d.doc_metadata or {},
                )
                for d in docs
            ]
        finally:
            session.close()

    def delete(self, doc_id: str) -> bool:
        session = self._get_session()
        try:
            query = select(DocumentModel).where(DocumentModel.id == doc_id)
            if self.collection_id:
                query = query.where(DocumentModel.collection_id == self.collection_id)

            db_doc = session.execute(query).scalar_one_or_none()
            if not db_doc:
                return False
            session.delete(db_doc)
            session.commit()
            return True
        finally:
            session.close()

    def update_qdrant_point_id(self, doc_id: str, point_ids: list[str]):
        session = self._get_session()
        try:
            query = select(DocumentModel).where(DocumentModel.id == doc_id)
            if self.collection_id:
                query = query.where(DocumentModel.collection_id == self.collection_id)

            db_doc = session.execute(query).scalar_one_or_none()
            if db_doc:
                db_doc.qdrant_point_id = ",".join(point_ids)
                session.commit()
        finally:
            session.close()

    def update(
        self,
        doc_id: str,
        title: str,
        content: str,
        document_type: str,
        doc_metadata: dict,
    ) -> DocumentResponse | None:
        session = self._get_session()
        try:
            query = select(DocumentModel).where(DocumentModel.id == doc_id)
            if self.collection_id:
                query = query.where(DocumentModel.collection_id == self.collection_id)

            db_doc = session.execute(query).scalar_one_or_none()
            if not db_doc:
                return None

            content_hash = compute_content_hash(content)

            db_doc.title = title
            db_doc.content = content
            db_doc.content_hash = content_hash
            db_doc.document_type = document_type
            db_doc.doc_metadata = doc_metadata

            session.commit()
            session.refresh(db_doc)

            return DocumentResponse(
                id=db_doc.id,
                collection_id=db_doc.collection_id,
                title=db_doc.title,
                content=db_doc.content,
                document_type=db_doc.document_type,
                created_at=db_doc.created_at,
                updated_at=db_doc.updated_at,
                doc_metadata=db_doc.doc_metadata or {},
            )
        finally:
            session.close()

    def count_by_collection(self, collection_id: str) -> int:
        session = self._get_session()
        try:
            result = session.execute(
                select(func.count(DocumentModel.id)).where(
                    DocumentModel.collection_id == collection_id
                )
            ).scalar()
            return result or 0
        finally:
            session.close()

    def get_by_id_for_user(self, doc_id: str, user_id: str) -> DocumentResponse | None:
        session = self._get_session()
        try:
            query = select(DocumentModel).where(
                DocumentModel.id == doc_id
            ).join(CollectionModel).where(
                CollectionModel.user_id == user_id
            )

            db_doc = session.execute(query).scalar_one_or_none()
            if not db_doc:
                return None
            return DocumentResponse(
                id=db_doc.id,
                collection_id=db_doc.collection_id,
                title=db_doc.title,
                content=db_doc.content,
                document_type=db_doc.document_type,
                created_at=db_doc.created_at,
                updated_at=db_doc.updated_at,
                doc_metadata=db_doc.doc_metadata or {},
            )
        finally:
            session.close()

    def list_all_for_user(self, user_id: str, limit: int = 50, offset: int = 0) -> list[DocumentResponse]:
        session = self._get_session()
        try:
            query = (
                select(DocumentModel)
                .join(CollectionModel)
                .where(CollectionModel.user_id == user_id)
                .order_by(DocumentModel.created_at.desc())
            )

            docs = session.execute(
                query.limit(limit).offset(offset)
            ).scalars().all()

            return [
                DocumentResponse(
                    id=d.id,
                    collection_id=d.collection_id,
                    title=d.title,
                    content=d.content,
                    document_type=d.document_type,
                    created_at=d.created_at,
                    updated_at=d.updated_at,
                    doc_metadata=d.doc_metadata or {},
                )
                for d in docs
            ]
        finally:
            session.close()


class UserRepository:
    def __init__(self, engine):
        self.SessionLocal = sessionmaker(bind=engine)

    def _get_session(self) -> Session:
        return self.SessionLocal()

    def create(
        self,
        email: str,
        username: str,
        password_hash: str,
        is_superuser: bool = False,
    ) -> UserResponse:
        session = self._get_session()
        try:
            user = UserModel(
                email=email,
                username=username,
                password_hash=password_hash,
                is_superuser=is_superuser,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
            )
        finally:
            session.close()

    def get_by_id(self, user_id: str) -> UserResponse | None:
        session = self._get_session()
        try:
            user = session.get(UserModel, user_id)
            if not user:
                return None
            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
            )
        finally:
            session.close()

    def get_by_username(self, username: str) -> dict | None:
        session = self._get_session()
        try:
            user = session.execute(
                select(UserModel).where(UserModel.username == username)
            ).scalar_one_or_none()
            if not user:
                return None
            return {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "password_hash": user.password_hash,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "created_at": user.created_at,
            }
        finally:
            session.close()

    def get_by_email(self, email: str) -> UserResponse | None:
        session = self._get_session()
        try:
            user = session.execute(
                select(UserModel).where(UserModel.email == email)
            ).scalar_one_or_none()
            if not user:
                return None
            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
            )
        finally:
            session.close()

    def update(
        self,
        user_id: str,
        email: str | None = None,
        username: str | None = None,
        password_hash: str | None = None,
        is_active: bool | None = None,
        is_superuser: bool | None = None,
    ) -> UserResponse | None:
        session = self._get_session()
        try:
            user = session.get(UserModel, user_id)
            if not user:
                return None
            if email is not None:
                user.email = email
            if username is not None:
                user.username = username
            if password_hash is not None:
                user.password_hash = password_hash
            if is_active is not None:
                user.is_active = is_active
            if is_superuser is not None:
                user.is_superuser = is_superuser
            session.commit()
            session.refresh(user)
            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
            )
        finally:
            session.close()

    def delete(self, user_id: str) -> bool:
        session = self._get_session()
        try:
            user = session.get(UserModel, user_id)
            if not user:
                return False
            session.delete(user)
            session.commit()
            return True
        finally:
            session.close()

    def list_all(self, limit: int = 50, offset: int = 0) -> list[UserResponse]:
        session = self._get_session()
        try:
            users = session.execute(
                select(UserModel).limit(limit).offset(offset)
            ).scalars().all()
            return [
                UserResponse(
                    id=u.id,
                    email=u.email,
                    username=u.username,
                    is_active=u.is_active,
                    is_superuser=u.is_superuser,
                    created_at=u.created_at,
                )
                for u in users
            ]
        finally:
            session.close()

    def search(self, query: str, limit: int = 50, offset: int = 0) -> list[UserResponse]:
        session = self._get_session()
        try:
            search_pattern = f"%{query}%"
            users = session.execute(
                select(UserModel).where(
                    or_(
                        UserModel.username.ilike(search_pattern),
                        UserModel.email.ilike(search_pattern),
                    )
                ).limit(limit).offset(offset)
            ).scalars().all()
            return [
                UserResponse(
                    id=u.id,
                    email=u.email,
                    username=u.username,
                    is_active=u.is_active,
                    is_superuser=u.is_superuser,
                    created_at=u.created_at,
                )
                for u in users
            ]
        finally:
            session.close()


class CollectionRepository:
    def __init__(self, engine):
        self.SessionLocal = sessionmaker(bind=engine)

    def _get_session(self) -> Session:
        return self.SessionLocal()

    def create(self, user_id: str, name: str) -> CollectionResponse:
        session = self._get_session()
        try:
            collection = CollectionModel(
                user_id=user_id,
                name=name,
            )
            session.add(collection)
            session.commit()
            session.refresh(collection)
            return CollectionResponse(
                id=collection.id,
                name=collection.name,
                document_count=0,
                api_key_count=0,
                created_at=collection.created_at,
            )
        finally:
            session.close()

    def get_by_id(self, collection_id: str) -> dict | None:
        session = self._get_session()
        try:
            collection = session.get(CollectionModel, collection_id)
            if not collection:
                return None
            doc_count = session.execute(
                select(func.count(DocumentModel.id)).where(
                    DocumentModel.collection_id == collection_id
                )
            ).scalar() or 0
            key_count = session.execute(
                select(func.count(ApiKeyModel.id)).where(
                    ApiKeyModel.collection_id == collection_id,
                    ApiKeyModel.is_active.is_(True),
                )
            ).scalar() or 0
            return {
                "id": collection.id,
                "name": collection.name,
                "qdrant_collection": collection.qdrant_collection,
                "user_id": collection.user_id,
                "document_count": doc_count,
                "api_key_count": key_count,
                "created_at": collection.created_at,
                "updated_at": collection.updated_at,
            }
        finally:
            session.close()

    def list_by_user(self, user_id: str) -> list[dict]:
        session = self._get_session()
        try:
            collections = session.execute(
                select(CollectionModel).where(CollectionModel.user_id == user_id)
            ).scalars().all()
            return [
                {
                    "id": c.id,
                    "name": c.name,
                    "qdrant_collection": c.qdrant_collection,
                    "user_id": c.user_id,
                    "created_at": c.created_at,
                }
                for c in collections
            ]
        finally:
            session.close()

    def delete(self, collection_id: str) -> bool:
        session = self._get_session()
        try:
            collection = session.get(CollectionModel, collection_id)
            if not collection:
                return False
            session.delete(collection)
            session.commit()
            return True
        finally:
            session.close()

    def rename(self, collection_id: str, name: str) -> CollectionResponse | None:
        session = self._get_session()
        try:
            collection = session.get(CollectionModel, collection_id)
            if not collection:
                return None
            collection.name = name
            session.commit()
            session.refresh(collection)
            doc_count = session.execute(
                select(func.count(DocumentModel.id)).where(
                    DocumentModel.collection_id == collection_id
                )
            ).scalar() or 0
            key_count = session.execute(
                select(func.count(ApiKeyModel.id)).where(
                    ApiKeyModel.collection_id == collection_id,
                    ApiKeyModel.is_active.is_(True),
                )
            ).scalar() or 0
            return CollectionResponse(
                id=collection.id,
                name=collection.name,
                document_count=doc_count,
                api_key_count=key_count,
                created_at=collection.created_at,
            )
        finally:
            session.close()

    def get_document_count(self, collection_id: str) -> int:
        session = self._get_session()
        try:
            result = session.execute(
                select(func.count(DocumentModel.id)).where(
                    DocumentModel.collection_id == collection_id
                )
            ).scalar()
            return result or 0
        finally:
            session.close()

    def get_api_key_count(self, collection_id: str) -> int:
        session = self._get_session()
        try:
            result = session.execute(
                select(func.count(ApiKeyModel.id)).where(
                    ApiKeyModel.collection_id == collection_id,
                    ApiKeyModel.is_active.is_(True),
                )
            ).scalar()
            return result or 0
        finally:
            session.close()


class ApiKeyRepository:
    def __init__(self, engine):
        self.SessionLocal = sessionmaker(bind=engine)

    def _get_session(self) -> Session:
        return self.SessionLocal()

    @staticmethod
    def hash_key(key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def validate(self, key: str) -> dict | None:
        session = self._get_session()
        try:
            key_hash = self.hash_key(key)
            api_key = session.execute(
                select(ApiKeyModel).where(
                    ApiKeyModel.key_hash == key_hash,
                    ApiKeyModel.is_active,
                )
            ).scalar_one_or_none()

            if api_key:
                if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                    return None
                collection = session.get(CollectionModel, api_key.collection_id)
                if not collection:
                    return None
                api_key.last_used = datetime.utcnow()
                session.commit()
                return {
                    "id": api_key.id,
                    "label": api_key.label,
                    "collection_id": api_key.collection_id,
                    "qdrant_collection": collection.qdrant_collection,
                    "collection_name": collection.name,
                    "user_id": api_key.user_id,
                    "permission": Permission(api_key.permission),
                    "is_admin": False,
                }
            return None
        finally:
            session.close()

    def get_by_id(self, key_id: str) -> dict | None:
        session = self._get_session()
        try:
            api_key = session.get(ApiKeyModel, key_id)
            if not api_key:
                return None
            collection = session.get(CollectionModel, api_key.collection_id)
            return {
                "id": api_key.id,
                "label": api_key.label,
                "collection_id": api_key.collection_id,
                "collection_name": collection.name if collection else None,
                "qdrant_collection": collection.qdrant_collection if collection else None,
                "is_active": api_key.is_active,
                "user_id": api_key.user_id,
                "permission": Permission(api_key.permission),
                "expires_at": api_key.expires_at,
                "created_at": api_key.created_at,
                "last_used": api_key.last_used,
            }
        finally:
            session.close()

    def create(
        self,
        label: str,
        collection_id: str,
        user_id: str | None = None,
        permission: Permission = Permission.READ_WRITE,
        expires_in_days: int | None = None,
    ) -> tuple[str, str]:
        session = self._get_session()
        try:
            key = generate_api_key()
            key_hash = hash_api_key(key)

            expires_at = None
            if expires_in_days is not None:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            elif settings.api_key_default_expiry_days is not None:
                expires_at = datetime.utcnow() + timedelta(days=settings.api_key_default_expiry_days)

            api_key = ApiKeyModel(
                key_hash=key_hash,
                label=label,
                collection_id=collection_id,
                user_id=user_id,
                permission=permission.value,
                expires_at=expires_at,
            )
            session.add(api_key)
            session.commit()
            return api_key.id, key
        finally:
            session.close()

    def list_all(self, user_id: str | None = None) -> list[dict]:
        session = self._get_session()
        try:
            query = select(ApiKeyModel)
            if user_id:
                query = query.where(ApiKeyModel.user_id == user_id)
            keys = session.execute(query).scalars().all()
            result = []
            for k in keys:
                collection = session.get(CollectionModel, k.collection_id)
                result.append({
                    "id": k.id,
                    "label": k.label,
                    "collection_id": k.collection_id,
                    "collection_name": collection.name if collection else None,
                    "created_at": k.created_at,
                    "last_used": k.last_used,
                    "is_active": k.is_active,
                    "user_id": k.user_id,
                    "permission": Permission(k.permission),
                    "expires_at": k.expires_at,
                })
            return result
        finally:
            session.close()

    def delete(self, key_id: str) -> bool:
        session = self._get_session()
        try:
            key = session.get(ApiKeyModel, key_id)
            if not key:
                return False
            session.delete(key)
            session.commit()
            return True
        finally:
            session.close()

    def revoke(self, key_id: str) -> bool:
        session = self._get_session()
        try:
            key = session.get(ApiKeyModel, key_id)
            if not key:
                return False
            key.is_active = False
            session.commit()
            return True
        finally:
            session.close()

    def rotate(self, key_id: str) -> tuple[str, str] | None:
        session = self._get_session()
        try:
            old_key = session.get(ApiKeyModel, key_id)
            if not old_key:
                return None

            old_key.is_active = False

            new_key = generate_api_key()
            key_hash = hash_api_key(new_key)

            new_api_key = ApiKeyModel(
                key_hash=key_hash,
                label=old_key.label,
                collection_id=old_key.collection_id,
                user_id=old_key.user_id,
                permission=old_key.permission,
                expires_at=old_key.expires_at,
            )
            session.add(new_api_key)
            session.commit()
            return new_api_key.id, new_key
        finally:
            session.close()

    def list_by_user(self, user_id: str) -> list[dict]:
        return self.list_all(user_id=user_id)


class PatTokenRepository:
    def __init__(self, engine):
        self.SessionLocal = sessionmaker(bind=engine)

    def _get_session(self) -> Session:
        return self.SessionLocal()

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def validate(self, token: str) -> dict | None:
        session = self._get_session()
        try:
            token_hash = self.hash_token(token)
            pat_token = session.execute(
                select(PatTokenModel).where(
                    PatTokenModel.token_hash == token_hash,
                    PatTokenModel.is_active.is_(True),
                )
            ).scalar_one_or_none()

            if not pat_token:
                return None

            if pat_token.expires_at and pat_token.expires_at < datetime.utcnow():
                return None

            user = session.get(UserModel, pat_token.user_id)
            if not user or not user.is_active:
                return None

            pat_token.last_used = datetime.utcnow()
            session.commit()

            return {
                "id": pat_token.id,
                "label": pat_token.label,
                "user_id": pat_token.user_id,
                "scopes": parse_scopes(pat_token.scopes),
                "is_superuser": user.is_superuser,
                "username": user.username,
                "email": user.email,
            }
        finally:
            session.close()

    def get_by_id(self, token_id: str) -> dict | None:
        session = self._get_session()
        try:
            pat_token = session.get(PatTokenModel, token_id)
            if not pat_token:
                return None
            return {
                "id": pat_token.id,
                "label": pat_token.label,
                "user_id": pat_token.user_id,
                "scopes": parse_scopes(pat_token.scopes),
                "created_at": pat_token.created_at,
                "expires_at": pat_token.expires_at,
                "is_active": pat_token.is_active,
                "last_used": pat_token.last_used,
            }
        finally:
            session.close()

    def create(
        self,
        label: str,
        user_id: str,
        scopes: list[str],
        expires_in_days: int | None = None,
    ) -> tuple[str, str]:
        session = self._get_session()
        try:
            token = generate_pat_token()
            token_hash = hash_pat_token(token)

            expires_at = None
            if expires_in_days is not None:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            elif settings.pat_default_expiry_days is not None:
                expires_at = datetime.utcnow() + timedelta(days=settings.pat_default_expiry_days)

            pat_token = PatTokenModel(
                token_hash=token_hash,
                label=label,
                user_id=user_id,
                scopes=scopes_to_str([Scope(s) for s in scopes]),
                expires_at=expires_at,
            )
            session.add(pat_token)
            session.commit()
            return pat_token.id, token
        finally:
            session.close()

    def list_all(self, user_id: str | None = None) -> list[dict]:
        session = self._get_session()
        try:
            query = select(PatTokenModel)
            if user_id:
                query = query.where(PatTokenModel.user_id == user_id)
            tokens = session.execute(query.order_by(PatTokenModel.created_at.desc())).scalars().all()
            return [
                {
                    "id": t.id,
                    "label": t.label,
                    "user_id": t.user_id,
                    "scopes": parse_scopes(t.scopes),
                    "created_at": t.created_at,
                    "expires_at": t.expires_at,
                    "is_active": t.is_active,
                    "last_used": t.last_used,
                }
                for t in tokens
            ]
        finally:
            session.close()

    def delete(self, token_id: str) -> bool:
        session = self._get_session()
        try:
            token = session.get(PatTokenModel, token_id)
            if not token:
                return False
            session.delete(token)
            session.commit()
            return True
        finally:
            session.close()

    def revoke(self, token_id: str) -> bool:
        session = self._get_session()
        try:
            token = session.get(PatTokenModel, token_id)
            if not token:
                return False
            token.is_active = False
            session.commit()
            return True
        finally:
            session.close()

    def rotate(self, token_id: str) -> tuple[str, str] | None:
        session = self._get_session()
        try:
            old_token = session.get(PatTokenModel, token_id)
            if not old_token:
                return None

            old_token.is_active = False

            new_token = generate_pat_token()
            token_hash = hash_pat_token(new_token)

            new_pat_token = PatTokenModel(
                token_hash=token_hash,
                label=old_token.label,
                user_id=old_token.user_id,
                scopes=old_token.scopes,
                expires_at=old_token.expires_at,
            )
            session.add(new_pat_token)
            session.commit()
            return new_pat_token.id, new_token
        finally:
            session.close()

    def list_by_user(self, user_id: str) -> list[dict]:
        return self.list_all(user_id=user_id)


_engine = None


def get_document_repository(collection_id: str | None = None) -> DocumentRepository:
    global _engine
    if _engine is None:
        _engine = init_db(settings.db_path)
    return DocumentRepository(_engine, collection_id)


def get_api_key_repository() -> ApiKeyRepository:
    global _engine
    if _engine is None:
        _engine = init_db(settings.db_path)
    return ApiKeyRepository(_engine)


def get_user_repository() -> UserRepository:
    global _engine
    if _engine is None:
        _engine = init_db(settings.db_path)
    return UserRepository(_engine)


def get_collection_repository() -> CollectionRepository:
    global _engine
    if _engine is None:
        _engine = init_db(settings.db_path)
    return CollectionRepository(_engine)


def get_pat_token_repository() -> PatTokenRepository:
    global _engine
    if _engine is None:
        _engine = init_db(settings.db_path)
    return PatTokenRepository(_engine)
