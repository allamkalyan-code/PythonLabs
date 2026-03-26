# Maaya — Optimal Version Roadmap

> **Goal:** The best coding agent that is cheaper than every existing tool (Devin $500/mo,
> Cursor $20/mo, Copilot $19/mo) by routing work to the cheapest capable model per task.

Each phase is self-contained. Give the prompt under each phase directly to Claude Code to implement it.
Do Phase 0 first — everything else depends on it.

---

## Phase 0 — Model Tier Config ✦ Do This First

**What:** Replace hardcoded model IDs with tier names (`fast`, `balanced`, `powerful`).
One config file maps tiers to models. Changing models = one line, one file.

**Tier assignments:**

| Agent | Tier | Reason |
|---|---|---|
| spec-evaluator | fast | Pure analysis, structured output |
| planner | balanced | Reasoning + decomposition |
| architect | balanced | System design judgment |
| frontend | balanced | UI creativity + TypeScript precision |
| backend | balanced | Business logic reasoning |
| database | fast | Formulaic patterns |
| devops | fast | Config files are deterministic |
| tester | fast | Test scaffolding follows rigid patterns |
| retry escalation | powerful | Only on 2nd failure |

**Files:** new `agents/model_config.py`, `agents/maaya.py`, `agents/subagents.yaml`, `.env.example`

**Prompt:**
```
Refactor Maaya's model selection to use a tier system instead of hardcoded model IDs.

Step 1 — Create maaya/agents/model_config.py:
  MODEL_TIERS dict with keys "fast", "balanced", "powerful".
  Each reads from an env var with a sensible default:
    MAAYA_MODEL_FAST     → anthropic:claude-haiku-4-5-20251001
    MAAYA_MODEL_BALANCED → anthropic:claude-sonnet-4-6
    MAAYA_MODEL_POWERFUL → anthropic:claude-opus-4-6
  Export get_model(tier: str) -> str helper.

Step 2 — Update subagents.yaml:
  Replace every `model: anthropic:...` line with `tier: fast`, `tier: balanced`,
  or `tier: powerful` per the table above. No tier = defaults to "balanced".

Step 3 — Update maaya.py _load_subagents():
  If "tier" key present: set subagent["model"] = get_model(subagent.pop("tier"))
  If "model" key present: use as-is (backward compat)
  If neither: use get_model("balanced")

Step 4 — Update .env.example with all three MAAYA_MODEL_* vars.

Step 5 — Log on startup which model each tier resolves to.
```

---

## Phase 1 — Self-Healing Test Loop ⭐ Highest ROI

**What:** When tester fails, auto-route the failure to the implementation agent (2 retries max).
After 2 failures, escalate to HIL with a diagnosis. No extra API cost.

**Files:** `server/routers/agent.py`, `agents/subagents.yaml` (tester), `agents/AGENTS.md`

**Prompt:**
```
Implement a self-healing test retry loop in Maaya.

When tester runs tests and they fail, the orchestrator should:
1. Parse failure output from the tester's HANDOFF block
2. Auto-invoke the relevant implementation agent (frontend or backend) with the
   full failure output and instruction to fix
3. Re-invoke tester
4. Allow up to 2 retry cycles total
5. After 2 failures, send HIL to user with summary of what was tried and what broke

Changes:
- subagents.yaml tester system_prompt: always output in HANDOFF:
    FAILED_TESTS: [test names]
    FAILURE_REASON: [one-line cause per test]
    SUGGESTED_FIX: [which agent and what to tell them]
- server/routers/agent.py: detect HANDOFF STATUS=FAILED from tester, parse fields,
  re-invoke named agent, re-invoke tester. Track retry count per story.
- agents/AGENTS.md: document retry flow — do not ask user when retry is in progress.
```

---

## Phase 2 — Spec Quality Gate

**What:** `spec-evaluator` subagent (fast tier) scans the spec before planner runs.
Returns up to 5 critical questions. Planner only runs after `SPEC_COMPLETE`.

**Files:** `agents/subagents.yaml` (new spec-evaluator), `agents/AGENTS.md`

**Prompt:**
```
Add a spec-evaluator subagent to Maaya that runs before the planner.

In subagents.yaml, add spec-evaluator:
- Tier: fast
- Description: "ALWAYS call this FIRST on any new spec, before the planner."
- System prompt: Check for:
    1. Missing user roles
    2. Undefined data entities
    3. Missing error states
    4. Ambiguous scope
    5. Missing auth requirements
  Output: "SPEC_COMPLETE: proceed to planner" OR numbered questions (max 5, critical first).
  If questions returned, do NOT call planner.

In AGENTS.md: "For every new build request, ALWAYS call spec-evaluator first.
Only call planner after spec-evaluator returns SPEC_COMPLETE."
```

---

## Phase 3 — Parallel Agent Execution

**What:** Frontend + backend agents run simultaneously via `asyncio.gather()` after architect.
Planner assigns `parallel_group` IDs; tasks in the same group dispatch concurrently.

**Files:** `server/models.py`, `server/database.py`, `agents/tracker_tools.py`,
`server/routers/agent.py`, `agents/subagents.yaml`, `agents/AGENTS.md`

**Prompt:**
```
Add parallel task execution to Maaya.

Step 1 — DB: Add `parallel_group: Mapped[str | None]` to Task in models.py.
  Add ALTER TABLE migration in database.py init_db().

Step 2 — Tool: Add optional `parallel_group: str = None` to create_task() in tracker_tools.py.

Step 3 — Planner: Update planner system_prompt in subagents.yaml to assign parallel_group:
  - Tasks with no shared file deps get the same group ID
  - Frontend + backend for same story → same group
  - Architect always group_0

Step 4 — Dispatch: In agent.py after planner completes, group tasks by parallel_group.
  asyncio.gather() for tasks within each group. Groups execute in order (0 → 1 → 2).

Step 5 — AGENTS.md: Document parallel_group rules.
```

---

## Phase 4 — Git-Native Output

**What:** Every story completion = git commit. Every epic completion = git tag.
Agent attribution in commit messages. Rollback = `git revert`.

**Files:** `agents/AGENTS.md`, `agents/subagents.yaml` (devops), `agents/tracker_tools.py`

**Prompt:**
```
Implement automatic git commits per story in Maaya.

In tracker_tools.py: add `get_story_changed_files(story_id)` returning files
created/modified during tasks in that story.

In subagents.yaml devops system_prompt, add auto-commit command:
  When called with "auto-commit story {id} title {title}":
  1. get_story_changed_files(story_id)
  2. Stage only those files (never git add -A)
  3. feat({epic-slug}): {story_title} — Tasks: {tasks} | Agents: {agents}
  4. HEREDOC syntax
  5. Report commit hash

In AGENTS.md: "After each story's tester completes STATUS=DONE, call devops
'auto-commit story {id} title {title}'. After epic completes, call devops
'create git tag {epic-slug}'."
```

---

## Phase 5 — Cross-Project User Memory

**What:** Corrections and explicit preferences persist to a `UserMemory` table.
Every new project starts with the user's preferences already loaded.

**Files:** `server/models.py`, `server/database.py`, `server/routers/projects.py`,
`agents/maaya.py`, `agents/tracker_tools.py`

**Prompt:**
```
Add cross-project user memory to Maaya.

Step 1 — DB: UserMemory model: id, key (unique), value (text), updated_at. Add migration.

Step 2 — API: GET /api/memory → {key: value}. PATCH /api/memory/{key} → upsert.

Step 3 — Tools: save_user_preference(key, value) and get_user_preferences() in tracker_tools.py.

Step 4 — Inject: In maaya.py create_maaya_agent(), call get_user_preferences() and prepend
  to system prompt as "## Your User's Preferences\n{key}: {value}\n..."

Step 5 — AGENTS.md: "When user corrects output or states a preference, call
  save_user_preference(key, value). E.g. 'use camelCase' → key='api_field_naming'."
```

---

## Phase 6 — Ollama Local Model Offload

**What:** Route devops and database tasks to a free local Ollama model.
Falls back silently to API model if Ollama is unavailable.

**Files:** `agents/maaya.py`, `.env.example`

**Prompt:**
```
Add Ollama local model offload to Maaya.

In maaya.py, add _detect_ollama():
  GET ${OLLAMA_URL:-http://localhost:11434}/api/tags → (True, models) or (False, [])
  Cache 60 seconds.

In create_maaya_agent(), if Ollama available and OLLAMA_MODEL set:
  Override "devops" and "database" subagent models to ollama/{OLLAMA_MODEL}.
  Log which agents use local vs API.

Wrap in try/except ConnectionError → fall back to tier model silently.

.env.example: OLLAMA_URL=http://localhost:11434 and OLLAMA_MODEL= (blank default).
```

---

## Phase 7 — Skills Marketplace

**What:** `maaya skill add <name>` downloads a SKILL.md from a curated registry into
`maaya/skills/`. Built-in catalog: stripe, nextjs, prisma, graphql, hipaa, react-native.

**Files:** new `cli.py`, new `registry.json`, `pyproject.toml`

**Prompt:**
```
Add a skills marketplace CLI to Maaya.

Create maaya/registry.json: [{"name": "stripe", "description": "...", "url": "..."}, ...]

Create maaya/cli.py:
  maaya skill list            → all available from registry
  maaya skill list --installed → locally installed only
  maaya skill add <name>      → download to maaya/skills/<name>/SKILL.md
  maaya skill remove <name>   → delete maaya/skills/<name>/

pyproject.toml: [project.scripts] maaya = "maaya.cli:main"

Note: _load_skills_prompt() already reads all SKILL.md dynamically — no change needed.
```

---

## Phase 8 — Diff Viewer UI Panel

**What:** Third panel showing live diffs of files being written/edited by agents,
streamed in real time. Auto-switches to Files tab when agent starts writing.

**Files:** `server/routers/agent.py`, `frontend/src/hooks/useWebSocket.ts`,
`frontend/src/types/index.ts`, new `frontend/src/components/DiffViewer.tsx`, `frontend/src/App.tsx`

**Prompt:**
```
Add a real-time diff viewer panel to the Maaya UI.

Backend: In agent.py on on_tool_start for write_file or edit_file:
  Send: {"type": "file_delta", "path": "...", "content": "...", "op": "write"|"edit"}

Types: export interface FileDelta { path: string; content: string; op: 'write' | 'edit' }

Hook: fileDelta: FileDelta | null state. Handle file_delta events. Clear when streaming ends.

Component DiffViewer.tsx:
  File path header + dark code block.
  'edit': green/red line diff. 'write': full content in <pre>.
  Empty state: "No files yet."

App.tsx: Add "Files" tab with Code2 icon. Auto-switch on file_delta.
```

---

## Execution Order

| Phase | What | Priority |
|---|---|---|
| **0** | Model Tier Config | First — unlocks all others |
| **1** | Self-Healing Loop | High ROI, do immediately after 0 |
| **2** | Spec Quality Gate | Quick win |
| **4** | Git-Native Output | Quick win |
| **5** | Cross-Project Memory | Medium effort |
| **3** | Parallel Execution | High effort |
| **8** | Diff Viewer UI | Medium |
| **6** | Ollama Offload | Medium |
| **7** | Skills Marketplace | Long tail |
