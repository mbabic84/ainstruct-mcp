# Add Collection Name to Documents Table

## Goal
Add a "Collection" column to the table on the `/documents` page of the web-ui service, showing which collection each document belongs to.

## Current State
- **API** (`/api/v1/documents`): Returns `DocumentListItem` with fields: `id`, `title`, `collection_id`, `document_type`, `created_at`, `updated_at`
- **Frontend** (`/documents` page): Table shows columns: Title, Type, Created, Actions

## Implementation Steps

### Backend Changes (`rest-api` service)

#### 1. Update `schemas.py`
- **File**: `services/rest-api/src/rest_api/schemas.py`
- **Change**: Add `collection_name: str | None` field to `DocumentListItem` class (around line 113-119)

#### 2. Update `routes/documents.py`
- **File**: `services/rest-api/src/rest_api/routes/documents.py`
- **Change**: Modify `list_documents` endpoint to populate `collection_name`:
  - Fetch collections to build a `collection_id → collection_name` mapping
  - Update the list comprehension to include `collection_name`

### Frontend Changes (`web-ui` service)

#### 3. Update `app.py`
- **File**: `services/web-ui/src/web_ui/app.py`
- **Change**: Update the `/documents` page table (around line 576-596):
  - Add a "Collection" column definition after "Title"
  - Include `collection_name` in the rows data

## Files Modified
1. `services/rest-api/src/rest_api/schemas.py`
2. `services/rest-api/src/rest_api/routes/documents.py`
3. `services/web-ui/src/web_ui/app.py`
