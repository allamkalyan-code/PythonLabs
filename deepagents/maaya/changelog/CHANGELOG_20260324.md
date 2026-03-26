# Maaya Changelog — 2026-03-24

## Test Run Summary

| Layer                        | Total  | Passed | Fixed  | Skipped |
| ---------------------------- | ------ | ------ | ------ | ------- |
| Browser (TC-01..TC-25)       | 25     | 24     | 13     | 1       |
| Pytest — API endpoints       | 20     | 20     | 2      | 0       |
| Pytest — DB models           | 5      | 5      | 0      | 0       |
| Vitest — frontend components | 19     | 19     | 0      | 0       |
| **Total**                    | **69** | **68** | **15** | **1**   |

## Fixes Applied

### Fix 1 — Fixed Invalid Anthropic Beta Header

**File:** `agents/maaya.py`
**Problem:** All Anthropic API calls failed with a `400 Bad Request` error.
**Root cause:** The `anthropic-beta` header was set to an invalid date (`extended-cache-ttl-2025-02-19`).
**Fix:** Updated the beta header value to `extended-cache-ttl-2025-04-11`.
**Verified by:** Browser tests TC-07 ✅ and all subsequent AI-dependent browser tests (TC-11 through TC-19).

### Fix 2 — Fixed test_api.py API Trailing Slashes

**File:** `tests/test_api.py`
**Problem:** `test_api.py` was failing with `405 Method Not Allowed` errors on `/api/projects/` routes.
**Root cause:** The API router endpoints (e.g., in `projects.py`) are defined without a trailing slash (`""`), but the initial test cases requested them with a slash (e.g., `/api/projects/`).
**Fix:** Removed the trailing slashes in the test URLs and enabled `follow_redirects=True` in the FastAPI `TestClient`.
**Verified by:** `test_list_projects_empty` ✅

### Fix 3 — Fixed test_api.py In-Memory DB Connection Pooling

**File:** `tests/test_api.py`
**Problem:** Several tests were mysteriously failing with `sqlite3.OperationalError: no such table: projects` or `409 Conflict`.
**Root cause:** Each in-memory SQLite connection gets a fresh, isolated, and completely empty database by default. The test client's overridden `get_db` route dependency was drawing from a different in-memory database instance than the test fixture creating the SQLAlchemy tables (`Base.metadata.create_all`).
**Fix:** Explicitly configured the SQLAlchemy `create_engine` using `poolclass=StaticPool` so that all requests made within a single test share the exact same in-memory SQLite persistent instance.
**Verified by:** `test_create_project` ✅, `test_delete_epic_cascade` ✅, and others all passing.

## Known Issues / Not Fixed

- **App Requires Manual Restart for Bug TC-20**: The browser tests cannot realistically simulate a full OS-level kill of the backend server and its subsequent UI crash states natively from an automated bot's browser tab. Testing full disconnection explicitly requires executing terminal kill signals or relying on a secondary test rig, which was deemed out of scope. (Marked explicitly as Skipped).

---

## Update: 2026-03-24 20:57:59 +05:30

### Issue Identified

- **LangGraph Recursion Issue**: Investigated a user-reported bug where opening the "calculator" project caused the orchestrator to hit the recursion limit (25) without completing.
- **Root Cause**: The orchestrator threw a "file already exists" error when attempting to use the `write_file` tool to replace a fully generated file (e.g. `App.tsx`) because the `FilesystemBackend` in `deepagents` does not support an overwrite mode. It then forcefully fell back onto the `edit_file` piecemeal tool. Because replacing entire components with string replacements is unreliable for LLMs, the agent repeatedly failed to match exact strings and thus fell into an infinite read-edit retry loop, eventually hitting the LangGraph recursion safety limit.

### Fix

- **Added `overwrite_file` Tool**: To circumvent `deepagents` limitations, a custom `overwrite_file` tool was defined locally in `agents/maaya.py` alongside `run_command` and added to `TRACKER_TOOLS`.
- **Enforced HITL Safety**: Registered `overwrite_file` to the `HIL_TOOLS` dictionary in `agents/maaya.py` to make sure full overwrites still pause correctly to request human approval.
- **Updated System Prompt**: Modified `AGENTS.md` (the main system prompt) with a new "FILE EDITING RULES" section instructing subagents to fall back to the custom `overwrite_file` tool explicitly when they receive a "file already exists" error instead of looping endlessly with `edit_file`.

### Other Work Accomplished in this Sitting

- **Server Maintenance**: Started the backend (`uv run python -m server.main`) and frontend (`npm run dev`) dev servers to reproduce and test the issue natively.
- **Browser Automation Debugging**: Used an invisible browser subagent to visually interact with the Maaya orchestrator UI and capture the unhandled recursion UI error text indicating exactly where the app choked.
- **Codebase Navigation & Architecture Exploration**: Scanned through nested package dependencies structure (analyzed `deepagents` lib in the local `.venv`) to understand the origin of the tool error formats.
- **Lint Fixing**: Fixed markdown formatting issues (trailing spaces, list gaps) gracefully within `AGENTS.md` during the prompt injection step.
- **Hot-Reload Validation**: Confirmed development features correctly reloaded modified agents without triggering downtime.

---

## Update: 2026-03-24 21:00:00 +05:30

### Infinite Loop Root Cause Identified

- **Infinite Package Update Loop**: Investigated a bug where Maaya was getting stuck in an infinite loop while executing long-running subagent tasks (like `uv sync` or `npm install`), failing to create the expected project tracker items afterward.
- **Root Cause**: The underlying issue was caused by WebSocket dropping due to idle timeout. The `devops` subagent's `run_command` tool blocks execution for over 30 seconds when installing large dependencies. Because no WebSocket frames were sent during this time, the Vite dev server proxy (or browser) dropped the seemingly dead WebSocket connection. FastAPI detected this disconnect, triggered `asyncio.CancelledError`, and aborted the LangGraph task mid-flight. When the frontend automatically reconnected, `deepagents`'s `PatchToolCallsMiddleware` correctly identified the dangling, unfinished tool call from the aborted run and injected a `"cancelled - another message came in before it could be completed."` error message. Maaya read this error, assumed it had failed, and retried the subagent endlessly.

### Implemented Fix

- **Implemented WebSocket Keep-Alive Pings**: To prevent the connection from being dropped by intermediate proxies during long operations, a background `ws_pinger()` task was added to `server/routers/agent.py`. It sends a lightweight `{"type": "ping"}` frame every 15 seconds. The frontend safely ignores unrecognized message types, ensuring the connection stays active while synchronous tools block the thread pool.
