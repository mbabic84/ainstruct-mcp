# WebUI Documentation

## Overview

The WebUI is a user dashboard for AI Document Memory, built with [NiceGUI](https://nicegui.io/) (a Python UI framework that renders to the browser). It provides a web interface for managing collections, documents, and API tokens.

## Architecture

### Tech Stack
- **Frontend Framework**: NiceGUI 2.x - Python-based UI that compiles to Quasar/Vue components
- **Backend**: Python FastAPI (served alongside the WebUI)
- **Authentication**: JWT tokens (access + refresh) stored in browser local storage

### Key Files

| File | Purpose |
|------|---------|
| `services/web-ui/src/web_ui/app.py` | Main application (~910 lines) - all page routes and UI components |
| `services/web-ui/src/web_ui/api_client.py` | HTTP client for REST API calls with token management |
| `services/web-ui/pyproject.toml` | Package configuration |

## Pages and Routes

| Route | Function | Description |
|-------|----------|-------------|
| `/login` | `login_page()` | User login form |
| `/register` | `register_page()` | User registration |
| `/` | `index_page()` | Redirects to login or dashboard |
| `/dashboard` | `dashboard_page()` | User dashboard with stats |
| `/collections` | `collections_page()` | List/create/delete collections |
| `/documents` | `documents_page()` | List documents, create new |
| `/documents/{doc_id}/edit` | `edit_document_page()` | Edit document content |
| `/tokens` | `tokens_page()` | Manage PAT (Personal Access Tokens) and CAT (Collection Access Tokens) |

## Authentication Flow

1. User enters credentials on `/login`
2. API returns `access_token` and `refresh_token`
3. Tokens stored in `app.storage.user` (browser local storage)
4. `api_client` automatically includes tokens in API requests
5. If `access_token` expires, `api_client` uses `refresh_token` to get new tokens

### Key Functions

```python
def is_logged_in() -> bool  # Check if user has access_token
def require_auth() -> bool  # Redirect to /login if not authenticated
def require_admin() -> bool  # Check if user is superuser
```

## API Client

The `ApiClient` class (`api_client.py`) handles all HTTP communication with the REST API:

```python
api_client = ApiClient(hostname=API_HOSTNAME)

# Authentication
api_client.login(username, password)
api_client.register(username, email, password)
api_client.refresh(refresh_token)

# Collections
api_client.list_collections()
api_client.create_collection(name)
api_client.delete_collection(collection_id)

# Documents
api_client.list_documents(collection_id=None, limit=50, offset=0)
api_client.create_document(title, content, collection_id, document_type="markdown")
api_client.get_document(document_id)
api_client.update_document(document_id, title=None, content=None)
api_client.delete_document(document_id)

# Tokens
api_client.list_pats()
api_client.create_pat(label, expires_in_days=None)
api_client.revoke_pat(pat_id)
api_client.rotate_pat(pat_id)
api_client.list_cats()
api_client.create_cat(label, collection_id, permission, expires_in_days=None)
api_client.revoke_cat(cat_id)
api_client.rotate_cat(cat_id)
```

## UI Patterns

### Dialogs (Modals)

Used for important information that requires user action:

```python
with ui.dialog() as dialog, ui.card().classes("w-[500px]"):
    ui.label("Title")
    # content
    ui.button("Close", on_click=dialog.close)
dialog.open()
```

### Notifications

For transient messages:

```python
ui.notify("Operation completed", type="positive")  # success
ui.notify("Error occurred", type="negative")       # error
ui.notify("Warning", type="warning")              # warning
ui.notify("Info", type="info")                     # info
```

### Forms

Input components with validation:

```python
username_input = ui.input("Username").classes("w-full")
password_input = ui.input("Password", password=True, password_toggle_button=True).classes("w-full")

def submit():
    response = api_client.login(username_input.value, password_input.value)
    if response.status_code == 200:
        ui.notify("Login successful")
    else:
        ui.notify(f"Error: {response.text}", type="negative")

ui.button("Login", on_click=submit).props("color=primary")
```

### Tables

For list displays:

```python
columns = [
    {"name": "name", "label": "Name", "field": "name", "align": "left"},
    {"name": "actions", "label": "Actions", "field": "actions", "align": "center"},
]
rows = [
    {"name": "Item 1", "id": "1"},
]
ui.table(columns=columns, rows=rows, row_key="id")
```

### Navigation

```python
ui.navigate.to("/path")    # Navigate to page
ui.navigate.reload()       # Refresh current page
ui.button("Click", on_click=lambda: ui.navigate.to("/target"))
```

## Token Management

The `/tokens` page handles two token types:

### PAT (Personal Access Tokens)
- User-scoped tokens with `read` and `write` scopes
- Created with optional expiration
- Can be revoked or rotated

### CAT (Collection Access Tokens)
- Collection-scoped tokens with `read` or `read_write` permissions
- Optional expiration
- Can be revoked or rotated

**Important**: When creating/rotating tokens, the token is shown in a modal dialog with a Copy button. The user must copy the token immediately as it cannot be retrieved later.

## Styling

The app uses Tailwind CSS classes via Quasar:

- `text-xl font-bold` - Large bold text
- `w-full` - Full width
- `mb-4` - Margin bottom
- `gap-2` - Gap between elements
- `justify-end` - Align to right

Custom CSS is added via `ui.add_css()` at the top of `app.py`.

## Development

### Running Locally

```bash
cd services/web-ui
uv run web-ui
```

The app will start on port 8080 by default.

### Docker Deployment

See [WEBUI_TESTING.md](./WEBUI_TESTING.md) for DEV environment details.

```bash
cd deploy/dev
docker compose up -d web_ui
```

### Key Environment Variables

| Variable | Description |
|----------|-------------|
| `API_HOSTNAME` | REST API URL (e.g., `http://localhost:9001`) |

## Common Patterns

### Error Handling

```python
response = api_client.some_endpoint()
if response.status_code == 200:
    # Success
    data = response.json()
else:
    ui.notify(f"Error: {response.text}", type="negative")
```

### Confirmation Dialogs

```python
if ui.confirm("Are you sure you want to delete this?"):
    # User clicked Yes
    api_client.delete_something()
else:
    # User clicked No
    pass
```

### Async Operations

NiceGUI handlers can be async:

```python
async def fetch_data():
    response = await api_client.some_endpoint()
    # process response
    
ui.button("Fetch", on_click=fetch_data)
```

## Gotchas

1. **Token Display**: Tokens are only shown once upon creation/rotation. Use modal dialogs, not notifications.
2. **Page Reload**: After mutations (create/update/delete), call `ui.navigate.reload()` to refresh the list.
3. **Form Reset**: Clear input values after successful form submission.
4. **Browser Storage**: User data is stored in browser's local storage via NiceGUI's `app.storage.user`.
