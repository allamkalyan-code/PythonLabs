---
name: project-planning
description: "Use this skill when breaking down a product spec into epics,
  stories, and tasks. Provides story sizing rules, acceptance criteria
  format, and LLM-friendly task boundaries."
---

# Project Planning Skill

LLM-aware planning standards for breaking a product spec into Epics, Stories, and Tasks.
This skill is written for LLM agents — not human developers. The rules account for how
LLMs differ from humans: fixed context windows, no implicit codebase knowledge, no state
between tasks, and high sensitivity to ambiguity.

---

## 1. Hierarchy

```
Epic   — A major feature area. Scoped to one concern (auth, data models, UI, etc.)
└── Story  — One user-facing capability. Implementable in a single context window.
    └── Task   — One concrete implementation step. One agent, one file set, one output.
```

**Epic** = "What the user can do in this area of the product."
**Story** = "One specific thing a user can do." Written as a user story.
**Task** = "One concrete thing an agent builds." Written as a verb phrase with a specific output.

---

## 2. Story Sizing Rules

### RIGHT SIZE — a story is correctly sized when:
- Requires reading **fewer than 5 files** to implement
- Produces **fewer than 3 new files**
- Can be described in **under 200 words** with full context included
- Assigned to **one agent** (one layer: either frontend OR backend OR database — never both)
- Implementable in **one context window** without needing to reference other in-progress tasks

### TOO BIG — split the story when it:
- Touches **both frontend and backend** (cross-layer)
- Requires understanding the **whole codebase** to implement
- Has more than **3 acceptance criteria** that span different layers
- The task description needs to say "look at the existing code" without a specific path

### How to split an oversized story:
Split by **layer**, in this order:
1. **Contract story** — define the API schema / data contract first (backend task: write Pydantic schema)
2. **Backend story** — implement the endpoint/service using the contract
3. **Frontend story** — implement the UI consuming the contract
4. **Tests story** — write tests for both layers

> Rule: if a feature needs frontend + backend, that is always at least 2 stories, not 1.

---

## 3. Epic Format

```
Title:            Short noun phrase — "User Authentication", "Task Management API"
Description:      What the user can accomplish when this epic is done.
Priority:         critical | high | medium | low
Success Criteria: 1-3 sentences. What is true when this epic is fully complete?
```

**Priority guidelines:**
- `critical` — nothing else works without this (project setup, core data models, auth)
- `high` — main user-facing feature
- `medium` — supporting feature or integration
- `low` — polish, nice-to-have, optimization

---

## 4. Story Format

```
Title:           User story — "User can register with email and password"
Description:     Include: what the user does, what the system does, what the result is.
                 Must be self-contained. Include the API contract if known.
Story Points:    1 = trivial (config, rename) | 2 = small (one endpoint, one component)
                 3 = medium (endpoint + service layer) | 5 = large (split this story)
                 Never assign 8 or 13 — that is always a sign the story needs splitting.
Assigned Agent:  One agent only. See agent assignment table below.
```

**Agent assignment:**

| Work type | assigned_agent |
|---|---|
| Folder structure, scaffold, tech decisions | architect |
| React components, hooks, pages, forms | frontend |
| FastAPI routes, services, Pydantic schemas | backend |
| SQLAlchemy models, Alembic migrations | database |
| Config files, docker, git, env files, run commands | devops |
| pytest tests, Vitest tests | tester |

---

## 5. Task Format

Tasks must be **verb + specific thing**. Include the exact file path, function name,
input types, and output types in the description. No implicit references.

**Good task titles:**
- `Create User SQLAlchemy model in backend/app/models/user.py`
- `Add POST /auth/register route in backend/app/routers/auth.py returning UserResponse`
- `Build RegisterForm component in frontend/src/components/auth/RegisterForm.tsx`

**Bad task titles (too vague for an LLM):**
- `Set up authentication` — which layer? which file? which function?
- `Update the user service` — which file? what change? what input/output?
- `Fix the bug` — what bug? where? what is the expected behaviour?

**Task description must include:**
1. Exact file path to create or modify
2. Function/component name and signature
3. Input types and output types (or HTTP method + path + status codes)
4. Any existing pattern to follow (with its file path)
5. What "done" looks like for this specific task

---

## 6. Acceptance Criteria — Gherkin Format

Every story must have acceptance criteria in Gherkin format. Criteria must be
**machine-verifiable**: a specific input produces a specific output. Never use
"works correctly" or "handles errors" — state the exact condition.

**Format:**
```
Given [a specific system state]
When  [a specific user action or input]
Then  [a specific, observable result — HTTP status, DB state, UI change, return value]
```

**Minimum required per story:**

| Criterion type | Example |
|---|---|
| Happy path (required) | Given a valid email+password, When POST /register is called, Then status 201 and a user row exists in the DB |
| Error case (required) | Given an email already in the DB, When POST /register is called, Then status 409 and body `{"detail": "Email already registered"}` |
| Integration criterion (required) | Given the register endpoint exists, When the RegisterForm submits, Then the form shows a success message and redirects to /dashboard |

**Add edge cases for:**
- Empty / null inputs → 422 Unprocessable Entity
- Boundary values (max length strings, zero quantities)
- Auth-required endpoints called without a token → 401

---

## 7. Definition of Done

A task is done only when **all** of these are true:

- [ ] Code is written in the correct file at the correct path
- [ ] Function/component matches the signature specified in the task description
- [ ] Acceptance criteria pass (manually traceable from the code)
- [ ] No `TODO`, `FIXME`, `pass`, or placeholder values remain
- [ ] Naming conventions match the existing codebase patterns
- [ ] Imports are correct and complete
- [ ] The task status is updated in the tracker (`update_task_status`)

---

## 8. Token Budget Awareness

**Context window is the hard limit — not time or effort.**

### Rules for keeping tasks within budget:

**Rule 1 — 5-file limit.**
A task is too big if completing it requires holding more than 5 files in context at once.
Split it even if a human would do it in one go.

**Rule 2 — Self-contained descriptions.**
Every task description must include everything the agent needs. LLMs have no implicit
knowledge of the codebase. Include:
- Exact file paths (`backend/app/routers/auth.py`, not "the auth router")
- Exact function names (`create_user(db, email, password) -> User`)
- The pattern to follow with its file path (`follow the pattern in backend/app/routers/items.py`)
- Input/output types explicitly

Never say:
- "look at the existing service" → say which file and which function
- "follow the existing pattern" → say which file contains the pattern
- "update it to support X" → say what the current signature is and what the new one should be

**Rule 3 — No cross-task state.**
Each task must assume the agent starts fresh. If Task 5 depends on a decision from Task 3,
re-state that decision in Task 5's description. Never reference another task by ID or title.

**Rule 4 — Contract-first sequencing.**
When frontend and backend must work together, always create a contract task first:
a backend task that defines and commits the Pydantic request/response schemas.
Both the frontend and backend tasks then include those schemas in their descriptions,
so neither agent needs to guess at the API shape.

**Rule 5 — Verifiable criteria only.**
Vague acceptance criteria cost tokens in clarification and produce drift.
Every criterion must specify: exact input → exact output → exact observable state.
"Returns the correct data" is not a criterion. "Returns `{"id": 1, "email": "..."}` with status 200" is.
