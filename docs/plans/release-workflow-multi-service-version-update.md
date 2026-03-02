# Release Workflow - Multi-Service Version Update Plan

## Problem

The current release workflow only updates the version in the root `pyproject.toml` using `scripts/update_version.py`. However, with the uv workspace containing multiple services, each service has its own `pyproject.toml` that also needs to be updated with the release version.

## Current State

### Version Mismatch (3 Different Versions!)
- **Root pyproject.toml**: version `3.15.0`
- **src/__init__.py**: `__version__ = "3.8.0"`
- **Service pyproject.toml files**: all at version `3.5.0`
  - `packages/shared/pyproject.toml`
  - `services/mcp-server/pyproject.toml`
  - `services/rest-api/pyproject.toml`
  - `services/web-ui/pyproject.toml`

### Current Flow
1. Release workflow triggers on push to `main`
2. `semantic-release` runs and calls `python scripts/update_version.py ${nextRelease.version}`
3. `update_version.py` only updates:
   - Root `pyproject.toml` (via `update_pyproject_toml()`)
   - `src/__init__.py` (via `update_init_py()`)
4. `.releaserc` commits changes to: `CHANGELOG.md`, `pyproject.toml`, `uv.lock`

### Current Script Issues
1. `update_pyproject_toml()` hardcodes `Path("pyproject.toml")` - cannot update other files
2. Workspace member versions are never updated
3. Script docstring is outdated (mentions only root pyproject.toml)

## Plan

### 1. Update `scripts/update_version.py`

#### a) Modify `update_pyproject_toml()` to accept a path parameter

```python
def update_pyproject_toml(version: str, pyproject_path: Path | None = None) -> None:
    """Update version in pyproject.toml [project] section only."""
    pyproject_path = pyproject_path or Path("pyproject.toml")
    # ... rest of function
```

#### b) Add function to find workspace members

```python
def get_workspace_pyproject_paths() -> list[Path]:
    """Find all workspace member pyproject.toml files."""
    return [
        Path("packages/shared/pyproject.toml"),
        Path("services/mcp-server/pyproject.toml"),
        Path("services/rest-api/pyproject.toml"),
        Path("services/web-ui/pyproject.toml"),
    ]
```

#### c) Update `main()` to iterate over all workspace members

```python
def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python update_version.py <new_version>")
        sys.exit(1)
    
    version = sys.argv[1]
    
    # Update root pyproject.toml
    update_pyproject_toml(version)
    
    # Update src/__init__.py
    update_init_py(version)
    
    # Update all workspace member pyproject.toml files
    for pyproject_path in get_workspace_pyproject_paths():
        update_pyproject_toml(version, pyproject_path)
    
    print(f"Version updated to {version}")
```

### 2. Update `.releaserc`

Add all workspace pyproject.toml files to the git assets array:

```json
"assets": [
  "CHANGELOG.md",
  "pyproject.toml",
  "src/__init__.py",
  "packages/shared/pyproject.toml",
  "services/mcp-server/pyproject.toml",
  "services/rest-api/pyproject.toml",
  "services/web-ui/pyproject.toml",
  "uv.lock"
]
```

### 3. Decision: Keep or Remove `src/__init__.py`?

**Option A: Keep it** (Recommended)
- Some tools expect `__version__` in `__init__.py`
- Already working, just needs to stay in sync
- Low maintenance overhead

**Option B: Remove it**
- Single source of truth (pyproject.toml only)
- Slightly simpler script
- May break tools expecting `__version__`

**Recommendation**: Keep `src/__init__.py` since it already exists and is functional.

## Implementation Steps

1. Modify `scripts/update_version.py`:
   - Add `path` parameter to `update_pyproject_toml()`
   - Add `get_workspace_pyproject_paths()` function
   - Update `main()` to iterate over workspace members
   - Update docstring to reflect all updated files

2. Modify `.releaserc`:
   - Add all workspace pyproject.toml files to assets array
   - Add `src/__init__.py` to assets array

3. Test locally:
   ```bash
   python scripts/update_version.py 3.16.0
   ```
   - Verify all pyproject.toml files are updated
   - Verify src/__init__.py is updated
   - Run `git diff` to confirm changes

## Alternative Considerations

- **Version strategy**: Use shared version (all services use monorepo version) - this is the chosen approach
- **Independent versions**: Could be considered but adds complexity to the release process
