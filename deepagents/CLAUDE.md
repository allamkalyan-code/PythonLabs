# Deep Agents — Project Context

This workspace uses the **Deep Agents** framework by LangChain (`deepagents-main/`).
Source: https://github.com/langchain-ai/deepagents

---

## What is Deep Agents?

A batteries-included agent harness built on LangGraph. `create_deep_agent()` returns a compiled LangGraph `CompiledStateGraph` with planning, filesystem, shell, sub-agents, skills, and memory built in.

---

## Core API

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model=None,               # Default: claude-sonnet-4-6. Use "openai:gpt-4o" string or BaseChatModel
    tools=[],                 # Custom LangChain tools (added alongside built-ins)
    system_prompt=None,       # String or SystemMessage — prepended to BASE_AGENT_PROMPT
    middleware=(),            # Extra AgentMiddleware after default stack
    subagents=None,           # List of SubAgent dicts (see below)
    async_subagents=None,     # List of AsyncSubAgent dicts for remote LangGraph servers
    skills=None,              # List of skill source paths e.g. ["./skills/"]
    memory=None,              # List of AGENTS.md file paths e.g. ["./AGENTS.md"]
    response_format=None,     # Structured output format
    context_schema=None,      # Schema for agent context
    checkpointer=None,        # LangGraph Checkpointer for persistence
    store=None,               # LangGraph BaseStore
    backend=None,             # Default: StateBackend. Use FilesystemBackend for disk access
    interrupt_on=None,        # Human-in-the-loop: {"edit_file": True}
    debug=False,
    name=None,
    cache=None,
)
```

---

## Built-in Tools (always available)

| Tool | Description |
|------|-------------|
| `write_todos` | Create/update a todo list for task planning |
| `read_file` | Read file content |
| `write_file` | Write/create a file |
| `edit_file` | Edit existing file |
| `ls` | List directory contents |
| `glob` | Find files by pattern |
| `grep` | Search file contents |
| `execute` | Run shell commands (requires sandbox backend) |
| `task` | Delegate to a named sub-agent |

---

## Default Middleware Stack (in order)

1. `TodoListMiddleware` — planning/todo tracking
2. `MemoryMiddleware` — loads AGENTS.md into system prompt (if `memory` specified)
3. `SkillsMiddleware` — loads SKILL.md files into system prompt (if `skills` specified)
4. `FilesystemMiddleware` — file read/write tools
5. `SubAgentMiddleware` — `task` tool for sub-agents
6. `SummarizationMiddleware` — auto-summarizes long contexts
7. `AnthropicPromptCachingMiddleware` — prompt caching (ignored for non-Anthropic models)
8. `PatchToolCallsMiddleware` — normalizes tool call formats
9. `HumanInTheLoopMiddleware` — added if `interrupt_on` specified
10. `AsyncSubAgentMiddleware` — added if `async_subagents` specified
11. Custom middleware from `middleware=` param — appended last

---

## Sub-agents

Defined as a list of dicts passed to `subagents=`:

```python
subagents=[
    {
        "name": "researcher",           # Required — used with task(subagent_type="researcher")
        "description": "...",           # Required — how the main agent decides when to use it
        "system_prompt": "...",         # Required — the sub-agent's instructions
        "model": "anthropic:claude-haiku-4-5-20251001",  # Optional — defaults to main model
        "tools": [web_search],          # Optional — defaults to main agent's tools
        "middleware": [],               # Optional — extra middleware
        "skills": ["./skills/"],        # Optional — skill sources for this sub-agent
    }
]
```

A default **general-purpose sub-agent** is always added automatically (uses main model + tools).
To override it, add a sub-agent with the same name as `GENERAL_PURPOSE_SUBAGENT["name"]`.

**Async sub-agents** (remote LangGraph deployments):
```python
async_subagents=[
    {
        "name": "remote-researcher",
        "description": "...",
        "graph_id": "my_graph",
        "url": "http://my-langgraph-server",  # Optional, omit for ASGI transport
    }
]
```

---

## Skills (SKILL.md files)

Skills follow the [Agent Skills specification](https://agentskills.io/specification).

**Directory structure:**
```
skills/
└── skill-name/          # Directory name MUST match `name` in frontmatter
    ├── SKILL.md          # Required: YAML frontmatter + markdown instructions
    └── helper.py         # Optional: supporting scripts
```

**SKILL.md format:**
```markdown
---
name: skill-name                          # Required, 1-64 chars, lowercase-alphanumeric-hyphens
description: What this skill does...      # Required, 1-1024 chars
license: MIT                              # Optional
compatibility: Python 3.10+              # Optional, 1-500 chars
allowed-tools: read_file write_file       # Optional, space-delimited tool names
metadata:
  key: value                              # Optional arbitrary key-value
---

# Skill Instructions

Full markdown instructions for how to use this skill...
```

**How skills work:** The agent sees skill names/descriptions in the system prompt. When a task matches, it reads the full SKILL.md for instructions (progressive disclosure).

**Register skills:**
```python
agent = create_deep_agent(skills=["./skills/"])
```

Multiple sources: later sources override earlier ones (last wins):
```python
skills=["./skills/base/", "./skills/project/"]
```

---

## Memory (AGENTS.md files)

Memory files are plain Markdown injected into the system prompt at startup.

```python
agent = create_deep_agent(memory=["./AGENTS.md"])
```

Multiple sources are concatenated in order. The agent can update memory via `edit_file`.

**What to put in AGENTS.md:**
- Project overview / role description
- Brand voice / writing standards
- Code style guidelines
- Architecture notes
- Workflow preferences

---

## Backends

| Backend | Use Case |
|---------|----------|
| `StateBackend` (default) | Ephemeral/in-memory. For `invoke()`, pass files via `invoke(files={...})`. No disk access. |
| `FilesystemBackend(root_dir=path)` | Reads/writes from real disk. Required for loading AGENTS.md and skills from filesystem. |

```python
from deepagents.backends import FilesystemBackend

agent = create_deep_agent(
    backend=FilesystemBackend(root_dir=Path(__file__).parent),
    memory=["./AGENTS.md"],
    skills=["./skills/"],
)
```

For `StateBackend` + skills/memory, use a factory:
```python
from deepagents.backends import StateBackend
backend_factory = lambda rt: StateBackend(rt)
```

---

## Running the Agent

**Invoke (sync):**
```python
result = agent.invoke({"messages": [{"role": "user", "content": "Your task"}]})
```

**Stream (async):**
```python
async for chunk in agent.astream(
    {"messages": [("user", task)]},
    config={"configurable": {"thread_id": "my-thread"}},
    stream_mode="values",
):
    if "messages" in chunk:
        print(chunk["messages"][-1])
```

**With checkpointer (persistence):**
```python
from langgraph.checkpoint.memory import MemorySaver

agent = create_deep_agent(checkpointer=MemorySaver())
config = {"configurable": {"thread_id": "session-1"}}
agent.invoke({"messages": [...]}, config=config)
```

---

## Human-in-the-Loop

```python
agent = create_deep_agent(
    interrupt_on={"edit_file": True}  # Pause before every edit_file call
)
```

---

## MCP Support

Via `langchain-mcp-adapters`:
```python
from langchain_mcp_adapters import MCPToolkit
tools = MCPToolkit(...).get_tools()
agent = create_deep_agent(tools=tools)
```

---

## Monorepo Structure (deepagents-main/)

```
libs/
├── deepagents/          # Core SDK (pip install deepagents)
│   └── deepagents/
│       ├── graph.py     # create_deep_agent() — main entry point
│       ├── _models.py   # Model resolution
│       ├── backends/    # StateBackend, FilesystemBackend, SandboxBackend, etc.
│       └── middleware/  # skills.py, memory.py, subagents.py, summarization.py, etc.
├── cli/                 # Deep Agents CLI (Textual TUI)
│   └── deepagents_cli/
│       ├── app.py       # Main Textual app
│       ├── agent.py     # CLI agent wiring
│       ├── skills/      # Skill loading for CLI
│       └── hooks.py     # CLI hooks system
├── acp/                 # Agent Context Protocol support
└── harbor/              # Evaluation/benchmark framework
examples/
├── content-builder-agent/   # Full example: AGENTS.md + skills + subagents + image gen
├── deep_research/           # Parallel sub-agents + web research
├── text-to-sql-agent/       # Skills + SQL + planning
├── ralph_mode/              # Autonomous looping pattern
├── nvidia_deep_agent/       # GPU analytics skills
└── downloading_agents/      # Agents as downloadable zip folders
```

---

## Development (inside deepagents-main/)

```bash
uv run python agent.py "Your task"   # Run an agent
make test                             # Run unit tests
make lint                             # Lint with ruff
make format                           # Format with ruff
uv run --group test pytest tests/unit_tests/test_specific.py
```

- Package manager: `uv`
- Linter/formatter: `ruff`
- Type checker: `ty`
- Tests: `pytest` with `asyncio_mode = "auto"` (no `@pytest.mark.asyncio` needed)
- Docstrings: Google-style with Args/Returns/Raises sections
- Commit format: `feat(sdk): ...`, `fix(cli): ...`, `chore(harbor): ...`

---

## Key Patterns

### Minimal agent
```python
from deepagents import create_deep_agent
agent = create_deep_agent()
result = agent.invoke({"messages": [{"role": "user", "content": "Do X"}]})
```

### Agent with custom tools + model
```python
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

@tool
def my_tool(query: str) -> str:
    """Does something useful."""
    return "result"

agent = create_deep_agent(
    model=init_chat_model("openai:gpt-4o"),
    tools=[my_tool],
    system_prompt="You are a specialized assistant.",
)
```

### Agent with memory + skills + subagents (FilesystemBackend)
```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from pathlib import Path

agent = create_deep_agent(
    memory=["./AGENTS.md"],
    skills=["./skills/"],
    subagents=[{
        "name": "researcher",
        "description": "Searches the web for information.",
        "system_prompt": "You are a research assistant...",
        "model": "anthropic:claude-haiku-4-5-20251001",
        "tools": [web_search_tool],
    }],
    backend=FilesystemBackend(root_dir=Path(".")),
)
```

### Streaming with rich output
```python
import asyncio
async def run():
    async for chunk in agent.astream(
        {"messages": [("user", task)]},
        config={"configurable": {"thread_id": "t1"}},
        stream_mode="values",
    ):
        msgs = chunk.get("messages", [])
        if msgs:
            print(msgs[-1])

asyncio.run(run())
```
