import hashlib
from datetime import datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from shared.config import settings
from shared.db.models import (
    CatModel,
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
    generate_cat_token,
    generate_pat_token,
    hash_cat_token,
    hash_pat_token,
    parse_scopes,
    scopes_to_str,
)


class DocumentRepository:
    def __init__(self, async_session_factory, collection_id: str | None = None):
        self.async_session = async_session_factory
        self.collection_id = collection_id

    async def create(self, doc: DocumentCreate) -> DocumentResponse:
        async with self.async_session() as session:
            content_hash = compute_content_hash(doc.content)

            existing = await session.execute(
                select(DocumentModel).where(
                    DocumentModel.content_hash == content_hash,
                    DocumentModel.collection_id == doc.collection_id,
                )
            )
            existing = existing.scalar_one_or_none()

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
            await session.commit()
            await session.refresh(db_doc)

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

    async def get_by_id(self, doc_id: str) -> DocumentResponse | None:
        async with self.async_session() as session:
            query = select(DocumentModel).where(DocumentModel.id == doc_id)
            if self.collection_id:
                query = query.where(DocumentModel.collection_id == self.collection_id)

            result = await session.execute(query)
            db_doc = result.scalar_one_or_none()
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

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[DocumentResponse]:
        async with self.async_session() as session:
            query = select(DocumentModel).order_by(DocumentModel.created_at.desc())
            if self.collection_id:
                query = query.where(DocumentModel.collection_id == self.collection_id)

            result = await session.execute(query.limit(limit).offset(offset))
            docs = result.scalars().all()

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

    async def delete(self, doc_id: str) -> bool:
        async with self.async_session() as session:
            query = select(DocumentModel).where(DocumentModel.id == doc_id)
            if self.collection_id:
                query = query.where(DocumentModel.collection_id == self.collection_id)

            result = await session.execute(query)
            db_doc = result.scalar_one_or_none()
            if not db_doc:
                return False
            await session.delete(db_doc)
            await session.commit()
            return True

    async def update_qdrant_point_id(self, doc_id: str, point_ids: list[str]):
        async with self.async_session() as session:
            query = select(DocumentModel).where(DocumentModel.id == doc_id)
            if self.collection_id:
                query = query.where(DocumentModel.collection_id == self.collection_id)

            result = await session.execute(query)
            db_doc = result.scalar_one_or_none()
            if db_doc:
                db_doc.qdrant_point_id = ",".join(point_ids)
                await session.commit()

    async def update_collection_id(self, doc_id: str, new_collection_id: str) -> bool:
        async with self.async_session() as session:
            query = select(DocumentModel).where(DocumentModel.id == doc_id)
            if self.collection_id:
                query = query.where(DocumentModel.collection_id == self.collection_id)

            result = await session.execute(query)
            db_doc = result.scalar_one_or_none()
            if not db_doc:
                return False

            db_doc.collection_id = new_collection_id
            await session.commit()
            return True

    async def update(
        self,
        doc_id: str,
        title: str,
        content: str,
        document_type: str,
        doc_metadata: dict,
    ) -> DocumentResponse | None:
        async with self.async_session() as session:
            query = select(DocumentModel).where(DocumentModel.id == doc_id)
            if self.collection_id:
                query = query.where(DocumentModel.collection_id == self.collection_id)

            result = await session.execute(query)
            db_doc = result.scalar_one_or_none()
            if not db_doc:
                return None

            content_hash = compute_content_hash(content)

            db_doc.title = title
            db_doc.content = content
            db_doc.content_hash = content_hash
            db_doc.document_type = document_type
            db_doc.doc_metadata = doc_metadata

            await session.commit()
            await session.refresh(db_doc)

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

    async def count_by_collection(self, collection_id: str) -> int:
        async with self.async_session() as session:
            result = await session.execute(
                select(func.count(DocumentModel.id)).where(
                    DocumentModel.collection_id == collection_id
                )
            )
            return result.scalar() or 0

    async def get_by_id_for_user(self, doc_id: str, user_id: str) -> DocumentResponse | None:
        async with self.async_session() as session:
            query = (
                select(DocumentModel)
                .where(DocumentModel.id == doc_id)
                .join(CollectionModel)
                .where(CollectionModel.user_id == user_id)
            )

            result = await session.execute(query)
            db_doc = result.scalar_one_or_none()
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

    async def list_all_for_user(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> list[DocumentResponse]:
        async with self.async_session() as session:
            query = (
                select(DocumentModel)
                .join(CollectionModel)
                .where(CollectionModel.user_id == user_id)
                .order_by(DocumentModel.created_at.desc())
            )

            result = await session.execute(query.limit(limit).offset(offset))
            docs = result.scalars().all()

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


class UserRepository:
    def __init__(self, async_session_factory):
        self.async_session = async_session_factory

    async def create(
        self,
        email: str,
        username: str,
        password_hash: str,
        is_superuser: bool = False,
    ) -> UserResponse:
        async with self.async_session() as session:
            user = UserModel(
                email=email,
                username=username,
                password_hash=password_hash,
                is_superuser=is_superuser,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
            )

    async def get_by_id(self, user_id: str) -> UserResponse | None:
        async with self.async_session() as session:
            result = await session.execute(select(UserModel).where(UserModel.id == user_id))
            user = result.scalar_one_or_none()
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

    async def get_by_username(self, username: str) -> dict | None:
        async with self.async_session() as session:
            result = await session.execute(select(UserModel).where(UserModel.username == username))
            user = result.scalar_one_or_none()
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

    async def get_by_email(self, email: str) -> UserResponse | None:
        async with self.async_session() as session:
            result = await session.execute(select(UserModel).where(UserModel.email == email))
            user = result.scalar_one_or_none()
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

    async def update(
        self,
        user_id: str,
        email: str | None = None,
        username: str | None = None,
        password_hash: str | None = None,
        is_active: bool | None = None,
        is_superuser: bool | None = None,
    ) -> UserResponse | None:
        async with self.async_session() as session:
            result = await session.execute(select(UserModel).where(UserModel.id == user_id))
            user = result.scalar_one_or_none()
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
            await session.commit()
            await session.refresh(user)
            return UserResponse(
                id=user.id,
                email=user.email,
                username=user.username,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                created_at=user.created_at,
            )

    async def delete(self, user_id: str) -> bool:
        async with self.async_session() as session:
            result = await session.execute(select(UserModel).where(UserModel.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return False
            await session.delete(user)
            await session.commit()
            return True

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[UserResponse]:
        async with self.async_session() as session:
            result = await session.execute(select(UserModel).limit(limit).offset(offset))
            users = result.scalars().all()
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

    async def search(self, query: str, limit: int = 50, offset: int = 0) -> list[UserResponse]:
        async with self.async_session() as session:
            search_pattern = f"%{query}%"
            result = await session.execute(
                select(UserModel)
                .where(
                    or_(
                        UserModel.username.ilike(search_pattern),
                        UserModel.email.ilike(search_pattern),
                    )
                )
                .limit(limit)
                .offset(offset)
            )
            users = result.scalars().all()
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

    async def count_superusers(self) -> int:
        async with self.async_session() as session:
            result = await session.execute(
                select(func.count(UserModel.id)).where(UserModel.is_superuser.is_(True))
            )
            return result.scalar() or 0


class CollectionRepository:
    def __init__(self, async_session_factory):
        self.async_session = async_session_factory

    async def create(self, user_id: str, name: str) -> CollectionResponse:
        async with self.async_session() as session:
            collection = CollectionModel(
                user_id=user_id,
                name=name,
            )
            session.add(collection)
            await session.commit()
            await session.refresh(collection)
            return CollectionResponse(
                id=collection.id,
                name=collection.name,
                document_count=0,
                cat_count=0,
                created_at=collection.created_at,
            )

    async def get_by_id(self, collection_id: str) -> dict | None:
        async with self.async_session() as session:
            result = await session.execute(
                select(CollectionModel).where(CollectionModel.id == collection_id)
            )
            collection = result.scalar_one_or_none()
            if not collection:
                return None

            doc_count_result = await session.execute(
                select(func.count(DocumentModel.id)).where(
                    DocumentModel.collection_id == collection_id
                )
            )
            doc_count = doc_count_result.scalar() or 0

            key_count_result = await session.execute(
                select(func.count(CatModel.id)).where(
                    CatModel.collection_id == collection_id,
                    CatModel.is_active.is_(True),
                )
            )
            key_count = key_count_result.scalar() or 0

            return {
                "id": collection.id,
                "name": collection.name,
                "qdrant_collection": collection.qdrant_collection,
                "user_id": collection.user_id,
                "document_count": doc_count,
                "cat_count": key_count,
                "created_at": collection.created_at,
                "updated_at": collection.updated_at,
            }

    async def list_by_user(self, user_id: str) -> list[dict]:
        async with self.async_session() as session:
            result = await session.execute(
                select(CollectionModel).where(CollectionModel.user_id == user_id)
            )
            collections = result.scalars().all()

            items = []
            for c in collections:
                doc_count_result = await session.execute(
                    select(func.count(DocumentModel.id)).where(DocumentModel.collection_id == c.id)
                )
                doc_count = doc_count_result.scalar() or 0

                key_count_result = await session.execute(
                    select(func.count(CatModel.id)).where(
                        CatModel.collection_id == c.id,
                        CatModel.is_active.is_(True),
                    )
                )
                cat_count = key_count_result.scalar() or 0

                items.append(
                    {
                        "id": c.id,
                        "name": c.name,
                        "qdrant_collection": c.qdrant_collection,
                        "user_id": c.user_id,
                        "document_count": doc_count,
                        "cat_count": cat_count,
                        "created_at": c.created_at,
                    }
                )
            return items

    async def delete(self, collection_id: str) -> bool:
        async with self.async_session() as session:
            result = await session.execute(
                select(CollectionModel).where(CollectionModel.id == collection_id)
            )
            collection = result.scalar_one_or_none()
            if not collection:
                return False
            await session.delete(collection)
            await session.commit()
            return True

    async def rename(self, collection_id: str, name: str) -> CollectionResponse | None:
        async with self.async_session() as session:
            result = await session.execute(
                select(CollectionModel).where(CollectionModel.id == collection_id)
            )
            collection = result.scalar_one_or_none()
            if not collection:
                return None
            collection.name = name
            await session.commit()
            await session.refresh(collection)

            doc_count_result = await session.execute(
                select(func.count(DocumentModel.id)).where(
                    DocumentModel.collection_id == collection_id
                )
            )
            doc_count = doc_count_result.scalar() or 0

            key_count_result = await session.execute(
                select(func.count(CatModel.id)).where(
                    CatModel.collection_id == collection_id,
                    CatModel.is_active.is_(True),
                )
            )
            key_count = key_count_result.scalar() or 0

            return CollectionResponse(
                id=collection.id,
                name=collection.name,
                document_count=doc_count,
                cat_count=key_count,
                created_at=collection.created_at,
            )

    async def get_document_count(self, collection_id: str) -> int:
        async with self.async_session() as session:
            result = await session.execute(
                select(func.count(DocumentModel.id)).where(
                    DocumentModel.collection_id == collection_id
                )
            )
            return result.scalar() or 0

    async def get_by_name_for_user(self, user_id: str, name: str) -> dict | None:
        async with self.async_session() as session:
            result = await session.execute(
                select(CollectionModel).where(
                    CollectionModel.user_id == user_id,
                    CollectionModel.name == name,
                )
            )
            collection = result.scalar_one_or_none()
            if not collection:
                return None
            return {
                "id": collection.id,
                "name": collection.name,
                "qdrant_collection": collection.qdrant_collection,
                "user_id": collection.user_id,
                "created_at": collection.created_at,
            }

    async def get_cat_count(self, collection_id: str) -> int:
        async with self.async_session() as session:
            result = await session.execute(
                select(func.count(CatModel.id)).where(
                    CatModel.collection_id == collection_id,
                    CatModel.is_active.is_(True),
                )
            )
            return result.scalar() or 0


class CatRepository:
    def __init__(self, async_session_factory):
        self.async_session = async_session_factory

    @staticmethod
    def hash_key(key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    async def validate(self, key: str) -> dict | None:
        async with self.async_session() as session:
            key_hash = self.hash_key(key)
            result = await session.execute(
                select(CatModel).where(
                    CatModel.key_hash == key_hash,
                    CatModel.is_active,
                )
            )
            api_key = result.scalar_one_or_none()

            if api_key:
                if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                    return None

                collection_result = await session.execute(
                    select(CollectionModel).where(CollectionModel.id == api_key.collection_id)
                )
                collection = collection_result.scalar_one_or_none()

                if not collection:
                    return None

                api_key.last_used = datetime.utcnow()
                await session.commit()

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

    async def get_by_id(self, key_id: str) -> dict | None:
        async with self.async_session() as session:
            result = await session.execute(select(CatModel).where(CatModel.id == key_id))
            api_key = result.scalar_one_or_none()
            if not api_key:
                return None

            collection_result = await session.execute(
                select(CollectionModel).where(CollectionModel.id == api_key.collection_id)
            )
            collection = collection_result.scalar_one_or_none()

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

    async def create(
        self,
        label: str,
        collection_id: str,
        user_id: str | None = None,
        permission: Permission = Permission.READ_WRITE,
        expires_in_days: int | None = None,
    ) -> tuple[str, str]:
        async with self.async_session() as session:
            key = generate_cat_token()
            key_hash = hash_cat_token(key)

            expires_at = None
            if expires_in_days is not None:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            elif settings.api_key_default_expiry_days is not None:
                expires_at = datetime.utcnow() + timedelta(
                    days=settings.api_key_default_expiry_days
                )

            api_key = CatModel(
                key_hash=key_hash,
                label=label,
                collection_id=collection_id,
                user_id=user_id,
                permission=permission.value,
                expires_at=expires_at,
            )
            session.add(api_key)
            await session.commit()
            return api_key.id, key

    async def list_all(self, user_id: str | None = None) -> list[dict]:
        async with self.async_session() as session:
            query = select(CatModel)
            if user_id:
                query = query.where(CatModel.user_id == user_id)
            result = await session.execute(query)
            keys = result.scalars().all()

            result_list = []
            for k in keys:
                collection_result = await session.execute(
                    select(CollectionModel).where(CollectionModel.id == k.collection_id)
                )
                collection = collection_result.scalar_one_or_none()

                result_list.append(
                    {
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
                    }
                )
            return result_list

    async def delete(self, key_id: str) -> bool:
        async with self.async_session() as session:
            result = await session.execute(select(CatModel).where(CatModel.id == key_id))
            key = result.scalar_one_or_none()
            if not key:
                return False
            await session.delete(key)
            await session.commit()
            return True

    async def revoke(self, key_id: str) -> bool:
        async with self.async_session() as session:
            result = await session.execute(select(CatModel).where(CatModel.id == key_id))
            key = result.scalar_one_or_none()
            if not key:
                return False
            key.is_active = False
            await session.commit()
            return True

    async def rotate(self, key_id: str) -> tuple[str, str] | None:
        async with self.async_session() as session:
            result = await session.execute(select(CatModel).where(CatModel.id == key_id))
            token = result.scalar_one_or_none()
            if not token:
                return None

            new_key = generate_cat_token()
            key_hash = hash_cat_token(new_key)
            token.key_hash = key_hash

            await session.commit()
            return token.id, new_key

    async def list_by_user(self, user_id: str) -> list[dict]:
        return await self.list_all(user_id=user_id)


class PatTokenRepository:
    def __init__(self, async_session_factory):
        self.async_session = async_session_factory

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    async def validate(self, token: str) -> dict | None:
        async with self.async_session() as session:
            token_hash = self.hash_token(token)
            result = await session.execute(
                select(PatTokenModel).where(
                    PatTokenModel.token_hash == token_hash,
                    PatTokenModel.is_active.is_(True),
                )
            )
            pat_token = result.scalar_one_or_none()

            if not pat_token:
                return None

            if pat_token.expires_at and pat_token.expires_at < datetime.utcnow():
                return None

            user_result = await session.execute(
                select(UserModel).where(UserModel.id == pat_token.user_id)
            )
            user = user_result.scalar_one_or_none()

            if not user or not user.is_active:
                return None

            pat_token.last_used = datetime.utcnow()
            await session.commit()

            return {
                "id": pat_token.id,
                "label": pat_token.label,
                "user_id": pat_token.user_id,
                "scopes": parse_scopes(pat_token.scopes),
                "is_superuser": user.is_superuser,
                "username": user.username,
                "email": user.email,
            }

    async def get_by_id(self, token_id: str) -> dict | None:
        async with self.async_session() as session:
            result = await session.execute(
                select(PatTokenModel).where(PatTokenModel.id == token_id)
            )
            pat_token = result.scalar_one_or_none()
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

    async def create(
        self,
        label: str,
        user_id: str,
        scopes: list[str],
        expires_in_days: int | None = None,
    ) -> tuple[str, str]:
        async with self.async_session() as session:
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
            await session.commit()
            return pat_token.id, token

    async def list_all(self, user_id: str | None = None) -> list[dict]:
        async with self.async_session() as session:
            query = select(PatTokenModel)
            if user_id:
                query = query.where(PatTokenModel.user_id == user_id)
            result = await session.execute(query.order_by(PatTokenModel.created_at.desc()))
            tokens = result.scalars().all()
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

    async def delete(self, token_id: str) -> bool:
        async with self.async_session() as session:
            result = await session.execute(
                select(PatTokenModel).where(PatTokenModel.id == token_id)
            )
            token = result.scalar_one_or_none()
            if not token:
                return False
            await session.delete(token)
            await session.commit()
            return True

    async def revoke(self, token_id: str) -> bool:
        async with self.async_session() as session:
            result = await session.execute(
                select(PatTokenModel).where(PatTokenModel.id == token_id)
            )
            token = result.scalar_one_or_none()
            if not token:
                return False
            token.is_active = False
            await session.commit()
            return True

    async def rotate(self, token_id: str) -> tuple[str, str] | None:
        async with self.async_session() as session:
            result = await session.execute(
                select(PatTokenModel).where(PatTokenModel.id == token_id)
            )
            token = result.scalar_one_or_none()
            if not token:
                return None

            new_token = generate_pat_token()
            token_hash = hash_pat_token(new_token)
            token.token_hash = token_hash

            await session.commit()
            return token.id, new_token

    async def list_by_user(self, user_id: str) -> list[dict]:
        return await self.list_all(user_id=user_id)


_engine = None
_async_session_factory = None


def get_async_session_factory():
    global _engine, _async_session_factory
    if _engine is None:
        from shared.db.models import get_db_engine

        _engine = get_db_engine(settings.database_url)
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_factory


def get_document_repository(collection_id: str | None = None) -> DocumentRepository:
    async_session = get_async_session_factory()
    return DocumentRepository(async_session, collection_id)


def get_cat_repository() -> CatRepository:
    async_session = get_async_session_factory()
    return CatRepository(async_session)


def get_user_repository() -> UserRepository:
    async_session = get_async_session_factory()
    return UserRepository(async_session)


def get_collection_repository() -> CollectionRepository:
    async_session = get_async_session_factory()
    return CollectionRepository(async_session)


def get_pat_token_repository() -> PatTokenRepository:
    async_session = get_async_session_factory()
    return PatTokenRepository(async_session)
