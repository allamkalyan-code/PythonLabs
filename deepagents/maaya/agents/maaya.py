"""Maaya v2 orchestrator — create_maaya_agent().

Returns a compiled LangGraph agent that:
- Receives user messages via the standard deepagents graph
- Delegates to specialist subagents (spec-evaluator in Phase 2)
- Streams tokens and messages over the caller's astream_events loop
- Uses FilesystemBackend(virtual_mode=True) scoped to the project directory
- Loads AGENTS.md and skills from Maaya's own root (separate backend)
- Uses a per-project MemorySaver for session isolation
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.middleware.memory import MemoryMiddleware
from deepagents.middleware.skills import SkillsMiddleware

from agents.model_config import get_model
from agents.tracker_tools import ALL_TRACKER_TOOLS

logger = logging.getLogger(__name__)

# Absolute path to this agents/ directory
_AGENTS_DIR = Path(__file__).parent

# Maaya's project root (contains AGENTS.md and skills/)
_MAAYA_ROOT = _AGENTS_DIR.parent


def _load_subagent_defs() -> list[dict]:
    """Load subagent definitions from subagents.yaml.

    Returns:
        List of subagent config dicts ready for create_deep_agent(subagents=...).
    """
    yaml_path = _AGENTS_DIR / "subagents.yaml"
    with open(yaml_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    subagent_defs = []
    for entry in raw.get("subagents", []):
        tier = entry.pop("tier", "balanced")
        entry["model"] = get_model(tier)
        subagent_defs.append(entry)
    return subagent_defs


def create_maaya_agent(
    project_path: str,
    checkpointer,
    *,
    model: str | None = None,
    interrupt_on: dict | None = None,
):
    """Create and return the Maaya orchestrator agent for a specific project.

    Each project gets its own agent instance bound to its directory via
    FilesystemBackend(virtual_mode=True), ensuring complete filesystem isolation.
    AGENTS.md and skills are loaded from Maaya's own root via a separate backend.

    Args:
        project_path: Absolute path to the user's project directory.
        checkpointer: LangGraph MemorySaver (or compatible) for session persistence.
        model: Optional model override. Defaults to balanced tier (sonnet-4-6).
        interrupt_on: HIL interrupt config, e.g. {"write_file": True}.

    Returns:
        Compiled LangGraph CompiledStateGraph ready for astream_events().
    """
    resolved_model = model or get_model("balanced")
    subagent_defs = _load_subagent_defs()

    # Backend scoped to the project directory — virtual_mode=True maps / to project root
    project_backend = FilesystemBackend(
        root_dir=Path(project_path),
        virtual_mode=True,
    )

    # Separate backend for Maaya's own AGENTS.md and skills (NOT virtual — real FS paths)
    maaya_backend = FilesystemBackend(
        root_dir=_MAAYA_ROOT,
        virtual_mode=False,
    )

    # Build extra middleware for memory (AGENTS.md) and skills, using Maaya's backend
    extra_middleware = []

    agents_md = _MAAYA_ROOT / "AGENTS.md"
    if agents_md.exists():
        extra_middleware.append(
            MemoryMiddleware(backend=maaya_backend, sources=["./AGENTS.md"])
        )

    skills_dir = _MAAYA_ROOT / "skills"
    if skills_dir.exists():
        extra_middleware.append(
            SkillsMiddleware(backend=maaya_backend, sources=["./skills/"])
        )

    agent = create_deep_agent(
        model=resolved_model,
        tools=ALL_TRACKER_TOOLS,
        subagents=subagent_defs,
        middleware=extra_middleware,
        backend=project_backend,
        checkpointer=checkpointer,
        interrupt_on=interrupt_on,
        debug=False,
        name="maaya",
    )

    logger.info(
        "Maaya agent created: project=%s model=%s subagents=%d memory=%s skills=%s",
        project_path,
        resolved_model,
        len(subagent_defs),
        agents_md.exists(),
        skills_dir.exists(),
    )
    return agent
