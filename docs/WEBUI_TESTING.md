# WebUI Testing Guide

This guide covers testing the WebUI service deployed in the DEV environment.

## DEV Environment

- **URL**: https://ainstruct-dev.kralicinora.cz
- **WebUI Port** (local Docker): 9080

## Deploying with Docker Compose

### Starting Services

From the `deploy/dev` directory, start all services:

```bash
cd deploy/dev
docker compose up -d
```

### Checking Service Status

```bash
docker compose ps
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web_ui
docker compose logs -f rest_api
```

### Stopping Services

```bash
docker compose down
```

### Rebuilding Services

If you've made code changes:

```bash
docker compose up -d --build
```

### Common Issues

- **Port conflicts**: Check if ports 5432, 6333, 9000, 9001, 9080 are available
- **Database not ready**: Wait a few seconds after starting postgres before other services
- **Reset everything**: `docker compose down -v` (removes volumes too)

| Service   | Port | Description |
|-----------|------|-------------|
| postgres  | 5432 | Database |
| qdrant    | 6333 | Vector store |
| mcp_server| 9000 | MCP server |
| rest_api  | 9001 | REST API |
| web_ui    | 9080 | WebUI frontend |

## Testing with Playwright

### Prerequisites

This project provides Playwright MCP tools for browser automation. Available tools:
- `playwright_browser_navigate` - Navigate to URL
- `playwright_browser_click` - Click element
- `playwright_browser_type` - Type text
- `playwright_browser_snapshot` - Get accessibility snapshot
- `playwright_browser_take_screenshot` - Take screenshot
- `playwright_browser_console_messages` - Get console messages
- `playwright_browser_wait_for` - Wait for text
- `playwright_browser_resize` - Resize viewport
- `playwright_browser_install` - Install browser (if needed)

If tools are unavailable, ask the user how to proceed.

### Example Test Workflow (MCP Tools)

Using available Playwright MCP tools to test the homepage:

```
1. playwright_browser_navigate(url="https://ainstruct-dev.kralicinora.cz")
2. playwright_browser_snapshot()
3. playwright_browser_take_screenshot(filename="homepage.png")
4. playwright_browser_console_messages()
```

### Common Interactions (MCP Tools)

Use these available MCP tools for browser automation:

| Action | MCP Tool |
|--------|----------|
| Navigate to URL | `playwright_browser_navigate` |
| Click element | `playwright_browser_click` |
| Type text | `playwright_browser_type` |
| Get page snapshot | `playwright_browser_snapshot` |
| Take screenshot | `playwright_browser_take_screenshot` |
| Get console errors | `playwright_browser_console_messages` |
| Wait for text | `playwright_browser_wait_for` |
| Resize viewport | `playwright_browser_resize` |

### Debugging

- Use `playwright_browser_snapshot` to get current page state
- Use `playwright_browser_console_messages` to check for JavaScript errors
- Use `playwright_browser_take_screenshot` to capture visual state

## Manual Testing Checklist

1. Homepage loads correctly
2. Navigation menu works
3. User can log in / log out
4. Forms submit correctly
5. Error states display properly
6. Responsive design works on mobile viewport
7. API calls complete without console errors
