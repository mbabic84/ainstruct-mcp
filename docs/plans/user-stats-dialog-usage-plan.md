# User Stats Dialog - Two-Column Layout Implementation Plan

## Overview

Add usage statistics (from PR #113) to the admin page user stats dialog using a two-column layout design.

## PR #113 Background

Added usage tracking endpoints:
- `GET /api/v1/admin/usage/{user_id}` - Returns current month usage: `{year_month, api_requests, mcp_requests, total_requests}`
- `GET /api/v1/admin/usage/{user_id}/history` - Returns history: `{history: [{year_month, api_requests, mcp_requests, total}]}`

## Files to Modify

| File | Changes |
|------|---------|
| `services/web-ui/src/web_ui/api_client.py` | Add `get_user_usage()` and `get_user_usage_history()` methods |
| `services/web-ui/src/web_ui/pages/admin.py` | Redesign dialog with two-column layout |

---

## Step 1: Add API Client Methods

Add two new methods to `ApiClient` class in `api_client.py`:

```python
def get_user_usage(self, user_id: str, year_month: str = None) -> httpx.Response:
    params = {}
    if year_month:
        params["year_month"] = year_month
    return self._request("GET", f"/api/v1/admin/usage/{user_id}", params=params)

def get_user_usage_history(self, user_id: str, months: int = 6) -> httpx.Response:
    return self._request("GET", f"/api/v1/admin/usage/{user_id}/history", params={"months": months})
```

---

## Step 2: Redesign Dialog in admin.py

Replace the existing dialog (lines 37-60) with:

1. **Expand dialog width** to `w-[700px]`
2. **Header row**: Username + Status badge (Active/Inactive)
3. **Two-column grid** using `ui.grid().classes("w-full grid-cols-2 gap-6")`

**Left Column (User Resources):**
- Collections count with icon
- Documents count with icon
- PATs with active/inactive breakdown
- CATs with active/inactive breakdown

**Right Column (Usage Stats):**
- "This Month's Usage" heading
- Three metric cards in a row: API | MCP | Total
- "History" heading
- Simple table: Month | API | MCP | Total

---

## Step 3: Update show_user_stats Function

Modify to:
1. Fetch usage data via new API methods
2. Update all the new UI elements
3. Handle missing usage data gracefully

---

## Dialog Preview

```
┌─────────────────────────────────────────────────────────────┐
│  👤 johndoe                              ● Active (green)   │
├──────────────────────────┬──────────────────────────────────┤
│  📁 Collections: 5        │  📊 This Month's Usage          │
│  📄 Documents: 23        │  ┌────────┐ ┌────────┐ ┌─────┐ │
│  🔑 PATs: 2 active       │  │   45   │ │   30   │ │ 75  │ │
│  🔐 CATs: 4 active      │  │  API    │ │  MCP   │ │Total│ │
│                          │  └────────┘ └────────┘ └─────┘ │
│                          ├──────────────────────────────────┤
│                          │  📈 History                     │
│                          │  Month  │ API │ MCP │ Total    │
│                          │  2026-03│  45 │  30 │    75    │
│                          │  2026-02│  38 │  25 │    63    │
└──────────────────────────┴──────────────────────────────────┘
```

## Benefits

1. **Usage is prominent** - It's the new feature, gets the larger right column
2. **Visual summary cards** - Numbers stand out, easy to scan
3. **History table is compact** - Last 6 months in a simple table
4. **Less visual clutter** - No tabs needed, everything visible at once
