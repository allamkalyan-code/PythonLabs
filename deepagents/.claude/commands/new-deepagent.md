Scaffold a new Deep Agent project in the current workspace.

Ask the user for:
1. **Project name** (e.g. `my-research-agent`) — used as the folder name
2. **What the agent should do** — a brief description of its purpose
3. **Model** — default is `anthropic:claude-sonnet-4-6`, ask if they want a different one
4. **Include skills?** (yes/no) — if yes, create a `skills/` folder with a starter SKILL.md
5. **Include subagents?** (yes/no) — if yes, scaffold a basic subagent

Then create the following structure:

```
<project-name>/
├── AGENTS.md              # Memory file — brand voice, role, preferences
├── agent.py               # Main entry point using create_deep_agent()
├── pyproject.toml         # uv-based project config
├── .env.example           # API key placeholders
├── skills/                # Only if skills requested
│   └── <skill-name>/
│       └── SKILL.md
└── README.md              # Brief usage instructions
```

**agent.py** must use this pattern:
```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from pathlib import Path
import asyncio

AGENT_DIR = Path(__file__).parent

def create_agent():
    return create_deep_agent(
        memory=["./AGENTS.md"],
        skills=["./skills/"],          # Remove if no skills
        backend=FilesystemBackend(root_dir=AGENT_DIR),
        system_prompt="<derived from user's description>",
    )

async def main(task: str):
    agent = create_agent()
    async for chunk in agent.astream(
        {"messages": [("user", task)]},
        config={"configurable": {"thread_id": "main"}},
        stream_mode="values",
    ):
        msgs = chunk.get("messages", [])
        if msgs:
            msg = msgs[-1]
            if hasattr(msg, "content") and msg.content:
                print(msg.content)

if __name__ == "__main__":
    import sys
    task = " ".join(sys.argv[1:]) or "Hello, what can you do?"
    asyncio.run(main(task))
```

**AGENTS.md** must be populated with:
- The agent's role based on the user's description
- Sensible defaults for tone, behavior, and workflow

**pyproject.toml** must use `uv` format:
```toml
[project]
name = "<project-name>"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "deepagents>=0.1.0",
    "langchain-anthropic>=0.3.0",
]

[tool.uv]
dev-dependencies = []
```

**SKILL.md** (if skills requested) must use valid frontmatter:
```markdown
---
name: <skill-name>
description: <what this skill does and when to use it>
license: MIT
---

# <Skill Name>

## When to Use
...

## Steps
...
```

After creating all files, print a summary of what was created and show the command to run the agent:
```
uv run python agent.py "Your task here"
```
