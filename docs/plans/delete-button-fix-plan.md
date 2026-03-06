# Fix Plan: Delete Button on /documents Page

**Date:** 2026-03-02  
**Status:** Draft  
**Priority:** High

## Issue Description

The delete button on the `/documents` page does nothing when clicked. The button appears in the table but clicking it has no effect.

## Root Cause Analysis

The delete button implementation has two problems:

1. **Missing event handler on table** - The `handle_delete` function is defined but never connected to the table
2. **Incorrect event emission in slot** - Uses `$emit()` instead of `$parent.$emit()`, preventing the event from bubbling up to the table

### Affected Code Locations

- `/documents` page: `services/web-ui/src/web_ui/app.py:632-640`
- `/collections` page: `services/web-ui/src/web_ui/app.py:519-527` (same bug)

### Comparison with Working Code

The tokens page uses the same pattern correctly (lines 920-932):

```python
pat_table = (
    ui.table(...)
    .on("rotate-click", rotate_pat)     # Handler attached
    .on("revoke-click", revoke_pat)
)
pat_table.add_slot(
    "body-cell-actions",
    """<q-td :props="props">
        <q-btn ... @click.stop="$parent.$emit('rotate-click', props.row)" />  # $parent.$emit used
    </q-td>""",
)
```

## Proposed Fix

### 1. Add event handler to documents table

**File:** `services/web-ui/src/web_ui/app.py`  
**Line:** ~632

Change:
```python
table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")
```

To:
```python
table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full").on('row-click', handle_delete)
```

### 2. Fix event emission in documents slot

**File:** `services/web-ui/src/web_ui/app.py`  
**Line:** ~637

Change:
```python
<q-btn flat round color="negative" icon="delete" @click.stop="$emit('row-click', props.row)" />
```

To:
```python
<q-btn flat round color="negative" icon="delete" @click.stop="$parent.$emit('row-click', props.row)" />
```

### 3. Apply same fixes to collections page

**File:** `services/web-ui/src/web_ui/app.py`  
**Lines:** ~519-527

Apply the same two fixes to the collections page delete functionality.

### 4. Improve confirmation dialog (Recommended)

The current `ui.confirm()` is functional but basic. The tokens page uses a better pattern that shows:
- The item name being deleted
- A "This action cannot be undone" warning
- Explicit Cancel/Revoke buttons

**Current implementation (lines 618-626):**
```python
def handle_delete(e):
    doc_id = e.args["id"]
    if ui.confirm("Are you sure you want to delete this document?"):
        response = api_client.delete_document(doc_id)
        ...
```

**Recommended improvement:**
```python
def handle_delete(e):
    doc_id = e.args["id"]
    doc_title = e.args.get("title", "this document")
    with ui.dialog() as dialog, ui.card():
        ui.label(f"Delete '{doc_title}'?").classes("text-lg font-bold")
        ui.label("This action cannot be undone.").classes("text-sm text-grey-7")
        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button(
                "Delete",
                on_click=lambda: [dialog.close(), _do_delete(doc_id)],
            ).props("color=negative")

    def _do_delete(doc_id):
        response = api_client.delete_document(doc_id)
        if response.status_code == 200:
            ui.notify("Document deleted")
            ui.navigate.reload()
        else:
            ui.notify(f"Error: {response.text}", type="negative")

    dialog.open()
```

Apply the same pattern to the collections page delete confirmation.

## Testing Checklist

- [ ] Test delete button on `/documents` page
- [ ] Test delete button on `/collections` page
- [ ] Verify delete confirmation dialog works
- [ ] Verify page reloads after successful delete
- [ ] Verify error handling for failed delete

## Notes

- The `handle_edit` function exists (lines 628-630) but no edit button is added to the actions slot. This could be added as a follow-up improvement.
- The improved confirmation dialog pattern follows the existing convention used on the tokens page (lines 836-856).
