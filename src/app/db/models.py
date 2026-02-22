from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Scope(StrEnum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class Permission(StrEnum):
    READ = "read"
    READ_WRITE = "read_write"


class CollectionModel(Base):
    __tablename__ = "collections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    qdrant_collection: Mapped[str] = mapped_column(String(100), nullable=False, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped[UserModel] = relationship("UserModel", back_populates="collections")
    api_keys: Mapped[list[ApiKeyModel]] = relationship("ApiKeyModel", back_populates="collection")
    documents: Mapped[list[DocumentModel]] = relationship("DocumentModel", back_populates="collection")


class DocumentModel(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_id: Mapped[str] = mapped_column(String(36), ForeignKey("collections.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(20), default="markdown")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    doc_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    qdrant_point_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    collection: Mapped[CollectionModel] = relationship("CollectionModel", back_populates="documents")


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    collections: Mapped[list[CollectionModel]] = relationship("CollectionModel", back_populates="user")
    api_keys: Mapped[list[ApiKeyModel]] = relationship("ApiKeyModel", back_populates="user")


class ApiKeyModel(Base):
    __tablename__ = "api_keys"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    collection_id: Mapped[str] = mapped_column(String(36), ForeignKey("collections.id"), nullable=False, index=True)
    permission: Mapped[str] = mapped_column(String(20), nullable=False, default=Permission.READ_WRITE.value)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[UserModel | None] = relationship("UserModel", back_populates="api_keys")
    collection: Mapped[CollectionModel] = relationship("CollectionModel", back_populates="api_keys")


class CollectionCreate(BaseModel):
    name: str


class CollectionResponse(BaseModel):
    id: str
    name: str
    document_count: int
    api_key_count: int
    created_at: datetime


class CollectionListResponse(BaseModel):
    id: str
    name: str
    created_at: datetime


class DocumentCreate(BaseModel):
    collection_id: str
    title: str
    content: str
    document_type: str = "markdown"
    doc_metadata: dict = {}


class DocumentResponse(BaseModel):
    id: str
    collection_id: str
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


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    is_superuser: bool
    created_at: datetime


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class ApiKeyCreate(BaseModel):
    label: str
    collection_id: str
    permission: Permission = Permission.READ_WRITE
    expires_in_days: int | None = None


class ApiKeyResponse(BaseModel):
    id: str
    label: str
    key: str | None = None
    collection_id: str
    collection_name: str
    permission: Permission
    created_at: datetime
    expires_at: datetime | None
    is_active: bool
    last_used: datetime | None


class ApiKeyListResponse(BaseModel):
    id: str
    label: str
    collection_id: str
    collection_name: str
    permission: Permission
    created_at: datetime
    expires_at: datetime | None
    is_active: bool
    last_used: datetime | None


def get_db_engine(db_path: str):
    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})


def init_db(db_path: str):
    engine = get_db_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def compute_content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    return f"ak_live_{secrets.token_urlsafe(32)}"


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def parse_scopes(scopes_str: str) -> list[Scope]:
    if not scopes_str:
        return [Scope.READ]
    return [Scope(s.strip()) for s in scopes_str.split(",") if s.strip() in [scope.value for scope in Scope]]


def scopes_to_str(scopes: list[Scope]) -> str:
    return ",".join(s.value for s in scopes)
