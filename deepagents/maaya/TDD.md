# Maaya — Technical Design Document

**Version:** 2.0
**Date:** 2026-03-21
**Status:** Implemented
**Previous version:** 1.0 (2026-03-19)

---

## Changelog from v1 → v2

| Area | Change |
| --- | --- |
| Agent streaming | Switched from `astream(stream_mode="values")` to `astream_events(version="v2")` for reliable token tracking |
| Token tracking | New `task_complete` WebSocket event with per-pass input/output tokens and cost in USD |
| HIL mechanism | Replaced `hil.py` custom handler with LangGraph native `interrupt_on` + `MemorySaver` + `Command(resume=...)` |
| Deadlock fix | Added concurrent `ws_receiver` background task so HIL responses arrive while agent is suspended |
| Skills loading | Removed `SkillsMiddleware`; skills now eagerly loaded into system prompt via `_load_skills_prompt()` |
| `run_command` tool | Added subprocess-based command tool (FilesystemBackend does not support built-in `execute`) |
| Skills count | 6 → 8 skills: added `project-planning` and `coding-standards` |
| Planner | TDD REQUIREMENT: writes acceptance criteria + creates tester tasks before implementation tasks |
| Tester | Full TDD APPROACH: writes failing tests first, verifies after implementation |
| All subagents | Mandatory `---HANDOFF---` block at end of every response |
| Orchestrator | COMMAND RECOGNITION, CODING STANDARDS, HANDOFF PARSING, strict TDD workflow order added to AGENTS.md |
| Frontend | `task_complete` message type renders token/cost row in chat; typing indicator added |
| Tests | New `tests/test_token_tracking.py` — 21 unit tests, no LLM calls |

---

## Table of Contents

1. [Overview](#1-overview)
2. [Goals and Non-Goals](#2-goals-and-non-goals)
3. [System Architecture](#3-system-architecture)
4. [Component Design](#4-component-design)
5. [Data Model](#5-data-model)
6. [API Reference](#6-api-reference)
7. [Agent Design](#7-agent-design)
8. [Frontend Design](#8-frontend-design)
9. [Security and Human-in-the-Loop](#9-security-and-human-in-the-loop)
10. [Configuration and Environment](#10-configuration-and-environment)
11. [Deployment](#11-deployment)
12. [Dependencies](#12-dependencies)
13. [Known Limitations and Future Work](#13-known-limitations-and-future-work)
14. [File Inventory](#14-file-inventory)

---

## 1. Overview

**Maaya** is a local, browser-based AI orchestration system for building full-stack applications from scratch. The user describes a product spec; Maaya breaks it into a structured work hierarchy (Epics → Stories → Tasks), delegates execution to specialist sub-agents, and builds the entire codebase autonomously — with human approval on destructive actions.

Maaya is powered by the [Deepagents](https://github.com/langchain-ai/deepagents) framework (LangChain), which wraps LangGraph's `CompiledStateGraph` with batteries-included tooling: filesystem access, sub-agent delegation, skill injection, memory injection, and streaming.

### Key Properties

| Property | Value |
| --- | --- |
| Runs | Locally (localhost:8000) |
| User interface | Browser (React SPA) |
| Agent runtime | Deepagents 0.4.x / LangGraph |
| Persistence | SQLite (tracker) + JSON (project config) + MemorySaver (LangGraph HIL state) |
| Models | Anthropic (Claude 4.x) or OpenAI (GPT-4o, o3) |
| Output | Writes files directly into the user-specified project directory |
| Development methodology | Test-Driven Development — failing tests written before implementation |

---

## 2. Goals and Non-Goals

### Goals

- Accept a natural-language product spec and autonomously build a working full-stack application
- Maintain a structured task tracker (Epics → Stories → Tasks) that the user can monitor in real time
- Delegate work to 7 specialist sub-agents: planner, architect, frontend, backend, database, devops, tester
- Stream agent thought and tool-use output to the browser in real time
- Display per-pass token usage and USD cost after each agent activity
- Pause before destructive actions (file writes, shell commands, git commits) for user approval
- Understand developer commands ("run the app", "run tests", "explain src/main.py") without full planning
- Follow Test-Driven Development: acceptance criteria before implementation, failing tests before code
- Support both Anthropic and OpenAI models, user-selectable per session
- Target a default tech stack: React + TypeScript + FastAPI + PostgreSQL + Tailwind CSS

### Non-Goals

- Cloud deployment of Maaya itself (local only)
- Multi-user or team support
- Authentication / authorization
- Maaya does not manage its own Docker environment (the *output project* may have Docker)
- Real-time collaboration or websocket multiplexing across multiple clients

---

## 3. System Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         Browser (localhost:8000)                    │
│                                                                     │
│  ┌───────────────┐  ┌──────────────────┐  ┌──────────────────────┐ │
│  │  ProjectSetup │  │      Chat        │  │    TaskTracker       │ │
│  │  (path/model) │  │  (WebSocket UI)  │  │  (REST polling)      │ │
│  └───────┬───────┘  └────────┬─────────┘  └──────────┬───────────┘ │
│          │  REST             │  WebSocket             │  REST       │
└──────────┼───────────────────┼────────────────────────┼─────────────┘
           │                  │                         │
┌──────────▼───────────────────▼─────────────────────────▼────────────┐
│                      FastAPI (server/)                               │
│                                                                      │
│  ┌──────────────┐  ┌────────────────────┐  ┌──────────────────────┐ │
│  │ projects.py  │  │    agent.py        │  │    tracker.py        │ │
│  │ /api/projects│  │    /ws/chat        │  │   /api/tracker/      │ │
│  └──────────────┘  └────────┬───────────┘  └──────────────────────┘ │
│                             │                                        │
│  ┌──────────────────────────▼───────────────────────────────────┐   │
│  │  _run_agent_stream()                                         │   │
│  │  astream_events(v2) loop:                                    │   │
│  │  • on_chain_stream  → forward messages to frontend           │   │
│  │  • on_chat_model_end → accumulate usage_metadata for tokens  │   │
│  │  HIL: aget_state().interrupts → hil_request → hil_queue      │   │
│  │       Command(resume={"decisions": [...]}) to continue       │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              SQLite (maaya_tracker.db)                       │   │
│  │              Managed by SQLAlchemy 2.0                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────┬───────────────────────────────────────────┘
                           │  Python call
┌──────────────────────────▼───────────────────────────────────────────┐
│                     agents/ (Deepagents)                             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  maaya.py — create_maaya_agent()                               │  │
│  │  create_deep_agent(model, tools, system_prompt,                │  │
│  │                    subagents, backend, interrupt_on,           │  │
│  │                    checkpointer=MemorySaver())                 │  │
│  └───────────────────────┬────────────────────────────────────────┘  │
│                          │  sub-agent delegation (task tool)         │
│   ┌──────────┐  ┌────────┴┐  ┌──────────┐  ┌────────────────────┐  │
│   │ planner  │  │architect│  │ frontend │  │ backend / database │  │
│   └──────────┘  └─────────┘  └──────────┘  │ devops / tester   │  │
│                                             └────────────────────┘  │
│                                                                      │
│   Skills: eager-loaded at startup via _load_skills_prompt()         │
│   → injected as plain text into system_prompt (8 SKILL.md files)    │
│                                                                      │
│   run_command tool: subprocess.run(cwd=project_path) — HIL-gated    │
│   FilesystemBackend(root=project_path, virtual_mode=False)          │
│   → reads/writes files in user's output project                     │
└──────────────────────────────────────────────────────────────────────┘
```

### Communication Patterns

| Channel | Direction | Purpose |
| --- | --- | --- |
| `POST /api/projects/config` | Browser → Server | Save project path + model |
| `GET /api/projects/models` | Browser → Server | List available models |
| `WS /ws/chat` | Bidirectional | Stream agent output; HIL approval |
| `GET/POST/PATCH/DELETE /api/tracker/*` | Browser → Server | CRUD on Epics/Stories/Tasks |

---

## 4. Component Design

### 4.1 `server/main.py` — FastAPI Application

The entry point. Responsibilities:

- Loads `.env` file at startup (API keys)
- Registers 3 routers: `agent`, `tracker`, `projects`
- Mounts the React `dist/` build for SPA serving
- Falls back gracefully if the frontend hasn't been built yet
- Initializes SQLite database tables on startup via `lifespan` context manager

```text
FastAPI app
├── CORSMiddleware (allow_origins=["*"])
├── /ws/chat              — agent.router
├── /api/tracker/*        — tracker.router
├── /api/projects/*       — projects.router
└── /assets/*             — StaticFiles (React build)
    /{full_path:path}     — SPA fallback → index.html
```

### 4.2 `server/routers/agent.py` — WebSocket Handler

Handles the full agent session lifecycle per WebSocket connection. Key design decisions since v1:

**Concurrent receiver pattern** — `ws_receiver()` runs as a background asyncio task reading all incoming frames and routing them to either `hil_queue` (for `hil_response` frames) or `message_queue` (for user messages). This eliminates the deadlock that occurred when `astream` blocked the coroutine while HIL responses were waiting to be read.

**`astream_events` instead of `astream`** — Uses `agent.astream_events(version="v2")` to receive fine-grained events. This is the only reliable way to capture `usage_metadata` from LangChain messages, which may be stripped during LangGraph state serialization when using `stream_mode="values"`.

**Token tracking** — Per-pass accumulation of `input_tokens` and `output_tokens` from `on_chat_model_end` events. Cost computed via `_compute_cost(model_id, in_tok, out_tok)` and emitted as a `task_complete` WebSocket frame after each `astream_events` pass completes.

**`Overwrite` wrapper handling** — LangGraph's `on_chain_stream` events may wrap message lists in an `Overwrite` sentinel object. The handler unwraps via `hasattr(msgs, "value")` before iterating.

**Deduplication** — `seen_ids: set` tracks message IDs across all `on_chain_stream` events to prevent duplicate display when the same message surfaces from multiple graph nodes.

**LangGraph native HIL** — After each `astream_events` pass, `agent.aget_state(config)` is checked for `state.interrupts`. For each interrupt, a `hil_request` frame is sent and `hil_queue.get()` awaits approval. Resumption uses `Command(resume={"decisions": [...]})`.

Cost table (`_COST_TABLE`) — USD per million tokens:

| Model key | Input $/M | Output $/M |
| --- | --- | --- |
| `claude-sonnet-4-6` | $3.00 | $15.00 |
| `claude-opus-4-6` | $15.00 | $75.00 |
| `claude-haiku-4-5` | $0.25 | $1.25 |
| `gpt-4o` | $2.50 | $10.00 |
| `gpt-4o-mini` | $0.15 | $0.60 |

Message types sent to frontend:

| type | Payload | Meaning |
| --- | --- | --- |
| `start` | — | Agent began processing |
| `message` | `{data: {type, content, tool_calls?}}` | Streamed agent/tool message |
| `hil_request` | `{tool, args}` | Paused, waiting for user approval |
| `task_complete` | `{agent, input_tokens, output_tokens, cost_usd}` | Per-pass token/cost summary |
| `error` | `{content}` | Agent or server error |
| `done` | — | Agent finished, `isStreaming` cleared |

### 4.3 `server/routers/tracker.py` — Task Tracker CRUD

Full REST API for the Epic → Story → Task hierarchy. All responses include nested children for display.

| Method | Path | Action |
| --- | --- | --- |
| GET | `/api/tracker/epics` | List all epics with nested stories+tasks |
| POST | `/api/tracker/epics` | Create epic |
| PATCH | `/api/tracker/epics/{id}` | Update epic status/priority |
| DELETE | `/api/tracker/epics/{id}` | Delete epic (cascades to stories+tasks) |
| POST | `/api/tracker/stories` | Create story under epic |
| PATCH | `/api/tracker/stories/{id}` | Update story status |
| DELETE | `/api/tracker/stories/{id}` | Delete story |
| POST | `/api/tracker/tasks` | Create task under story |
| PATCH | `/api/tracker/tasks/{id}` | Update task status, notes, agent |
| DELETE | `/api/tracker/tasks/{id}` | Delete task |

### 4.4 `server/routers/projects.py` — Project Configuration

Persists project settings to `.maaya_config.json` in the Maaya directory.

| Method | Path | Action |
| --- | --- | --- |
| GET | `/api/projects/config` | Return current project path and model |
| POST | `/api/projects/config` | Save project path and model |
| GET | `/api/projects/models` | List available model IDs |

Available models (6):

- `anthropic:claude-sonnet-4-6`
- `anthropic:claude-opus-4-6`
- `anthropic:claude-haiku-4-5-20251001`
- `openai:gpt-4o`
- `openai:gpt-4o-mini`
- `openai:o3`

### 4.5 `server/hil.py` — Status: Unused (kept for reference)

The original `make_hil_handler(ws, queue)` approach from v1 is no longer used. HIL is now handled natively by LangGraph's `interrupt_on` mechanism — see Section 9 for the current flow. The file is retained but not imported.

### 4.6 `server/database.py` — Database Layer

```python
engine = create_engine("sqlite:///maaya_tracker.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    ...  # FastAPI dependency injection
```

`init_db()` calls `Base.metadata.create_all(engine)` on startup.

---

## 5. Data Model

### Entity Relationship

```text
Epic (1) ──────────< Story (1) ──────────< Task
  id                  id                   id
  title               epic_id (FK)         story_id (FK)
  description         title                title
  status              description          description
  priority            status               status
  created_at          priority             priority
  updated_at          story_points         assigned_agent
                      created_at           notes
                      updated_at           created_at
                                           updated_at
```

Cascade delete: deleting an Epic deletes all its Stories and their Tasks.

### Enums

**Status** (shared across all three models):

- `not_started` — default
- `wip` — in progress
- `done` — completed
- `blocked` — cannot proceed

**Priority** (shared across all three models):

- `low`
- `medium` — default
- `high`
- `critical`

### `assigned_agent` values (Task only)

| Value | Responsible Agent |
| --- | --- |
| `architect` | System design, scaffold |
| `frontend` | React/TypeScript/Tailwind |
| `backend` | FastAPI routes, services |
| `database` | SQLAlchemy models, Alembic migrations |
| `devops` | Config files, docker-compose, git, run commands |
| `tester` | pytest + Vitest tests; writes failing tests first |

---

## 6. API Reference

### WebSocket: `GET /ws/chat` (upgrade)

**Client → Server messages:**

```jsonc
// Start a new agent run
{"type": "message", "content": "Build me a todo app"}

// Respond to a HIL approval request
{"type": "hil_response", "approved": true}
```

**Server → Client messages:**

```jsonc
{"type": "start"}
{"type": "message", "data": {"type": "ai", "content": "...", "tool_calls": [...]}}
{"type": "message", "data": {"type": "tool", "name": "write_file", "content": "..."}}
{"type": "hil_request", "tool": "write_file", "args": {"path": "...", "content": "..."}}
{"type": "task_complete", "agent": "backend", "input_tokens": 1240, "output_tokens": 890, "cost_usd": 0.004}
{"type": "error", "content": "..."}
{"type": "done"}
```

### REST: Tracker

Full CRUD — see Section 4.3. All responses use camelCase JSON.

**Epic create request:**

```json
{"title": "User Auth", "description": "...", "priority": "high"}
```

**Task create request:**

```json
{
  "story_id": 3,
  "title": "Create POST /auth/register route in backend/app/routers/auth.py",
  "description": "...",
  "priority": "critical",
  "assigned_agent": "backend"
}
```

**Task update request:**

```json
{"status": "done", "notes": "backend/app/routers/auth.py, backend/app/services/auth_service.py"}
```

---

## 7. Agent Design

### 7.1 Maaya Orchestrator (`agents/maaya.py`)

Created via `create_maaya_agent(project_path, model_id)`.

```python
run_command = _make_run_command_tool(project_path)  # subprocess, HIL-gated

agent = create_deep_agent(
    model=init_chat_model(model_id),
    tools=TRACKER_TOOLS + [run_command],   # 9 tools: 8 tracker + run_command
    system_prompt=_load_system_prompt() + _load_skills_prompt(),  # AGENTS.md + 8 SKILL.md files
    memory=["./AGENTS.md"],                # Project AGENTS.md (if it exists)
    subagents=subagents,                   # 7 specialist agents, each with tracker + run_command tools
    backend=FilesystemBackend(root=project_path, virtual_mode=False),
    interrupt_on=HIL_TOOLS,               # write_file, edit_file, execute, run_command
    checkpointer=MemorySaver(),            # Required for LangGraph interrupt/resume
)
```

**Key design decisions:**

- `virtual_mode=False` on the project backend — avoids Windows `\\?\` extended-path prefix issues when the project path is user-supplied
- **Skills eager-loaded** — `_load_skills_prompt()` reads all `SKILL.md` files at startup and injects their content as plain text into `system_prompt`. This replaces the v1 `SkillsMiddleware` approach which caused a two-backend problem: skills were listed from `MAAYA_DIR` but `read_file` resolved paths relative to the project backend, causing "file not found" errors on Windows
- **`run_command` tool** — `FilesystemBackend` does not provide the built-in `execute` tool (that requires `SandboxBackend`). `_make_run_command_tool(project_path)` creates a `subprocess.run(shell=True, cwd=project_path, timeout=60)` wrapper using a closure. HIL-gated
- **`MemorySaver` checkpointer** — required for LangGraph to suspend the graph at interrupt points and resume later. Without this, `interrupt_on` has no effect
- `hil_handler` parameter removed — HIL is now handled by LangGraph natively

### 7.2 Tracker Tools (`agents/tracker_tools.py`)

8 LangChain `@tool` functions available to ALL agents (orchestrator and all sub-agents):

| Tool | Description |
| --- | --- |
| `create_epic(title, description, priority)` | Create a top-level epic |
| `create_story(epic_id, title, description, priority, story_points)` | Create a story |
| `create_task(story_id, title, description, priority, assigned_agent)` | Create a task |
| `update_task_status(task_id, status, notes)` | Update task status and notes |
| `update_story_status(story_id, status)` | Update story status |
| `update_epic_status(epic_id, status)` | Update epic status |
| `get_tracker_summary()` | Return full Epic→Story→Task hierarchy as text |
| `get_next_task()` | Return the next not_started task (lowest priority + id) |

All tracker tools talk directly to the SQLite database via SQLAlchemy sessions. They do not go through the REST API.

### 7.3 Sub-Agent Definitions (`agents/subagents.yaml`)

7 specialist agents loaded at startup and passed to `create_deep_agent()` as the `subagents=` list. Each receives all 9 tools (8 tracker + `run_command`).

All agents end every response with a mandatory `---HANDOFF---` block (see Section 7.6).

| Agent | Model | Responsibility |
| --- | --- | --- |
| `planner` | claude-sonnet-4-6 | Spec → Epic/Story/Task breakdown with AC; creates tester tasks before implementation |
| `architect` | claude-sonnet-4-6 | Folder structure, scaffold, ARCHITECTURE.md |
| `frontend` | claude-sonnet-4-6 | React + TypeScript + Tailwind + shadcn/ui |
| `backend` | claude-sonnet-4-6 | FastAPI routes, Pydantic schemas, services |
| `database` | claude-haiku-4-5 | SQLAlchemy 2.0 models, Alembic migrations |
| `devops` | claude-haiku-4-5 | pyproject.toml, package.json, docker-compose, git; COMMAND MODE |
| `tester` | claude-haiku-4-5 | TDD: writes failing tests first, verifies after impl; COMMAND MODE |

### 7.4 Orchestrator Workflow (TDD Order)

```text
User sends spec
      │
      ▼
[planner] Analyze spec → create Epics/Stories WITH acceptance criteria
          For each story: create tester task → impl tasks → verify tester task
      │
      ▼
[architect] Design folder structure → scaffold project
      │
      ▼
Loop: get_next_task()
  ├── tester task "Write failing tests for X"
  │     → tester writes tests that fail (code doesn't exist yet)
  │     → confirms tests fail for the right reason
  ├── database/backend/frontend implementation task
  │     → writes code to make the failing tests pass
  ├── tester task "Verify all tests pass for X"
  │     → runs tests, confirms all pass
  │     → reports any remaining failures
  └── update_task_status(done) after each
      │
      ▼ (after each story)
  update_story_status(done) + notify user
      │
      ▼ (after each epic / logical chunk)
  Propose git commit → HIL approval

COMMAND MODE (skip planning entirely):
  "run the app"      → devops: run_command(uvicorn / npm run dev)
  "run tests"        → tester: run_command(pytest -v / npm test)
  "install deps"     → devops: run_command(uv sync / npm install)
  "explain X.py"     → Maaya reads file and explains directly
  "fix the bug"      → identify file, delegate to backend/frontend/tester
```

### 7.5 Handoff Protocol

Every subagent ends its response with:

```text
---HANDOFF---
STATUS: [DONE | PARTIAL | BLOCKED | FAILED]
SUMMARY: [1-2 sentences of what was accomplished]
FILES_CREATED: [comma-separated file paths, or none]
FILES_MODIFIED: [comma-separated file paths, or none]
TESTS_WRITTEN: [yes/no — if yes, list test file paths]
ASSUMPTIONS: [any assumptions made due to unclear spec, or none]
FLAGS: [risks, missing deps, decisions affecting other agents, or none]
NEXT_SUGGESTED: [what should happen next]
---END HANDOFF---
```

Maaya parses this block after every task and acts accordingly:

| Field | Maaya's action |
| --- | --- |
| `STATUS: BLOCKED/FAILED` | Stop. Report to user. Await instruction. |
| `FLAGS` non-empty | Surface to user before continuing |
| `FILES_CREATED/MODIFIED` | Record in task notes; pass paths explicitly to next agent |
| `ASSUMPTIONS` questionable | Clarify with user before next task |
| `TESTS_WRITTEN: yes` | Confirm test files exist before dispatching implementation agent |

### 7.6 Skills (`skills/`)

8 skill files (SKILL.md) loaded at startup via `_load_skills_prompt()` in `maaya.py` and injected as plain text into the orchestrator's system prompt. All subagents also receive the full skill content through their shared system prompt context.

| Skill | Purpose |
| --- | --- |
| `spec-breakdown` | Breaking a spec into tracker Epics/Stories/Tasks; references `project-planning` |
| `project-planning` | Story sizing rules (RIGHT SIZE vs TOO BIG), Gherkin AC format, LLM-specific task boundaries, token budget awareness |
| `coding-standards` | Stack-specific code examples: FastAPI route pattern, Pydantic schemas, SQLAlchemy models, React components, pytest, Vitest |
| `react-component` | React + TypeScript + Tailwind component patterns |
| `fastapi-route` | FastAPI router + Pydantic schema + service layer patterns |
| `database-schema` | SQLAlchemy 2.0 model + Alembic migration patterns |
| `git-workflow` | Conventional commit messages + HIL-gated git flow |
| `test-writing` | pytest + Vitest test patterns |

**Why eager loading instead of SkillsMiddleware:** In v1, `SkillsMiddleware` listed skills from a `FilesystemBackend(root=MAAYA_DIR)` but when an agent called `read_file` to load a skill's content, it used the project backend (`root=project_path`). On Windows, `/skills/spec-breakdown/SKILL.md` resolved as an OS-absolute path (`C:\skills\...`) rather than relative to MAAYA_DIR, causing "file not found" errors. Eager loading sidesteps this entirely.

---

## 8. Frontend Design

### 8.1 Technology Stack

| Concern | Library |
| --- | --- |
| Framework | React 18 + TypeScript |
| Build | Vite 5 |
| Styling | Tailwind CSS 3 |
| UI Primitives | Radix UI (Dialog, Select, Tooltip) + CVA |
| HTTP | Axios + React Query |
| Icons | Lucide React |
| Routing | React Router v6 |

### 8.2 Component Tree

```text
App.tsx
├── ProjectSetup          — project path + model selector (top bar)
└── Tabs: Chat | Tracker
    ├── Chat
    │   ├── useWebSocket (hook) — WS state, message list, HIL state, streaming state
    │   ├── ChatMessage         — renders human/ai/tool/task_complete/error messages
    │   │   └── task_complete row: agent badge · "1,240 in / 890 out" · "$0.0043"
    │   ├── HilApproval        — approval card (inline in chat)
    │   └── typing indicator   — bouncing dots + "Maaya is working..." while isStreaming
    └── TaskTracker            — Epic/Story/Task table, status dropdowns
```

### 8.3 Key Hooks and State

**`useWebSocket.ts`**

State managed:

- `messages: ChatMessage[]` — full conversation history
- `isStreaming: boolean` — agent currently running
- `hilRequest: HilRequest | null` — pending approval (tool name + args)
- `status: 'disconnected' | 'connecting' | 'connected'`

Methods:

- `sendMessage(text: string)` — sends `{"type": "message", "content": text}`, adds message locally
- `respondHil(approved: boolean)` — sends `{"type": "hil_response", "approved": bool}`, clears `hilRequest`

**Duplicate prevention:**

- React StrictMode double-mount: guard on `wsRef.current?.readyState === WebSocket.CONNECTING`
- Server-side HumanMessage echoes: incoming `type: 'human'` frames are silently dropped (user's message is already displayed from local state)
- Fresh `thread_id` per message: prevents LangGraph from replaying prior state

**`task_complete` handling:** incoming `{type: "task_complete", agent, input_tokens, output_tokens, cost_usd}` frames are added to the message list as `ChatMessage` objects with `type: 'task_complete'`.

### 8.4 TypeScript Types

```typescript
export interface ChatMessage {
  id: string
  type: 'human' | 'ai' | 'tool' | 'error' | 'system' | 'task_complete'
  content: string
  tool_calls?: { name: string; args: Record<string, unknown> }[]
  tool_name?: string
  // task_complete fields
  agent?: string
  input_tokens?: number
  output_tokens?: number
  cost_usd?: number
}

export interface HilRequest {
  tool: string
  args: Record<string, unknown>
}
```

### 8.5 Task Tracker

Polls `GET /api/tracker/epics` every 5 seconds. Renders:

- Collapsible epic rows with progress bars (tasks done / total)
- Story rows nested under each epic
- Task rows nested under each story with:
  - Status dropdown (inline PATCH on change)
  - Priority badge (colour-coded)
  - Assigned agent badge
  - Notes column

### 8.6 Project Setup

Persistent across sessions — reads config from `GET /api/projects/config` on mount. User can update the project path and model at any time; changes POST to `/api/projects/config`.

---

## 9. Security and Human-in-the-Loop

### HIL-Gated Tools

The following tool calls pause the agent and wait for explicit user approval before executing:

| Tool | Risk |
| --- | --- |
| `write_file` | Overwrites files in the project directory |
| `edit_file` | Modifies existing files |
| `execute` | Built-in (not used — FilesystemBackend does not support it) |
| `run_command` | Runs arbitrary shell commands in the project directory |

### HIL Flow (LangGraph native — v2)

```text
Agent wants to call run_command(command="uvicorn app.main:app")
  → LangGraph HumanInTheLoopMiddleware fires (interrupt_on={"run_command": True})
  → agent.astream_events() completes (graph suspended at interrupt point)
  → agent.aget_state(config) returns state.interrupts (non-empty)
  → agent.py extracts action_requests from interrupt.value
  → Sends {"type": "hil_request", "tool": "run_command", "args": {...}} over WebSocket
  → hil_queue.get() — suspends _run_agent_stream coroutine
  → ws_receiver() (background task) reads the WebSocket frame while agent is suspended
  → User clicks Approve in browser
  → Client sends {"type": "hil_response", "approved": true}
  → ws_receiver routes to hil_queue.put(True)
  → hil_queue.get() returns True
  → decisions = [{"type": "approve"}]
  → agent.astream_events(Command(resume={"decisions": decisions})) resumes graph
  → Tool executes; agent continues
```

**Why `ws_receiver` is a background task:** In v1, `astream` and `receive_text` shared the same coroutine. When `hil_queue.get()` blocked waiting for approval, no code was reading the WebSocket, so the `hil_response` frame was never received — permanent deadlock. The fix: `ws_receiver` is an `asyncio.create_task` that runs concurrently and routes frames to either `hil_queue` or `message_queue`. `_run_agent_stream` waits on `hil_queue.get()` while `ws_receiver` feeds it from the WebSocket. No deadlock possible.

### CORS

All origins allowed (`allow_origins=["*"]`). Acceptable since the server is local-only (bound to `0.0.0.0:8000`). Would need to be locked down in any networked deployment.

### API Keys

Stored in a `.env` file in `maaya/`. Loaded at startup via `python-dotenv`. Never transmitted to the frontend or logged.

---

## 10. Configuration and Environment

### Environment Variables (`.env`)

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...         # Optional — needed for OpenAI models only
```

### Project Config (`.maaya_config.json`)

```json
{
  "project_path": "/absolute/path/to/your/project",
  "model": "anthropic:claude-sonnet-4-6"
}
```

Persisted in the `maaya/` directory. Updated via `POST /api/projects/config`.

### `maaya/AGENTS.md`

Maaya's identity, workflow rules, coding standards, handoff parsing rules, tech stack defaults, and communication style. Loaded as the system prompt for the orchestrator agent. Editable to customize Maaya's behavior without code changes.

Sections:

- `## Your Identity` — persona
- `## COMMAND RECOGNITION` — routing table for dev commands
- `## Your Workflow` — TDD-ordered execution steps
- `## CODING STANDARDS` — naming, structure, error handling, API conventions, testing, comments
- `## Tech Stack Defaults` — React + FastAPI + PostgreSQL defaults
- `## DELEGATION RULE` — Maaya never writes code itself
- `## HANDOFF PARSING` — how to act on subagent handoff blocks
- `## Rules` — invariants
- `## Communication Style` — tone and format

---

## 11. Deployment

### Local Development (Recommended)

```bash
# 1. Python environment
cd maaya
pip install deepagents langchain-anthropic langchain-openai aiofiles pydantic-settings

# 2. API keys
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY and/or OPENAI_API_KEY

# 3. Frontend (Vite dev server — hot reload)
cd frontend && npm install && npm run dev
# → http://localhost:5173 (proxied to API at :8000)

# 4. Start server
cd ..
python -m server.main
# → http://localhost:8000
```

### Server Configuration

| Setting | Value |
| --- | --- |
| Host | `0.0.0.0` |
| Port | `8000` |
| ASGI server | Uvicorn |
| Reload | `True` (dev mode — watches all Python files) |
| Database | `maaya_tracker.db` (SQLite, created automatically) |

---

## 12. Dependencies

### Python (`pyproject.toml`)

| Package | Purpose |
| --- | --- |
| `deepagents` | Agent runtime (LangGraph wrapper) |
| `langchain-anthropic` | Claude model integration |
| `langchain-openai` | OpenAI model integration |
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `sqlalchemy` | ORM (2.0 syntax) |
| `pydantic` | Data validation (v2) |
| `python-dotenv` | `.env` loading |
| `aiofiles` | Async file I/O |
| `pyyaml` | `subagents.yaml` loading |
| `websockets` | WebSocket support for FastAPI |

Dev dependencies:

| Package | Purpose |
| --- | --- |
| `pytest` | Test runner |
| `pytest-asyncio` | Async test support (`asyncio_mode = "auto"`) |
| `httpx` | Async HTTP client for FastAPI TestClient |

### JavaScript (`frontend/package.json`)

| Package | Purpose |
| --- | --- |
| `react` / `react-dom` | UI framework |
| `react-router-dom` | Client routing |
| `@tanstack/react-query` | Server state management |
| `axios` | HTTP client |
| `lucide-react` | Icons |
| `@radix-ui/react-dialog` / `select` / `tooltip` | Accessible UI primitives |
| `clsx` + `tailwind-merge` | Class name utilities |
| `class-variance-authority` | Component variant system |
| `vite` | Build tool |
| `tailwindcss` | Utility CSS |
| `vitest` | Test runner |
| `@testing-library/react` | Component testing |

---

## 13. Known Limitations and Future Work

### Current Limitations

| Limitation | Notes |
| --- | --- |
| Single WebSocket session | Only one agent can run at a time per browser tab |
| SQLite only | Not suitable for concurrent multi-user access |
| MemorySaver is in-process only | HIL state persists within one server process; restarting the server loses in-progress interrupted sessions |
| No file diff preview | HIL shows raw tool args, not a diff of the change |
| Frontend dev server separate | Vite dev server runs on :5173; production uses pre-built dist/ served by FastAPI |
| No auth | Anyone with network access to port 8000 can use the system |
| `run_command` 60s timeout | Long-running commands (docker build, npm install on slow connections) may time out |
| Token tracking covers outer graph only | Subagent LLM calls are captured via `on_chat_model_end` propagation; very deeply nested calls may be missed depending on LangGraph version |

### Resolved from v1

| Issue | Resolution |
| --- | --- |
| Duplicate human messages in chat | React StrictMode guard (`CONNECTING` check), fresh `thread_id` per message, client-side filtering of server-echoed human frames |
| HIL deadlock | `ws_receiver` background task; `hil_queue` + `message_queue` separation |
| `interrupt_on` had no effect | Was accidentally disabled when `hil_handler` was provided; now always active with `MemorySaver` checkpointer |
| Skills not found at runtime | Two-backend path mismatch on Windows; fixed by eager loading into system prompt |
| No conversation state across HIL resume | `MemorySaver` checkpointer now persists graph state across interrupt/resume cycles |

### Planned Improvements

| Feature | Priority |
| --- | --- |
| File diff view in HIL approval | High |
| Persistent conversation threads (LangGraph SQLite checkpointer) | High |
| Per-subagent token breakdown (separate `task_complete` per subagent call) | Medium |
| Progress notifications / desktop toasts | Medium |
| Project library (switch between multiple projects) | Medium |
| Streaming sub-agent output (show which sub-agent is currently active) | Medium |
| One-click docker-compose launch for generated projects | Low |
| MCP server integration for external tool access | Low |

---

## 14. File Inventory

```text
maaya/
├── AGENTS.md                     Orchestrator system prompt (identity, workflow, coding standards,
│                                 command recognition, handoff parsing, TDD order)
├── TDD.md                        This document (v2)
├── README.md                     Setup + usage guide
├── pyproject.toml                uv project config + Python deps
├── .env.example                  API key placeholders
│
├── server/
│   ├── __init__.py
│   ├── main.py                   FastAPI app entry point
│   ├── database.py               SQLite engine, session, init_db()
│   ├── models.py                 Epic, Story, Task SQLAlchemy models
│   ├── hil.py                    [Unused] Original HIL handler (kept for reference)
│   └── routers/
│       ├── __init__.py
│       ├── agent.py              /ws/chat WebSocket endpoint
│       │                         astream_events, token tracking, HIL native flow
│       ├── tracker.py            /api/tracker/* CRUD
│       └── projects.py           /api/projects/* config + models
│
├── agents/
│   ├── __init__.py
│   ├── maaya.py                  create_maaya_agent() factory
│   │                             _make_run_command_tool(), _load_skills_prompt()
│   │                             MemorySaver checkpointer, run_command HIL gate
│   ├── subagents.yaml            7 specialist agent definitions
│   │                             All agents: HANDOFF block
│   │                             planner: TDD REQUIREMENT + AC format
│   │                             tester: TDD APPROACH (write failing tests first)
│   │                             devops/tester: COMMAND MODE
│   └── tracker_tools.py          8 LangChain tracker tools
│
├── skills/
│   ├── spec-breakdown/SKILL.md   Spec → tracker breakdown; references project-planning
│   ├── project-planning/SKILL.md Story sizing, Gherkin AC, LLM task boundaries (NEW)
│   ├── coding-standards/SKILL.md Stack patterns: FastAPI, SQLAlchemy, React, pytest, Vitest (NEW)
│   ├── react-component/SKILL.md  React component patterns
│   ├── fastapi-route/SKILL.md    FastAPI route patterns
│   ├── database-schema/SKILL.md  SQLAlchemy + Alembic patterns
│   ├── git-workflow/SKILL.md     Git commit + HIL flow
│   └── test-writing/SKILL.md     pytest + Vitest patterns
│
├── tests/
│   └── test_token_tracking.py    21 unit tests (no LLM calls):
│                                   _compute_cost (7 tests)
│                                   _msg_to_dict (6 tests)
│                                   _run_agent_stream integration (8 tests)
│                                   Overwrite wrapper handling (1 test)
│
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.tsx
        ├── index.css
        ├── App.tsx               Tab layout: Chat | Tracker
        ├── setupTests.ts
        ├── types/index.ts        ChatMessage (incl. task_complete fields), HilRequest
        ├── lib/api.ts            Axios instance + REST helpers + createChatSocket()
        ├── hooks/
        │   └── useWebSocket.ts   WS state, message list, HIL state, task_complete handler
        └── components/
            ├── Chat.tsx          Streaming chat UI + typing indicator
            ├── ChatMessage.tsx   human/ai/tool/task_complete/error message renderer
            ├── HilApproval.tsx   Approval card (inline in chat)
            ├── ProjectSetup.tsx  Path + model configuration bar
            └── TaskTracker.tsx   Epic/Story/Task interactive table
```
