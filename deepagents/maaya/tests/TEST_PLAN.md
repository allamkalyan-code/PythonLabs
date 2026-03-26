# Maaya — Master Test Plan

**Version:** 1.0
**Date:** 2026-03-24
**Coverage:** Browser/UI · REST API · WebSocket · pytest backend · vitest frontend

---

## How to Use This Document

This is the human-readable reference. For the ready-to-paste agent prompt, see
[ANTIGRAVITY_PROMPT.md](ANTIGRAVITY_PROMPT.md).

Test layers:

| Layer | Tool | Count |
| --- | --- | --- |
| Browser / UI | anti-gravity (browser automation) | 25 |
| Backend API | pytest (`maaya/tests/test_api.py`) | 20 |
| DB Models | pytest (`maaya/tests/test_models.py`) | 5 |
| Frontend components | vitest (`frontend/src/__tests__/`) | 17 |
| **Total** | | **67** |

---

## Prerequisites

```bash
# Backend
cd maaya/
uv run python -m server.main          # http://localhost:8000

# Frontend
cd maaya/frontend/
npm run dev                            # http://localhost:5173
```

---

## Layer 1 — Browser / UI Tests

### Area 1 — App Startup

| ID | Steps | Expected |
| --- | --- | --- |
| TC-01 | Navigate to http://localhost:5173 | No JS console errors. Sidebar shows empty state. |
| TC-02 | Check http://localhost:8000/api/projects/models | JSON array of 6 model objects returned. |

### Area 2 — Project Management UI

| ID | Steps | Expected |
| --- | --- | --- |
| TC-03 | Click "New Project" button | Dialog opens with name, path, model dropdown fields. |
| TC-04 | Fill name="test-project", path="C:\temp\test-project", model="Claude Sonnet 4.6" → Create | Dialog closes. Project in sidebar. Chat tab shown. |
| TC-05 | Refresh browser (F5) | Project still in sidebar. Select it → Chat tab loads. |
| TC-06 | Create a second project "project-2" | Both projects in sidebar. Each shows independent state. |

### Area 3 — Chat & WebSocket

| ID | Steps | Expected |
| --- | --- | --- |
| TC-07 | Select "test-project", view Chat tab | "Hi, I'm Maaya" empty state. Status bar shows "Connected" (green). |
| TC-08 | Type "hello", press Enter | "hello" appears right-aligned immediately. Agent responds with AI bubble. |
| TC-09 | Check message list after TC-08 | "hello" appears exactly ONCE (no duplicates). |
| TC-10 | Observe while agent responds | Animated dots + "Maaya is working..." shown. Send button disabled. After response: dots gone, button re-enabled. |
| TC-11 | Type "line1", Shift+Enter, "line2", then Enter | Textarea shows 2 lines before sending. Sent as multi-line message. |
| TC-12 | After any subagent interaction | task_complete message visible showing agent name, input_tokens, output_tokens, cost_usd. |
| TC-13 | Refresh browser, re-select "test-project" | Previous messages reload. "── Previous conversation ──" divider separates history from new messages. |

### Area 4 — DiffViewer Panel

| ID | Steps | Expected |
| --- | --- | --- |
| TC-14 | Ask: "Create a file called hello.txt with: Hello World". Approve HIL. | DiffViewer opens as right panel (50/50 split). Shows "hello.txt", green "write" badge, line content. |
| TC-15 | Wait for streaming to end (done event) | DiffViewer panel closes. Chat returns to full width. |

### Area 5 — Human-in-the-Loop (HIL)

| ID | Steps | Expected |
| --- | --- | --- |
| TC-16 | Ask: "Create hello.txt with Hello World" | HIL modal appears before write. Shows tool=write_file, path, content. |
| TC-17 | Click Approve in modal | Modal closes. File written. DiffViewer opens. |
| TC-18 | Ask: "Create secret.txt with: do not write". Click Reject in modal. | Modal closes. No DiffViewer. File NOT created. Agent continues. |

### Area 6 — Tracker UI

| ID | Steps | Expected |
| --- | --- | --- |
| TC-19 | Ask: "Build a simple todo app with FastAPI and React" | spec-evaluator runs first. Planner creates epics/stories/tasks. |
| TC-20 | Click Tracker tab | At least 1 Epic. Expand → Stories. Expand story → Tasks with status/priority/agent. |
| TC-21 | Click a task's status chip | Cycles: not_started → wip → done → blocked → not_started. |
| TC-22 | Refresh browser, re-select project | Task status is preserved. |

### Area 7 — Error Handling & Resilience

| ID | Steps | Expected |
| --- | --- | --- |
| TC-23 | Stop backend (Ctrl+C). Send a message. | Red error message in chat. Streaming stops cleanly. |
| TC-24 | Restart backend. Send another message. | Status returns to "Connected". Agent responds normally. |

### Area 8 — REST API (DevTools console)

| ID | Command | Expected |
| --- | --- | --- |
| TC-25 | `fetch('/api/projects/').then(r=>r.json()).then(console.log)` | Array of projects including "test-project". |

---

## Layer 2 — Backend API Tests (pytest)

**File to write:** `maaya/tests/test_api.py`
**Run:** `uv run pytest maaya/tests/test_api.py -v` from `maaya/`

### Projects Router

| Test | Endpoint | Assertion |
| --- | --- | --- |
| `test_list_projects_empty` | GET /api/projects/ | Returns `[]` on fresh DB |
| `test_create_project` | POST /api/projects/ | Returns 201, body has `id` |
| `test_get_project` | GET /api/projects/{id} | Returns `name`, `path`, `model` |
| `test_update_project` | PATCH /api/projects/{id} | Updated fields reflected in response |
| `test_delete_project` | DELETE /api/projects/{id} | Returns 204. Subsequent GET returns 404. |
| `test_get_models` | GET /api/projects/models | Array with exactly 6 items, each has `id` + `label` |
| `test_get_messages_empty` | GET /api/projects/{id}/messages | Returns `[]` for new project |
| `test_clear_messages` | DELETE /api/projects/{id}/messages | Returns 204. GET /messages returns `[]`. |

### Tracker Router

| Test | Endpoint | Assertion |
| --- | --- | --- |
| `test_create_epic` | POST /api/tracker/epics | Returns epic with `id`, `title`, `status=not_started` |
| `test_list_epics_project_scoped` | GET /api/tracker/epics?project_id=X | Returns only epics for that project |
| `test_update_epic` | PATCH /api/tracker/epics/{id} | `status=done` persisted |
| `test_delete_epic_cascade` | DELETE /api/tracker/epics/{id} | 204. Stories and tasks under it are gone. |
| `test_create_story` | POST /api/tracker/stories | Returns story with `epic_id`, `id` |
| `test_update_story` | PATCH /api/tracker/stories/{id} | Fields updated correctly |
| `test_delete_story` | DELETE /api/tracker/stories/{id} | 204. Tasks under it are gone. |
| `test_create_task` | POST /api/tracker/tasks | Returns task with `story_id`, `assigned_agent` |
| `test_create_task_parallel_group` | POST with `parallel_group="group_1"` | `parallel_group` stored and returned |
| `test_update_task_status` | PATCH /api/tracker/tasks/{id} | `status=wip` persisted |
| `test_delete_task` | DELETE /api/tracker/tasks/{id} | Returns 204 |
| `test_cascade_delete_epic` | Create epic+story+task, delete epic | All descendants removed |

---

## Layer 2b — DB Model Tests (pytest)

**File to write:** `maaya/tests/test_models.py`
**Run:** `uv run pytest maaya/tests/test_models.py -v` from `maaya/`

| Test | What it checks |
| --- | --- |
| `test_user_memory_create` | `UserMemory(key, value)` stored and retrievable |
| `test_user_memory_upsert` | Setting same key twice does NOT create duplicate — updates in place |
| `test_project_model` | `model` defaults to `"anthropic:claude-sonnet-4-6"` if not set |
| `test_chat_message_persist` | `role`, `content`, `metadata_json` stored; `metadata_json` deserializes to dict |
| `test_task_parallel_group_field` | `parallel_group` is nullable; stores string value correctly |

---

## Layer 3 — Frontend Component Tests (vitest)

**Run:** `npm test` from `maaya/frontend/`

### ChatMessage.test.tsx

| Test | What it checks |
| --- | --- |
| renders human message right-aligned | Human bubble has right-aligned layout class |
| renders ai message with content | AI bubble shows `content` text |
| renders tool message with tool_name | Tool row shows tool name label |
| renders task_complete with token count and cost | Shows input/output tokens and formatted cost string |
| renders error message in red | Error row has red color class |
| renders system divider text | Divider shows content string centered |
| does not render human message as ai bubble | Human type does not get AI bubble styling |

### DiffViewer.test.tsx

| Test | What it checks |
| --- | --- |
| shows empty state when fileDelta is null | Placeholder text visible, no table rendered |
| renders file path in header | `fileDelta.path` shown in header |
| shows write badge with green class when op=write | Badge element has green color class |
| shows edit badge with yellow class when op=edit | Badge element has yellow color class |
| renders correct number of line numbers | Line count matches `content.split('\n').length` |
| highlights + lines green in edit mode | Lines starting with `+` have green bg class |
| highlights - lines red in edit mode | Lines starting with `-` have red bg class |

### HilApproval.test.tsx

| Test | What it checks |
| --- | --- |
| renders tool name from request | `request.tool` displayed in modal |
| renders stringified args | `request.args` shown as JSON |
| Approve button calls onRespond(true) | Click Approve → `onRespond` called with `true` |
| Reject button calls onRespond(false) | Click Reject → `onRespond` called with `false` |

---

## Changelog Format

After all tests pass and fixes are applied, create:

**Path:** `maaya/changelog/CHANGELOG_{YYYYMMDD}.md`

```markdown
# Maaya Changelog — {YYYY-MM-DD}

## Test Run Summary

| Layer | Total | Passed | Fixed | Skipped |
| --- | --- | --- | --- | --- |
| Browser (TC-01..TC-25) | 25 | X | Y | Z |
| Pytest backend | 20 | X | Y | Z |
| Pytest models | 5 | X | Y | Z |
| Vitest frontend | 17 | X | Y | Z |

## Fixes Applied

### Fix N — {title}
**File:** `path/to/file`
**Problem:** ...
**Root cause:** ...
**Fix:** ...
**Verified by:** TC-XX ✅

## Known Issues / Not Fixed
...
```
