import hashlib
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from ..config import settings
from .models import (
    ApiKeyModel,
    DocumentCreate,
    DocumentModel,
    DocumentResponse,
    compute_content_hash,
    init_db,
)


class DocumentRepository:
    def __init__(self, engine, api_key_id: str | None = None):
        self.SessionLocal = sessionmaker(bind=engine)
        self.api_key_id = api_key_id

    def _get_session(self) -> Session:
        return self.SessionLocal()

    def create(self, doc: DocumentCreate) -> DocumentResponse:
        session = self._get_session()
        try:
            content_hash = compute_content_hash(doc.content)

            existing = session.execute(
                select(DocumentModel).where(
                    DocumentModel.content_hash == content_hash,
                    DocumentModel.api_key_id == doc.api_key_id,
                )
            ).scalar_one_or_none()

            if existing:
                return DocumentResponse(
                    id=existing.id,
                    api_key_id=existing.api_key_id,
                    title=existing.title,
                    content=existing.content,
                    document_type=existing.document_type,
                    created_at=existing.created_at,
                    updated_at=existing.updated_at,
                    doc_metadata=existing.doc_metadata or {},
                )

            db_doc = DocumentModel(
                api_key_id=doc.api_key_id,
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
                api_key_id=db_doc.api_key_id,
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
            if self.api_key_id:
                query = query.where(DocumentModel.api_key_id == self.api_key_id)

            db_doc = session.execute(query).scalar_one_or_none()
            if not db_doc:
                return None
            return DocumentResponse(
                id=db_doc.id,
                api_key_id=db_doc.api_key_id,
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
            if self.api_key_id:
                query = query.where(DocumentModel.api_key_id == self.api_key_id)

            docs = session.execute(
                query.limit(limit).offset(offset)
            ).scalars().all()

            return [
                DocumentResponse(
                    id=d.id,
                    api_key_id=d.api_key_id,
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
            if self.api_key_id:
                query = query.where(DocumentModel.api_key_id == self.api_key_id)

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
            if self.api_key_id:
                query = query.where(DocumentModel.api_key_id == self.api_key_id)

            db_doc = session.execute(query).scalar_one_or_none()
            if db_doc:
                db_doc.qdrant_point_id = ",".join(point_ids)
                session.commit()
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
                api_key.last_used = datetime.utcnow()
                session.commit()
                return {
                    "id": api_key.id,
                    "label": api_key.label,
                    "qdrant_collection": api_key.qdrant_collection,
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
            return {
                "id": api_key.id,
                "label": api_key.label,
                "qdrant_collection": api_key.qdrant_collection,
                "is_active": api_key.is_active,
            }
        finally:
            session.close()

    def create(self, key: str, label: str, qdrant_collection: str | None = None) -> str:
        session = self._get_session()
        try:
            key_hash = self.hash_key(key)
            collection = qdrant_collection or str(uuid.uuid4())
            api_key = ApiKeyModel(
                key_hash=key_hash,
                label=label,
                qdrant_collection=collection,
            )
            session.add(api_key)
            session.commit()
            return api_key.id
        finally:
            session.close()

    def list_all(self) -> list[dict]:
        session = self._get_session()
        try:
            keys = session.execute(select(ApiKeyModel)).scalars().all()
            return [
                {
                    "id": k.id,
                    "label": k.label,
                    "qdrant_collection": k.qdrant_collection,
                    "created_at": k.created_at,
                    "last_used": k.last_used,
                    "is_active": k.is_active,
                }
                for k in keys
            ]
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


_engine = None


def get_document_repository(api_key_id: str | None = None) -> DocumentRepository:
    global _engine
    if _engine is None:
        _engine = init_db(settings.db_path)
    return DocumentRepository(_engine, api_key_id)


def get_api_key_repository() -> ApiKeyRepository:
    global _engine
    if _engine is None:
        _engine = init_db(settings.db_path)
    return ApiKeyRepository(_engine)
