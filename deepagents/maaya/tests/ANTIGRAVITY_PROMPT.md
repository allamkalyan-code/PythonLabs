# Anti-Gravity Testing Prompt — Maaya App

Copy everything below this line and paste it into anti-gravity.

---

You are testing the Maaya AI development orchestrator app end-to-end.
Your job has four parts:

- **Part A** — Start the app
- **Part B** — Run 25 browser test cases; fix any failures immediately
- **Part C** — Write and run automated pytest + vitest tests; fix any failures
- **Part D** — Write a changelog summarising everything

Work through each part in order. Do not skip ahead.

---

## PART A — SETUP

Open a terminal in `d:\PythonLabs\deepagents\maaya\` and run:

```
uv run python -m server.main
```

Wait until you see: `Uvicorn running on http://0.0.0.0:8000`

Open a second terminal in `d:\PythonLabs\deepagents\maaya\frontend\` and run:

```
npm run dev
```

Wait until you see: `Local: http://localhost:5173`

Open `http://localhost:5173` in the browser.

---

## PART B — BROWSER TEST CASES

Mark each test ✅ PASS or ❌ FAIL.

**On FAIL:** Fix the root cause in the source code immediately, then re-run only that test.

Source locations:

- Backend: `d:\PythonLabs\deepagents\maaya\server\`
- Frontend: `d:\PythonLabs\deepagents\maaya\frontend\src\`
- Agents: `d:\PythonLabs\deepagents\maaya\agents\`

Restart the backend after any server-side code change.
Vite hot-reloads frontend changes automatically.

---

### [TC-01] Page Load

Navigate to `http://localhost:5173`.

**EXPECT:** No JS errors in browser console. Sidebar shows an empty state (no projects listed).

---

### [TC-02] Models Endpoint

Navigate to `http://localhost:8000/api/projects/models`.

**EXPECT:** JSON array of exactly 6 objects, each with `id` and `label` fields.

---

### [TC-03] New Project Dialog

Click the "New Project" button (or the `+` icon in the sidebar).

**EXPECT:** A dialog opens with three fields: project name, project path, model dropdown.

---

### [TC-04] Create Project

Fill in: name=`test-project`, path=`C:\temp\test-project`, model=`Claude Sonnet 4.6`.
Click Create.

**EXPECT:** Dialog closes. `test-project` appears in the sidebar. Chat panel is shown.

---

### [TC-05] WebSocket Connected

**EXPECT:** Status bar shows a green wifi icon and the text `Connected` within 3 seconds of selecting the project.

---

### [TC-06] Empty Chat State

**EXPECT:** Chat panel shows the heading `Hi, I'm Maaya` and a description. No messages in the list.

---

### [TC-07] Send Simple Message

Type `hello` in the input box. Press Enter.

**EXPECT:**

1. `hello` appears immediately as a right-aligned human message.
2. Status changes to `Maaya is working...` with animated dots.
3. Agent responds with an AI message bubble.

---

### [TC-08] No Duplicate Human Messages

After TC-07, inspect the message list.

**EXPECT:** `hello` appears exactly **once**. No duplicate entries.

---

### [TC-09] Streaming Indicator

While the agent is responding:

**EXPECT:** Animated dots visible below the last message. Send button is disabled (greyed out).

After the response completes:

**EXPECT:** Dots disappear. Send button re-enables.

---

### [TC-10] Shift+Enter Newline

Type `line1`, press Shift+Enter, type `line2`.

**EXPECT:** Textarea shows two lines. The message has NOT been sent yet.

Press Enter (without Shift).

**EXPECT:** Multi-line message is sent and displayed correctly in chat.

---

### [TC-11] Task Complete Message

After any exchange that involves a subagent:

**EXPECT:** A `task_complete` row appears in the chat. It shows: agent name, input token count, output token count, and cost in USD (e.g. `$0.003`).

---

### [TC-12] Plan a Project

Type the following and press Enter:

```
Build a simple todo app with FastAPI backend and React frontend.
```

**EXPECT:**

- AI message mentions the spec-evaluator agent, OR asks clarifying questions.
- If questions are asked: answer them and re-send.
- Eventually: planner creates Epics, Stories, and Tasks (visible in the Tracker tab).

---

### [TC-13] Tracker Tab Populated

Click the **Tracker** tab.

**EXPECT:**

- At least 1 Epic is visible.
- Expanding the Epic shows Stories.
- Expanding a Story shows Tasks.
- Each Task shows: title, status chip, priority, assigned agent.

---

### [TC-14] Status Chip Cycles

Click a task's status chip (e.g. `not_started`).

**EXPECT:** Status advances to `wip`. Click again → `done`. Click again → `blocked`. Click again → `not_started`.

---

### [TC-15] Status Persists After Refresh

After TC-14, refresh the browser (F5). Re-select `test-project`.

**EXPECT:** The task's status is still the last value you set.

---

### [TC-16] HIL Modal — Write File

Go to the **Chat** tab. Type and send:

```
Create a file called hello.txt with the content: Hello World
```

**EXPECT:** Before the file is written, a HIL approval modal appears. The modal shows the tool name (`write_file`), the file path, and the content.

---

### [TC-17] HIL Approve

Click the **Approve** button.

**EXPECT:**

1. Modal closes.
2. DiffViewer panel opens on the right half of the screen.
3. DiffViewer shows: `hello.txt` path, green `write` badge, line numbers, file content.

---

### [TC-18] DiffViewer Closes

Wait for streaming to finish (the `done` event).

**EXPECT:** DiffViewer panel disappears. Chat returns to full width.

---

### [TC-19] HIL Reject

Type and send:

```
Create a file called secret.txt with the content: do not write
```

When the HIL modal appears, click **Reject**.

**EXPECT:** Modal closes. Agent continues but no DiffViewer opens. `secret.txt` is NOT created on disk.

---

### [TC-20] Error Display

Stop the backend (Ctrl+C in the backend terminal). Send any message from the UI.

**EXPECT:** A red error message appears in chat. Streaming stops cleanly.

Restart the backend, then send another message.

**EXPECT:** Status returns to `Connected`. Agent responds normally.

---

### [TC-21] Chat History Reload

Refresh the browser. Select `test-project`.

**EXPECT:** All previous messages reload. A `── Previous conversation ──` divider separates old history from any new messages.

---

### [TC-22] Multiple Projects

Create a second project named `project-2`. Switch between `test-project` and `project-2` in the sidebar.

**EXPECT:** Each project shows its own independent chat history and tracker data.

---

### [TC-23] Model Dropdown

Open the New Project dialog (or project settings if available).

**EXPECT:** The model dropdown lists all 6 options:

- Claude Sonnet 4.6
- Claude Opus 4.6
- Claude Haiku 4.5
- GPT-4o
- GPT-4o Mini
- o3

---

### [TC-24] REST API — Projects

Open browser DevTools → Console. Run:

```javascript
fetch('/api/projects/').then(r=>r.json()).then(console.log)
```

**EXPECT:** Array containing at least `test-project` and `project-2`.

---

### [TC-25] REST API — Tracker

In the DevTools console, run:

```javascript
fetch('/api/tracker/epics?project_id=1').then(r=>r.json()).then(console.log)
```

**EXPECT:** Array of epics with nested stories and tasks for project 1.

---

## PART C — WRITE AND RUN AUTOMATED TESTS

### Step C-1 — Backend pytest tests

Write this file: `d:\PythonLabs\deepagents\maaya\tests\test_api.py`

Use `fastapi.testclient.TestClient` and pytest fixtures.
Use an in-memory SQLite test database — do NOT touch the production DB.

The file must contain these tests (use `pytest.fixture` for client and DB setup):

```
PROJECTS ROUTER
  test_list_projects_empty         GET /api/projects/  →  []
  test_create_project              POST /api/projects/ with {name, path, model}  →  201, id returned
  test_get_project                 GET /api/projects/{id}  →  name/path/model in response
  test_update_project              PATCH /api/projects/{id} with {name: "renamed"}  →  updated name
  test_delete_project              DELETE /api/projects/{id}  →  204; GET returns 404
  test_get_models                  GET /api/projects/models  →  list of exactly 6 items
  test_get_messages_empty          GET /api/projects/{id}/messages  →  [] for new project
  test_clear_messages              DELETE /api/projects/{id}/messages  →  204; GET returns []

TRACKER ROUTER
  test_create_epic                 POST /api/tracker/epics {title, project_id}  →  id, status=not_started
  test_list_epics_project_scoped   GET /api/tracker/epics?project_id=X  →  only that project's epics
  test_update_epic                 PATCH /api/tracker/epics/{id} {status: done}  →  status persisted
  test_delete_epic_cascade         DELETE /api/tracker/epics/{id}  →  204; stories + tasks gone
  test_create_story                POST /api/tracker/stories {epic_id, title}  →  id, epic_id
  test_update_story                PATCH /api/tracker/stories/{id} {title: "new"}  →  updated
  test_delete_story                DELETE /api/tracker/stories/{id}  →  204; tasks gone
  test_create_task                 POST /api/tracker/tasks {story_id, title, assigned_agent}  →  id
  test_create_task_parallel_group  POST with parallel_group="group_1"  →  field stored correctly
  test_update_task_status          PATCH /api/tracker/tasks/{id} {status: wip}  →  persisted
  test_delete_task                 DELETE /api/tracker/tasks/{id}  →  204
  test_cascade_delete_epic         Create epic+story+task, delete epic  →  all descendants removed
```

Also write: `d:\PythonLabs\deepagents\maaya\tests\test_models.py`

```
  test_user_memory_create          UserMemory(key="foo", value="bar") stored; db.get returns it
  test_user_memory_upsert          Set key "foo" twice  →  only 1 row, value=second value
  test_project_model               Project without model  →  default is "anthropic:claude-sonnet-4-6"
  test_chat_message_persist        ChatMessage with metadata_json stored; json.loads returns dict
  test_task_parallel_group_field   Task with parallel_group=None  →  nullable OK; with "group_1"  →  stored
```

Run the tests:

```bash
cd d:\PythonLabs\deepagents\maaya
uv run pytest tests/test_api.py tests/test_models.py -v
```

Fix all failures before continuing.

---

### Step C-2 — Frontend vitest tests

Write: `d:\PythonLabs\deepagents\maaya\frontend\src\__tests__\ChatMessage.test.tsx`

Use `@testing-library/react` and `vitest`. Import `ChatMessageItem` from `../components/ChatMessage`.

Tests to write:

```
renders human message right-aligned
  → render <ChatMessageItem message={{id:'1', type:'human', content:'hi'}} />
  → expect element with right-align / justify-end class

renders ai message with content text
  → message {type:'ai', content:'hello'}
  → getByText('hello') present

renders tool message showing tool_name
  → message {type:'tool', content:'ok', tool_name:'write_file'}
  → getByText or getByRole shows tool name

renders task_complete with token count and formatted cost
  → message {type:'task_complete', agent:'backend', input_tokens:100, output_tokens:50, cost_usd:0.003}
  → text "100" and "$0.003" (or "0.003") visible

renders error message with red styling
  → message {type:'error', content:'something went wrong'}
  → element with red color class exists

renders system divider text
  → message {type:'system', content:'── Previous conversation ──'}
  → getByText shows content

does not apply ai-bubble styling to human messages
  → human message should NOT have the same container class as ai messages
```

Write: `d:\PythonLabs\deepagents\maaya\frontend\src\__tests__\DiffViewer.test.tsx`

Import `DiffViewer` from `../components/DiffViewer`.

Tests to write:

```
shows empty state placeholder when fileDelta is null
  → render <DiffViewer fileDelta={null} />
  → placeholder text visible, no <table> rendered

renders file path in header
  → fileDelta={path:'src/main.py', content:'x', op:'write'}
  → getByText('src/main.py') present

shows write badge with green styling when op=write
  → op='write'  →  badge element contains text "write" and has green class

shows edit badge with yellow styling when op=edit
  → op='edit'  →  badge element contains text "edit" and has yellow class

renders correct number of table rows
  → content="line1\nline2\nline3"  →  3 <tr> rows rendered

highlights + lines green in edit mode
  → op='edit', content='+added line'
  →  row has bg-green class

highlights - lines red in edit mode
  → op='edit', content='-removed line'
  →  row has bg-red class
```

Write: `d:\PythonLabs\deepagents\maaya\frontend\src\__tests__\HilApproval.test.tsx`

Import `HilApproval` from `../components/HilApproval`.

Tests to write:

```
renders the tool name from request
  → render <HilApproval request={{tool:'edit_file', args:{file_path:'x.ts'}}} onRespond={fn} />
  → getByText('edit_file') present

renders the args as readable text
  → args object displayed in the modal body

Approve button calls onRespond(true)
  → click button with text "Approve"
  → expect onRespond to have been called with true

Reject button calls onRespond(false)
  → click button with text "Reject"
  → expect onRespond to have been called with false
```

Run the frontend tests:

```bash
cd d:\PythonLabs\deepagents\maaya\frontend
npm test
```

Fix all failures before continuing.

---

## PART D — WRITE CHANGELOG

Create: `d:\PythonLabs\deepagents\maaya\changelog\CHANGELOG_{YYYYMMDD}.md`

Replace `{YYYYMMDD}` with today's date (e.g. `CHANGELOG_20260324.md`).

Use this exact format:

```markdown
# Maaya Changelog — {YYYY-MM-DD}

## Test Run Summary

| Layer | Total | Passed | Fixed | Skipped |
| --- | --- | --- | --- | --- |
| Browser (TC-01..TC-25) | 25 | X | Y | Z |
| Pytest — API endpoints | 20 | X | Y | Z |
| Pytest — DB models | 5 | X | Y | Z |
| Vitest — frontend components | 17 | X | Y | Z |
| **Total** | **67** | **X** | **Y** | **Z** |

## Fixes Applied

### Fix 1 — {short descriptive title}

**File:** `relative/path/to/file.py`
**Problem:** What was wrong and how it manifested
**Root cause:** Why it was happening
**Fix:** Exactly what code changed (one-liner or brief description)
**Verified by:** TC-XX ✅ / `test_function_name` ✅

### Fix 2 — ...

_(One section per fix. If nothing was fixed, write "No fixes required.")_

## Known Issues / Not Fixed

_(List anything found but left unfixed, with reason — e.g. "out of scope", "needs manual deploy".)_
```

Save the file.

Report: **TESTING COMPLETE** — changelog at `maaya/changelog/CHANGELOG_{date}.md`
