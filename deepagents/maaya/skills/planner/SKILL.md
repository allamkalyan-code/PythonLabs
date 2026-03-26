---
name: planner
description: Project planning using Standard 1 (Epic/Story/Task hierarchy) and Standard 5 (token-aware task sizing rules). Read this before creating any tracker entries.
license: MIT
compatibility: Python 3.11+
allowed-tools: create_epic update_epic_status create_story update_story_status create_task update_task_status get_tracker_summary
---

# Planner Skill

Read every rule below before calling any tracker tool.

---

## Standard 1 — Project Planning Hierarchy

### Epics

An Epic is a major product area — a theme, not a feature.

- Create **2–6 Epics** per project.
- Required fields: `title`, `description`, `success_criteria`, `priority`.
- Title format: noun phrase — e.g. "User Authentication", "Calculator Core", "Deployment".
- `success_criteria`: one observable sentence describing when this Epic is done.

### Stories

A Story is a single user-facing capability **in one layer only** (never cross frontend and backend in a single Story).

- Create **3–6 Stories per Epic**.
- Required fields: `title`, `user_story`, `acceptance_criteria`, `assigned_agent`, `story_points`, `depends_on`.
- Title format: verb-object — e.g. "Create POST /calculate endpoint", "Render calculator UI".
- `user_story`: "As a [role], I want [action] so that [outcome]."
- `acceptance_criteria`: list of **Gherkin Given/When/Then** strings — minimum 3:
  1. Happy path (valid input → correct output)
  2. Error case (invalid input → correct error)
  3. Integration (works end-to-end with upstream/downstream)
- `story_points`: 1 (trivial) | 2 (small) | 3 (medium) | 5 (large — split it)
- `assigned_agent`: one of: frontend, backend, database, devops, tester
- `depends_on`: list of story IDs that must complete before this starts

### Tasks

A Task is a single unit of work: **one file + one function/class + one concern**.

- Create **2–5 Tasks per Story**.
- Required fields: `title`, `description`, `assigned_agent`, `file_path`, `input_output_types`.
- Title format: verb-noun — e.g. "Create calculate() service function".
- `file_path`: exact relative path to the file to create or edit (e.g. `api/routes/calculate.py`).
- `input_output_types`: parameter names, types, and return type — e.g. `(a: float, b: float) -> float`.
- `description`: self-contained, 3–5 sentences. Include: what to implement, which pattern to follow, which existing files to reference.
- `parallel_group`: integer — tasks in the same group run concurrently. Use `1` for the first parallel batch, `2` for the next, etc.

---

## Standard 5 — Token-Aware Task Sizing Rules

Apply these rules to every Story before creating it. If a Story fails a check, split it.

| Signal | Verdict | Action |
|--------|---------|--------|
| Touches both frontend AND backend | Too big | Split: one Story per layer |
| Reads more than 5 existing files | Too big | Reduce scope or split |
| Creates more than 3 new files | Too big | Split into multiple Stories |
| Description needs more than 10 bullet points | Too vague | Rewrite with specifics |
| References "look around" or "find the right file" | Invalid | Rewrite with exact file paths |
| Under 200 words, reads ≤5 files, creates ≤3 files | Right size | Proceed |

### Correct sizing examples

**Too big** — "Implement user authentication": touches models (database), routes (backend), forms (frontend), tests.
**Right size** — "Create User SQLAlchemy model with email + hashed_password columns": one file, one class, database layer only.

**Too big** — "Build the calculator API": creates route, service, schema, tests, dockerfile.
**Right size** — "Create POST /api/calculate FastAPI route": one file (`api/routes/calculate.py`), one endpoint, backend layer.

---

## Workflow

1. Read the spec carefully. Identify the major product areas → create Epics.
2. For each Epic, identify user-facing capabilities → create Stories (one layer each).
3. For each Story, identify the exact files to create → create Tasks.
4. Apply Standard 5 sizing check to every Story before calling `create_story`.
5. Set `depends_on` correctly: frontend Stories depend on their backend Story; backend Stories depend on the database Story that creates the schema they use.
6. Set `parallel_group` for Stories that can run concurrently (same layer, no shared files).
7. End with the HANDOFF block as instructed in AGENTS.md.
