---
name: spec-breakdown
description: Analyzes a product spec or feature request and breaks it into Epics, Stories, and Tasks with priorities and agent assignments. Use when given a new spec, PRD, feature description, or user story to implement.
license: MIT
allowed-tools: create_epic create_story create_task get_tracker_summary
---

# Spec Breakdown Skill

> **Follow the `project-planning` skill for all sizing rules, acceptance criteria format,
> and LLM-friendly task boundaries before creating any tracker entries.**
> The rules below are the quick-reference process. The `project-planning` skill contains
> the authoritative standards you must apply.

## When to Use
- User provides a new product spec or PRD
- User describes a new feature to build
- A new project is starting and needs to be planned
- An existing project needs a new module planned

## Hierarchy

```
Epic (major feature area, 1-2 weeks)
└── Story (user-facing functionality, 1-3 days)
    └── Task (concrete implementation step, hours)
```

## Process

### Step 1 — Read and understand
Read the full spec. Identify:
- The core purpose of the product/feature
- The main user-facing areas (these become Epics)
- What a user can do in each area (these become Stories)
- What needs to be built technically (these become Tasks)

### Step 2 — Create Epics (3-7 per project)
Good epic examples:
- "Project Setup & Infrastructure"
- "User Authentication"
- "Core Data Models"
- "Frontend UI"
- "API Layer"
- "Testing & Quality"

```
create_epic(title="Project Setup & Infrastructure", description="...", priority="critical")
```

### Step 3 — Create Stories per Epic (2-5 per epic)

**Sizing check before creating each story (from `project-planning` skill):**
- RIGHT SIZE: reads < 5 files, produces < 3 new files, one agent, one layer
- TOO BIG: touches frontend AND backend → split into separate stories per layer
- Story points: 1-3 = ok to create as-is | 5 = borderline, add detail | 8+ = must split

Good story examples for "User Authentication" epic:
- "User can register with email/password" (backend story — route + service + schema)
- "Registration form renders and submits" (frontend story — component only)
- "User can log in and receive JWT token"
- "User can reset their password"

```
create_story(epic_id=1, title="User can register with email/password", story_points=3, priority="high")
```

### Step 4 — Create Tasks per Story (2-6 per story)

**Each task description must include: exact file path, function/component name,
input/output types, and the pattern to follow. Never say "update the existing service"
without naming the file and function.**

Good task examples for "User can register" story:
- "Create User SQLAlchemy model in backend/app/models/user.py" → assigned_agent: "database"
- "Write Alembic migration for users table" → assigned_agent: "database"
- "Create POST /auth/register route in backend/app/routers/auth.py returning UserResponse" → assigned_agent: "backend"
- "Build RegisterForm in frontend/src/components/auth/RegisterForm.tsx posting to POST /auth/register" → assigned_agent: "frontend"
- "Write pytest tests for POST /auth/register in tests/test_auth.py" → assigned_agent: "tester"

```
create_task(story_id=1, title="Create User SQLAlchemy model in backend/app/models/user.py", assigned_agent="database", priority="high")
```

## Agent Assignment Rules

| Type of work | assigned_agent |
|---|---|
| System design, folder structure | architect |
| React components, hooks, pages | frontend |
| FastAPI routes, services, schemas | backend |
| DB models, migrations, schema | database |
| Config files, docker, git, env | devops |
| pytest tests, Vitest tests | tester |

## Priority Guidelines
- **critical**: Core functionality without which nothing works (DB setup, app skeleton, auth)
- **high**: Main user-facing features
- **medium**: Supporting features and integrations
- **low**: Nice-to-have, polish, optimizations

## Always Include These Epics for a New Project
1. **Project Setup & Infrastructure** (devops + architect tasks) — always first, critical priority
2. **Core Data Models** (database tasks) — before any business logic
3. **API Layer** (backend tasks)
4. **Frontend UI** (frontend tasks)
5. **Testing** (tester tasks) — create after implementation epics

## Output
After creating everything, call `get_tracker_summary` and return the full breakdown showing:
- Total epics, stories, tasks created
- The recommended execution order
- Any assumptions made about the spec
