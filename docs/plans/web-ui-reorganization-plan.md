# web-ui Service Reorganization Plan

## Overview

Organize the web-ui service from a single-file application into a modular structure following best practices, with compatibility for NiceGUI v3.

## Deployment Strategy: Parallel Versioning

This update creates a **new service** (`web-ui-v2`) alongside the existing `web-ui`, keeping the current version intact. Both versions can be deployed simultaneously for gradual migration.

### Service Structure
```
services/
├── web-ui/           # Current version (NiceGUI v2) - UNCHANGED
│   ├── pyproject.toml
│   └── src/web_ui/
│       ├── __init__.py
│       ├── app.py
│       └── api_client.py
│
└── web-ui-v2/        # New version (NiceGUI v3) - NEW
    ├── pyproject.toml
    └── src/web_ui_v2/
        ├── __init__.py
        ├── app.py
        ├── config.py
        ├── api_client.py
        ├── auth.py
        ├── pages/
        ├── components/
        └── static/
```

### Entrypoint Configuration

| Service | Package Name | CLI Command | Port | Container |
|---------|--------------|-------------|------|-----------|
| web-ui | `ainstruct-web-ui` | `web-ui` | Config default | Separate container |
| web-ui-v2 | `ainstruct-web-ui-v2` | `web-ui-v2` | Config default | Separate container |

Both services run in **separate containers**, so they use the **same default port** from shared configuration. This allows:
- Gradual user migration via container orchestration
- A/B testing via load balancer routing
- Rollback capability (switch container versions)
- Feature comparison

### Entrypoint Setup

**web-ui-v2/pyproject.toml:**
```toml
[project]
name = "ainstruct-web-ui-v2"
version = "1.0.0"
description = "User Dashboard WebUI v2 for AI Document Memory"
requires-python = ">=3.14"
dependencies = [
    "nicegui>=3.8.0,<4.0.0",
    "httpx>=0.28.0",
    "ainstruct-shared",
]

[project.scripts]
web-ui-v2 = "web_ui_v2:main"
```

**web-ui-v2/src/web_ui_v2/__init__.py:**
```python
from .app import create_app
from shared.config import settings

def main():
    app = create_app()
    app.run(port=settings.web_ui_port)  # Same port, different container
```

## Current State

| File | Lines | Contents |
|------|-------|----------|
| `app.py` | ~1384 | All pages, auth, navigation, JS integration |
| `api_client.py` | ~240 | API client wrapper |

### Issues
- Single file contains 9 page handlers, auth logic, navigation, JavaScript integration
- Hard to maintain, test, and navigate

## NiceGUI Version Upgrade

| Current | Target | Status |
|---------|--------|--------|
| >=2.0.0 | >=3.8.0,<4.0.0 | Major version upgrade |

### Breaking Changes (v2 → v3)

| Change | Impact | Action Required |
|--------|--------|-----------------|
| **Shared auto-index pages removed** | CSS/JS in global scope won't work | Move CSS/JS into page functions |
| **`ui.open` removed** | None (already using `ui.navigate.to`) | None |
| **`run_method()` security fix** (v3.8) | JS expressions in method calls blocked | Use `run_javascript` instead |
| **Script mode introduced** | Apps need proper `@ui.page` or `root` param | Add `@ui.page` decorators |

### Security Fixes (v3.7.0+)

| Version | Fix | Action Required |
|---------|-----|-----------------|
| v3.7.0 | XSS in `ui.markdown()` | Add `sanitize=True` for untrusted content |
| v3.7.0 | Path traversal in `FileUpload.name` | Already fixed in library |
| v3.8.0 | XSS via `run_method()` expressions | Use `run_javascript` pattern |

## New v3 Features to Adopt

### Storage Secret (Required for Auth Sessions)
```python
# Required for app.storage.browser and app.storage.user
ui.run(storage_secret='your-secret-key')
```

Enable server-side session storage instead of manual localStorage:
```python
from nicegui import app

@ui.page('/dashboard')
def dashboard():
    token = app.storage.user.get('access_token')  # Server-side, secure
    ...
```

### Root Parameter (Alternative Entry Point)
```python
# Alternative to @ui.page('/') for single-page apps
def main_page():
    ui.label('Main content')
    
ui.run(root=main_page)
```

### UnoCSS Engine (v3.7.0+)
```python
ui.run(unocss='wind4')  # Options: "mini", "wind3", "wind4"
```
Faster than Tailwind Play CDN, better for smaller pages.

### Global Theming with app.colors (v3.6.0+)
```python
from nicegui import app

app.colors.primary = '#6750A4'
app.colors.secondary = '#625B71'
```

### Dark Mode Element
```python
from nicegui import ui

dark = ui.dark_mode()
ui.switch('Dark mode').bind_value(dark)  # Toggle with binding
```

## Target Structure

```
services/web-ui-v2/src/web_ui_v2/
├── __init__.py           # Package init, exports main()
├── app.py                # Main: CSS/JS includes in page functions, includes routers
├── config.py             # Configuration
├── api_client.py         # API client (copy from web-ui, adapt as needed)
├── auth.py               # Auth helpers (login, register, guards)
├── pages/
│   ├── __init__.py       # Export routers
│   ├── index.py          # Route: /
│   ├── auth.py           # Routes: /auth/login, /auth/register
│   ├── dashboard.py      # Route: /dashboard
│   ├── collections.py    # Route: /collections
│   ├── documents.py      # Routes: /documents, /documents/{id}/edit
│   ├── tokens.py         # Route: /tokens
│   └── admin.py          # Route: /admin
├── components/
│   ├── __init__.py       # Export components
│   ├── nav.py            # Navigation bar
│   └── layout.py         # Page wrapper with CSS/JS includes
└── static/
    └── auth.js           # Token handling (external file)
```

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Deployment** | Parallel service (`web-ui-v2`) | Zero-risk migration, rollback capability |
| **Package Name** | `ainstruct-web-ui-v2` | Distinct from current version |
| **CLI Command** | `web-ui-v2` | Separate entrypoint for v2 |
| **Port** | Shared config default | Same port, different containers |
| **Container** | Separate container per version | Container orchestration handles routing |
| JavaScript | External file (`static/auth.js`) | Best practice 2026 - caching, maintainability |
| Routing | `APIRouter` with prefixes | Proven pattern, matches REST API structure |
| v3 Compatibility | CSS/JS in page functions | Required for v3 (no global UI elements) |
| Entry Point | `@ui.page('/')` on main page | Required for v3 (no auto-index client) |
| Session Storage | `app.storage.user` | Server-side, secure, persists across tabs |
| CSS Engine | UnoCSS `wind4` | Better performance than Tailwind CDN |

## Migration Steps

### Step 0: Create web-ui-v2 Service Directory
- Create `services/web-ui-v2/` directory structure
- Create `services/web-ui-v2/src/web_ui_v2/` package directory
- Create `services/web-ui-v2/tests/` directory

### Step 1: Create pyproject.toml
- Create `services/web-ui-v2/pyproject.toml` with:
  - `name = "ainstruct-web-ui-v2"`
  - `version = "1.0.0"`
  - `nicegui>=3.8.0,<4.0.0`
  - CLI entrypoint: `web-ui-v2 = "web_ui_v2:main"`

### Step 1b: Configure Storage Secret
- Add `storage_secret` parameter to `ui.run()` call
- Use environment variable or settings for the secret value

### Step 2: Create directories
- Create `pages/`, `components/`, `static/` directories under `web_ui_v2/`

### Step 3: Copy and Extract JavaScript
- Copy token handling JS from `web-ui/src/web_ui/app.py` to `web-ui-v2/src/web_ui_v2/static/auth.js`
- Load via `ui.add_body_html('<script src="/auth.js"></script>')` in layout component

### Step 4: Create auth module
- Create `auth.py` with auth helpers (no UI elements at module level)

### Step 5: Create components with CSS/JS
- Create `components/layout.py` with `render_page()` that includes CSS and JS
- All CSS/JS must be inside functions (v3 requirement)

### Step 6: Create pages with APIRouter
- Each page module defines its router with prefix
- All pages use `@router.page()` decorator
- Import layout component to include CSS/JS

### Step 7: Create app.py
- Main entry point with `@ui.page('/')` decorator
- Import and include all routers
- All CSS/JS must be inside page functions (v3 requirement)

### Step 8: Create __init__.py
- Export `main()` function using port from shared configuration

### Step 9: Update Workspace Configuration
- Add `web-ui-v2` to root `pyproject.toml` workspace (if applicable)
- Add `web-ui-v2` to `uv` workspace configuration

## v3-Specific Changes Required

### Before (v2 - Global CSS/JS)
```python
# app.py
ui.add_css("...", shared=True)  # ❌ Won't work in v3
ui.add_head_html("...")          # ❌ Won't work in v3

@ui.page('/')
def index():
    ...
```

### After (v3 - CSS/JS in page function)
```python
# components/layout.py
def render_page(content_fn):
    ui.add_css("...", shared=True)  # ✅ Inside function
    ui.add_head_html("...")          # ✅ Inside function
    with ui.column():
        render_nav()
        content_fn()
```

### Page Definition
```python
# pages/auth.py
from nicegui import APIRouter, ui
from web_ui_v2.components.layout import render_page

router = APIRouter(prefix='/auth')

@router.page('/login')
def login_page():
    render_page(_login_content)

def _login_content():
    # actual login UI
    ...
```

### run_method() Migration (v3.8.0+)
```python
# Before (v2 - now blocked for security)
row = await grid.run_grid_method('(g) => g.getDisplayedRowAtIndex(0).data')

# After (v3.8+)
row = await ui.run_javascript(f'return getElement({grid.id}).api.getDisplayedRowAtIndex(0).data')
```

## Dependencies

- NiceGUI >= 3.8.0, < 4.0.0 (updated from >=2.0.0)
- httpx >= 0.28.0
- ainstruct-shared

## Migration Path

### Phase 1: Development
1. Create `web-ui-v2` service
2. Implement modular structure
3. Test thoroughly in isolation

### Phase 2: Parallel Deployment
1. Build container image for `web-ui-v2`
2. Deploy both containers via orchestration (load balancer routes traffic)
3. Internal testing on v2 container
4. Gradual user migration (percentage-based routing)

### Phase 3: Deprecation
1. Route 100% traffic to `web-ui-v2` container
2. Monitor for issues
3. Remove `web-ui` container after stabilization period

### Rollback Strategy
- Keep `web-ui` container image available during v2 rollout
- Immediate rollback: update load balancer to route traffic back to v1 container
- No data migration required (both use same REST API)

## Testing Checklist

- [ ] All pages load without errors
- [ ] CSS styling applies correctly
- [ ] JavaScript token handling works
- [ ] Navigation between pages works
- [ ] Login/logout flow works
- [ ] Dark mode applies correctly
- [ ] Dark mode toggle persists across sessions
- [ ] Storage persistence across server restarts (`app.storage.user`)
- [ ] Token refresh works with storage secret
- [ ] CSS loads correctly with UnoCSS (if adopted)

## Notes

- **Current `web-ui` service remains unchanged** - no modifications to existing code
- Follow the existing REST API structure in `services/rest-api/`
- APIRouter is still supported in v3 and is the recommended approach for prefix grouping
- `ui.sub_pages` is an alternative for deeply nested routes but not needed here
- All UI element creation must happen inside page functions (v3 requirement)
- Consider migrating from localStorage to `app.storage.user` for auth tokens (server-side, more secure)
- Both services share the same REST API backend (`ainstruct-rest-api`)
