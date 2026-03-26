# Maaya

AI-powered full-stack development orchestrator. Give Maaya a spec — she plans it, assigns tasks to specialist agents, and builds it.

## Architecture

```
Browser UI (React + Tailwind)
    │  WebSocket + REST
    ▼
FastAPI local server  ←→  SQLite task tracker
    │
    ▼
Maaya orchestrator (deepagents)
    ├── planner       → breaks spec into epics/stories/tasks
    ├── architect     → system design + project scaffold
    ├── frontend      → React + TypeScript + Tailwind
    ├── backend       → FastAPI + SQLAlchemy
    ├── database      → PostgreSQL + Alembic
    ├── tester        → pytest + Vitest
    └── devops        → config, docker, git
```

## Setup

### 1. Install Python dependencies

```bash
cd maaya
uv sync
```

### 2. Set API keys

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY and/or OPENAI_API_KEY
```

### 3. Build the frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

### 4. Run Maaya

```bash
uv run python -m server.main
# or
uv run maaya
```

Open http://localhost:8000 in your browser.

## Usage

1. Set your **project output path** in the top bar (where Maaya will create files)
2. Select your **model** (Anthropic or OpenAI)
3. Type your spec in the chat — e.g.:
   > "Build a task management app with user auth, projects, and real-time updates using React and FastAPI"
4. Maaya will:
   - Plan epics/stories/tasks (visible in the Tracker tab)
   - Build the project file by file
   - Ask for your approval before writing files, running commands, or committing to git
5. Switch to the **Tracker** tab to see progress and edit tasks

## Frontend Dev Mode

To develop the frontend with hot reload:

```bash
cd frontend
npm run dev
```

The Vite dev server proxies `/api` and `/ws` to `http://localhost:8000`.

## Generated Project Stack

| Layer | Tech |
|---|---|
| Frontend | React 18 + TypeScript + Tailwind CSS + shadcn/ui + Vite |
| Backend | FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic v2 |
| Database | PostgreSQL |
| Tests | pytest (backend) + Vitest (frontend) |

## Skills

Maaya uses skills to guide specialist agents:

| Skill | Purpose |
|---|---|
| `spec-breakdown` | Analyzes specs into epics/stories/tasks |
| `react-component` | React + TypeScript + Tailwind patterns |
| `fastapi-route` | FastAPI routes + Pydantic schemas |
| `database-schema` | SQLAlchemy models + Alembic migrations |
| `git-workflow` | Git commits with HIL approval |
| `test-writing` | pytest + Vitest test patterns |
