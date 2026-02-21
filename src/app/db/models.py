import hashlib
import uuid
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import JSON, Boolean, DateTime, String, Text, create_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

Base = declarative_base()


class DocumentModel(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(20), default="markdown")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    doc_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    qdrant_point_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class ApiKeyModel(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    qdrant_collection: Mapped[str] = mapped_column(String(100), nullable=False, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class DocumentCreate(BaseModel):
    api_key_id: str
    title: str
    content: str
    document_type: str = "markdown"
    doc_metadata: dict = {}


class DocumentResponse(BaseModel):
    id: str
    api_key_id: str
    title: str
    content: str
    document_type: str
    created_at: datetime
    updated_at: datetime
    doc_metadata: dict


class ChunkData(BaseModel):
    document_id: str
    chunk_index: int
    content: str
    token_count: int
    title: str


def get_db_engine(db_path: str):
    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})


def init_db(db_path: str):
    engine = get_db_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
