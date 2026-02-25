from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, EmailStr


class Permission(StrEnum):
    READ = "read"
    READ_WRITE = "read_write"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


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

    model_config = {"from_attributes": True}


class UserDetailResponse(UserResponse):
    collection_count: int = 0
    pat_count: int = 0
    cat_count: int = 0


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    username: str | None = None
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class CollectionCreate(BaseModel):
    name: str


class CollectionResponse(BaseModel):
    id: str
    name: str
    user_id: str
    document_count: int = 0
    cat_count: int = 0
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CollectionListItem(BaseModel):
    id: str
    name: str
    document_count: int = 0
    cat_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class CollectionListResponse(BaseModel):
    collections: list[CollectionListItem]


class CollectionUpdate(BaseModel):
    name: str


class DocumentCreate(BaseModel):
    title: str
    content: str
    document_type: str = "markdown"
    collection_id: str
    metadata: dict | None = None


class DocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    collection_id: str
    document_type: str
    created_at: datetime
    updated_at: datetime | None = None
    metadata: dict | None = None

    model_config = {"from_attributes": True}


class DocumentListItem(BaseModel):
    id: str
    title: str
    collection_id: str
    document_type: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentListItem]
    total: int
    limit: int
    offset: int


class DocumentUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    document_type: str | None = None
    metadata: dict | None = None


class DocumentStoreResponse(BaseModel):
    id: str
    title: str
    collection_id: str
    chunk_count: int
    token_count: int
    created_at: datetime


class DocumentUpdateResponse(BaseModel):
    id: str
    title: str
    chunk_count: int | None = None
    token_count: int | None = None
    updated_at: datetime


class SearchRequest(BaseModel):
    query: str
    collection_id: str | None = None
    max_results: int = 5
    max_tokens: int = 2000


class SearchResultItem(BaseModel):
    document_id: str
    title: str
    chunk_index: int
    content: str
    score: float
    collection: str


class SearchResponse(BaseModel):
    results: list[SearchResultItem]
    total_results: int
    tokens_used: int
    formatted_context: str


class CatCreate(BaseModel):
    label: str
    collection_id: str
    permission: Permission = Permission.READ_WRITE
    expires_in_days: int | None = None


class CatResponse(BaseModel):
    id: str
    label: str
    token: str | None = None
    collection_id: str
    collection_name: str
    permission: Permission
    created_at: datetime
    expires_at: datetime | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class CatListItem(BaseModel):
    id: str
    label: str
    collection_id: str
    collection_name: str
    permission: Permission
    created_at: datetime
    expires_at: datetime | None = None
    is_active: bool
    last_used: datetime | None = None

    model_config = {"from_attributes": True}


class CatListResponse(BaseModel):
    tokens: list[CatListItem]


class PatCreate(BaseModel):
    label: str
    expires_in_days: int | None = None


class PatResponse(BaseModel):
    id: str
    label: str
    token: str | None = None
    user_id: str
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None = None
    is_active: bool
    last_used: datetime | None = None

    model_config = {"from_attributes": True}


class PatListItem(BaseModel):
    id: str
    label: str
    user_id: str
    scopes: list[str]
    created_at: datetime
    expires_at: datetime | None = None
    is_active: bool
    last_used: datetime | None = None

    model_config = {"from_attributes": True}


class PatListResponse(BaseModel):
    tokens: list[PatListItem]


class UserListItem(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    users: list[UserListItem]
    total: int
    limit: int
    offset: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class MessageResponse(BaseModel):
    message: str
