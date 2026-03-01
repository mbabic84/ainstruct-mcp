# Register Page Layout Fix Plan

## Problem

The register page (`/register`) has a structural bug where the button and "Already have an account?" link are placed **outside** the `ui.card()` context manager, causing them to render outside the card container.

**Location:** `services/web-ui/src/web_ui/app.py:279-311`

### Current Broken Structure

```python
@ui.page("/register")
def register_page():
    with ui.column().classes("w-full h-screen justify-center items-center"):
        with ui.card().classes("w-full max-w-md p-8"):
            # Form inputs INSIDE card
            ...
    # BUG: These are OUTSIDE the card!
    async def try_register():  # line 295
    ui.button("Register", ...)  # line 309
    ui.label("Already have an account?")  # line 310
    ui.button("Login", ...)  # line 311
```

## Solution

Move all elements inside the `with ui.card()` context, matching the login page structure.

### Changes Required

1. **Move `try_register` function** - Move definition inside the card context (before or after error_label)

2. **Move UI elements inside card:**
   - Register button (line 309)
   - "Already have an account?" label (line 310)
   - Login button (line 311)

3. **Add missing styling for consistency with login page:**
   - Add `.props("color=primary")` to register button
   - Add `.classes("mt-4")` to register button (like login has)
   - Wrap "Already have an account?" + Login button in `with ui.row().classes("w-full justify-center gap-2 mt-4")`

## Expected Result

Register page will have identical layout structure to login page - all form elements and actions contained within the card container, properly centered on screen.

## Testing

After fix, verify:
1. Register page renders correctly with all elements inside the card
2. Form validation works (password mismatch error)
3. Navigation to login works after clicking "Login" link
4. Registration flow completes successfully
