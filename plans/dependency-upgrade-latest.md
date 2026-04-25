# Plan: Upgrade Dependencies to Latest Versions

## Context
- The workspace uses direct dependency lower bounds across `packages/shared` and `services/*` plus a shared `uv.lock`.
- Current runtime skew includes `uvicorn` behind current `websockets`, which already produces deprecation warnings during service startup.
- The goal is to update direct dependencies to the latest available versions, refresh the lockfile, and verify the workspace still builds and tests cleanly.

## Changes
1. Update direct dependency constraints in workspace manifests to current latest versions.
   - Root dev tools in `pyproject.toml`
   - Shared runtime deps in `packages/shared/pyproject.toml`
   - Service runtime deps in `services/mcp-server/pyproject.toml`, `services/rest-api/pyproject.toml`, and `services/web-ui/pyproject.toml`
2. Refresh the workspace lockfile with `uv lock --upgrade` and sync the environment.
3. Run targeted validation.
   - `uv sync --all-packages`
   - `uv run --frozen python -m compileall ...` for touched Python packages if needed
   - `./scripts/test.sh` for full lint, typecheck, and test verification
4. If upgrades introduce breakage, apply the smallest compatible code fixes and rerun verification.

## Files Modified
| File | Change |
|------|--------|
| pyproject.toml | Upgrade dev dependency minimums |
| packages/shared/pyproject.toml | Upgrade shared runtime dependency minimums |
| services/mcp-server/pyproject.toml | Upgrade MCP server dependency minimums |
| services/rest-api/pyproject.toml | Upgrade REST API dependency minimums |
| services/web-ui/pyproject.toml | Upgrade web UI dependency minimums |
| uv.lock | Refresh locked versions after upgrade |

## Verification
- Run `uv lock --upgrade`
- Run `uv sync --all-packages`
- Run `./scripts/test.sh`
- If runtime behavior needs spot checking, rebuild the dev stack with `docker compose up -d --build` from `deploy/dev`
