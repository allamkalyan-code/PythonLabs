"""Tests for the three agent loop guards in server/routers/agent.py.

Guards:
  1. Stall guard   — orchestrator makes STALL_LIMIT consecutive passes with no subagent call
  2. Loop guard    — same subagent called > LOOP_GUARD_LIMIT times in one run
  3. Emergency cap — orchestrator passes exceed MAX_PASSES (hard backstop)

Strategy: We don't call the real LLM. Instead we mock create_maaya_agent() to return
a fake agent whose astream_events() yields a controlled sequence of LangGraph events.
We then call _run_agent() directly and inspect the WebSocket frames that were sent.

Run with:  uv run pytest tests/test_loop_guards.py -v
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Shared fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-only")


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Temp SQLite DB so tests don't touch the real maaya.db."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", url)

    import server.database as db_mod
    db_mod.DATABASE_URL = url
    engine = create_engine(url, connect_args={"check_same_thread": False})
    db_mod.engine = engine
    db_mod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_mod.Base.metadata.create_all(bind=engine)
    return db_mod.SessionLocal


def _make_project(project_id: int = 1, path: str = "/tmp/proj") -> MagicMock:
    """Return a minimal Project-like object."""
    p = MagicMock()
    p.id = project_id
    p.path = path
    p.model = None
    return p


def _make_ws() -> tuple[MagicMock, list[dict]]:
    """Return a (fake WebSocket, list-of-sent-frames) pair."""
    sent: list[dict] = []

    async def _send_text(payload: str):
        import json
        sent.append(json.loads(payload))

    ws = MagicMock()
    ws.send_text = _send_text
    return ws, sent


# ── Event helpers — build fake LangGraph event dicts ─────────────────────────

def _model_end_event(text: str = "thinking...", agent_name: str = "maaya") -> dict:
    """on_chat_model_end event with a plain-string content chunk."""
    output = MagicMock()
    output.content = text
    output.tool_calls = []
    output.usage_metadata = None
    return {
        "event": "on_chat_model_end",
        "name": agent_name,
        "data": {"output": output},
    }


def _tool_start_event(subagent_type: str) -> dict:
    """on_tool_start event for the 'task' tool (subagent invocation)."""
    return {
        "event": "on_tool_start",
        "name": "task",
        "data": {"input": {"subagent_type": subagent_type}},
    }


def _tool_end_event(name: str = "task", output: str = "done") -> dict:
    """on_tool_end event."""
    return {
        "event": "on_tool_end",
        "name": name,
        "data": {"output": output, "input": {}},
    }


async def _fake_agent(events: list[dict]):
    """Async generator that yields a fixed sequence of events."""
    for e in events:
        yield e


# ── Helper: run _run_agent with a controlled event stream ────────────────────

async def _run(
    events: list[dict],
    isolated_db,
    *,
    project_id: int = 1,
) -> list[dict]:
    """
    Patch create_maaya_agent + set_current_project, then call _run_agent()
    with the supplied event list.  Returns the list of WS frames sent.

    _persist_message is patched to a no-op so tests don't need a fully
    initialised database — we're testing guard logic, not persistence.
    """
    from server.routers import agent as agent_mod

    ws, sent = _make_ws()
    project = _make_project(project_id=project_id)
    stop_event = asyncio.Event()
    db = MagicMock()  # DB not used — _persist_message is mocked below

    fake_agent_obj = MagicMock()
    fake_agent_obj.astream_events = MagicMock(
        return_value=_fake_agent(events)
    )

    with (
        patch("agents.maaya.create_maaya_agent", return_value=fake_agent_obj),
        patch("agents.tracker_tools.set_current_project"),
        patch.object(agent_mod, "_get_checkpointer", return_value=MagicMock()),
        patch.object(agent_mod, "_persist_message"),   # no-op — not under test
    ):
        await agent_mod._run_agent(ws, project, "test message", stop_event, db)

    return sent


def _frame_types(sent: list[dict]) -> list[str]:
    return [f["type"] for f in sent]


def _last_error(sent: list[dict]) -> str | None:
    errors = [f["content"] for f in sent if f.get("type") == "error"]
    return errors[-1] if errors else None


# ─────────────────────────────────────────────────────────────────────────────
# 1. Stall guard
# ─────────────────────────────────────────────────────────────────────────────

class TestStallGuard:
    """Orchestrator makes STALL_LIMIT consecutive passes with no subagent call."""

    async def test_stall_guard_fires_after_stall_limit_passes(self, isolated_db, monkeypatch):
        """Exactly STALL_LIMIT orchestrator model-end events → stall error emitted."""
        from server.routers.agent import STALL_LIMIT

        events = [_model_end_event(f"pass {i}") for i in range(STALL_LIMIT)]
        sent = await _run(events, isolated_db)

        assert "error" in _frame_types(sent), "Expected an error frame"
        assert "done" in _frame_types(sent), "done frame must always be sent"
        err = _last_error(sent)
        assert err is not None
        assert "stall" in err.lower() or "subagent" in err.lower(), (
            f"Error should mention stall/subagent, got: {err!r}"
        )

    async def test_stall_guard_does_not_fire_below_limit(self, isolated_db):
        """STALL_LIMIT - 1 passes without a subagent call must NOT trigger stall guard."""
        from server.routers.agent import STALL_LIMIT

        events = [_model_end_event(f"pass {i}") for i in range(STALL_LIMIT - 1)]
        sent = await _run(events, isolated_db)

        assert "error" not in _frame_types(sent), (
            "Should not error for fewer passes than STALL_LIMIT"
        )
        assert "done" in _frame_types(sent)

    async def test_subagent_call_resets_stall_counter(self, isolated_db):
        """Calling a subagent resets the stall counter — subsequent passes are fine."""
        from server.routers.agent import STALL_LIMIT

        # STALL_LIMIT - 1 orchestrator passes, then a subagent call, then STALL_LIMIT - 1 more
        # Total orchestrator passes without subagent in any window = STALL_LIMIT - 1 → no stall
        events = (
            [_model_end_event(f"pre-{i}") for i in range(STALL_LIMIT - 1)]
            + [_tool_start_event("planner"), _tool_end_event("task")]
            + [_model_end_event(f"post-{i}") for i in range(STALL_LIMIT - 1)]
        )
        sent = await _run(events, isolated_db)

        assert "error" not in _frame_types(sent), (
            "Subagent call must reset stall counter; no error expected"
        )

    async def test_stall_fires_even_after_initial_subagent_call(self, isolated_db):
        """After a subagent call, the stall window restarts from zero."""
        from server.routers.agent import STALL_LIMIT

        events = (
            [_tool_start_event("planner"), _tool_end_event("task")]
            + [_model_end_event(f"post-{i}") for i in range(STALL_LIMIT)]
        )
        sent = await _run(events, isolated_db)

        assert "error" in _frame_types(sent), (
            "After the subagent call, STALL_LIMIT passes should still trigger the guard"
        )
        err = _last_error(sent)
        assert "stall" in err.lower() or "subagent" in err.lower()


# ─────────────────────────────────────────────────────────────────────────────
# 2. Loop guard
# ─────────────────────────────────────────────────────────────────────────────

class TestLoopGuard:
    """Same subagent called more than LOOP_GUARD_LIMIT times."""

    async def test_loop_guard_fires_on_sixth_call(self, isolated_db):
        """Calling the same subagent LOOP_GUARD_LIMIT + 1 times triggers loop guard."""
        from server.routers.agent import LOOP_GUARD_LIMIT

        events = []
        for _ in range(LOOP_GUARD_LIMIT + 1):
            events += [
                _tool_start_event("planner"),
                _model_end_event("planner thinking", agent_name="planner"),
                _tool_end_event("task"),
                _model_end_event("orchestrator deciding"),
            ]

        sent = await _run(events, isolated_db)

        assert "error" in _frame_types(sent)
        err = _last_error(sent)
        assert "loop" in err.lower() or "planner" in err.lower(), (
            f"Error should mention loop/planner, got: {err!r}"
        )

    async def test_loop_guard_does_not_fire_at_limit(self, isolated_db):
        """Calling a subagent exactly LOOP_GUARD_LIMIT times must NOT trigger the guard."""
        from server.routers.agent import LOOP_GUARD_LIMIT

        events = []
        for _ in range(LOOP_GUARD_LIMIT):
            events += [
                _tool_start_event("backend"),
                _tool_end_event("task"),
                _model_end_event("orchestrator deciding"),
            ]

        sent = await _run(events, isolated_db)

        errors = [f for f in sent if f.get("type") == "error"]
        loop_errors = [e for e in errors if "loop" in e.get("content", "").lower()]
        assert not loop_errors, "Should not trigger loop guard at exactly LOOP_GUARD_LIMIT calls"

    async def test_different_subagents_do_not_cross_count(self, isolated_db):
        """Calls to different subagents must not share a counter."""
        from server.routers.agent import LOOP_GUARD_LIMIT

        # Call two different subagents LOOP_GUARD_LIMIT times each — no loop
        events = []
        for agent_name in ("backend", "frontend"):
            for _ in range(LOOP_GUARD_LIMIT):
                events += [
                    _tool_start_event(agent_name),
                    _tool_end_event("task"),
                    _model_end_event("orchestrator deciding"),
                ]

        sent = await _run(events, isolated_db)

        loop_errors = [
            f for f in sent
            if f.get("type") == "error" and "loop" in f.get("content", "").lower()
        ]
        assert not loop_errors, "Different subagents must not share loop counters"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Emergency backstop
# ─────────────────────────────────────────────────────────────────────────────

class TestEmergencyBackstop:
    """Hard MAX_PASSES cap — should only fire if both other guards somehow miss."""

    async def test_emergency_backstop_fires_at_max_passes(self, isolated_db, monkeypatch):
        """MAX_PASSES orchestrator passes with regular subagent calls triggers backstop."""
        from server.routers import agent as agent_mod
        # Override constants to make the test fast
        monkeypatch.setattr(agent_mod, "MAX_PASSES", 10)
        monkeypatch.setattr(agent_mod, "STALL_LIMIT", 999)    # disable stall guard
        monkeypatch.setattr(agent_mod, "LOOP_GUARD_LIMIT", 999)  # disable loop guard

        # Alternate: orchestrator pass → subagent call (so neither other guard fires)
        events = []
        for i in range(15):
            events += [
                _model_end_event(f"orchestrator pass {i}"),
                _tool_start_event("backend"),
                _tool_end_event("task"),
            ]

        sent = await _run(events, isolated_db)

        assert "error" in _frame_types(sent)
        err = _last_error(sent)
        assert "emergency" in err.lower() or "limit" in err.lower(), (
            f"Error should mention emergency/limit, got: {err!r}"
        )

    async def test_done_always_sent_even_on_backstop(self, isolated_db, monkeypatch):
        """done frame must be the last frame regardless of which guard fires."""
        from server.routers import agent as agent_mod
        monkeypatch.setattr(agent_mod, "MAX_PASSES", 5)
        monkeypatch.setattr(agent_mod, "STALL_LIMIT", 999)

        events = []
        for i in range(10):
            events += [
                _model_end_event(f"pass {i}"),
                _tool_start_event("backend"),
                _tool_end_event("task"),
            ]

        sent = await _run(events, isolated_db)

        assert sent[-1]["type"] == "done", (
            f"done must be the last frame, got: {sent[-1]['type']!r}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 4. Happy path — guards must NOT fire on a normal run
# ─────────────────────────────────────────────────────────────────────────────

class TestNoFalsePositives:
    """Guards must stay silent during a normal multi-story build."""

    async def test_normal_build_no_guards_fire(self, isolated_db):
        """9 stories delegated in sequence — no guard should trigger."""
        agents = ["planner", "architect", "backend", "backend", "frontend",
                  "database", "tester", "backend", "devops"]
        events = []
        for ag in agents:
            events += [
                _model_end_event(f"orchestrator deciding to call {ag}"),
                _tool_start_event(ag),
                _model_end_event(f"{ag} working", agent_name=ag),
                _tool_end_event("task"),
            ]
        # Final orchestrator summary
        events.append(_model_end_event("Build complete! Here's what was created."))

        sent = await _run(events, isolated_db)

        errors = [f for f in sent if f.get("type") == "error"]
        assert not errors, f"Expected no errors on a normal build, got: {errors}"
        assert "done" in _frame_types(sent)

    async def test_orchestrator_uses_tools_before_delegating(self, isolated_db):
        """Orchestrator reading tracker/files before calling a subagent is fine."""
        from server.routers.agent import STALL_LIMIT

        # Use fewer than STALL_LIMIT orchestrator passes, then delegate
        pre_passes = STALL_LIMIT - 2
        events = (
            [_model_end_event(f"checking state {i}") for i in range(pre_passes)]
            + [_tool_start_event("planner"), _tool_end_event("task")]
            + [_model_end_event("Done planning")]
        )

        sent = await _run(events, isolated_db)

        errors = [f for f in sent if f.get("type") == "error"]
        assert not errors, (
            f"Orchestrator reading state is legitimate and must not trigger stall guard: {errors}"
        )
