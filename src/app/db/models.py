import hashlib
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, Boolean, create_engine
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic import BaseModel

Base = declarative_base()


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key_id = Column(String(36), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)
    document_type = Column(String(20), default="markdown")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    doc_metadata = Column(JSON, default={})
    qdrant_point_id = Column(String(36), nullable=True)


class ApiKeyModel(Base):
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key_hash = Column(String(64), nullable=False, unique=True, index=True)
    label = Column(String(100), nullable=False)
    qdrant_collection = Column(String(100), nullable=False, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)


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
