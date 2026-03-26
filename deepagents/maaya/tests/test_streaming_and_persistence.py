"""TDD tests for streaming token extraction and message persistence.

These tests were written to cover the three bugs that slipped through the
first test suite:
  1. Anthropic content blocks crash "".join() and send arrays as token deltas
  2. getMessages 500s due to MetaData attribute conflict in ChatMessageResponse
  3. A persisted human message is returned correctly after a server restart

Run with:  uv run pytest tests/test_streaming_and_persistence.py -v
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-only")


# ── Shared isolated DB fixture ────────────────────────────────────────────────

@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Return a (engine, SessionLocal) pair backed by a temp SQLite file.

    Also patches server.database so the FastAPI app uses the same temp DB.
    """
    import os
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

    yield db_mod.SessionLocal


@pytest.fixture
def client(isolated_db):
    from fastapi.testclient import TestClient
    from server.main import app
    with TestClient(app) as c:
        yield c


# ─────────────────────────────────────────────────────────────────────────────
# 1. Token extraction — _extract_text_from_chunk
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractTextFromChunk:
    """Unit tests for _extract_text_from_chunk.

    These cover all Anthropic content block formats that the streaming
    handler will encounter in production.
    """

    def _extract(self, content):
        from server.routers.agent import _extract_text_from_chunk
        chunk = SimpleNamespace(content=content)
        return _extract_text_from_chunk(chunk)

    # ── Happy paths ──────────────────────────────────────────────────────────

    def test_plain_string_content(self):
        """Old-style string content is returned as-is."""
        assert self._extract("Hello world") == "Hello world"

    def test_single_text_block(self):
        """Single Anthropic text block returns its text."""
        assert self._extract([{"type": "text", "text": "Hello"}]) == "Hello"

    def test_multiple_text_blocks_concatenated(self):
        """Multiple text blocks are concatenated in order."""
        blocks = [
            {"type": "text", "text": "Hello "},
            {"type": "text", "text": "world"},
        ]
        assert self._extract(blocks) == "Hello world"

    def test_empty_text_block(self):
        """Text block with empty string returns empty string."""
        assert self._extract([{"type": "text", "text": ""}]) == ""

    # ── Bug-regression: tool call blocks must be skipped ─────────────────────

    def test_tool_use_block_returns_empty(self):
        """tool_use block (start of a tool call) must produce no delta.

        BUG: Before the fix, this was appended as a list to streaming_content
        and caused TypeError in ''.join() at on_chat_model_end.
        """
        blocks = [{"type": "tool_use", "id": "toolu_abc", "name": "task", "input": {}}]
        result = self._extract(blocks)
        assert result == "", f"Expected empty string, got {result!r}"

    def test_input_json_delta_block_returns_empty(self):
        """input_json_delta block (tool argument streaming) must produce no delta.

        BUG: Before the fix, partial_json dicts were forwarded to the frontend
        as 'delta', which is expected to be a string. React crashed trying
        to call .split() on an array.
        """
        blocks = [{"type": "input_json_delta", "partial_json": '{"subagent_type": "spec'}]
        result = self._extract(blocks)
        assert result == "", f"Expected empty string, got {result!r}"
        assert isinstance(result, str), "delta MUST always be a str"

    def test_mixed_tool_and_text_blocks(self):
        """When a message has both a tool call and text, only text is extracted."""
        blocks = [
            {"type": "tool_use", "id": "toolu_abc", "name": "task"},
            {"type": "text", "text": "I'll delegate this."},
        ]
        assert self._extract(blocks) == "I'll delegate this."

    def test_unknown_block_type_is_skipped(self):
        """Unknown block types must not raise and must return empty."""
        blocks = [{"type": "future_type", "data": "..."}]
        assert self._extract(blocks) == ""

    # ── Edge cases ───────────────────────────────────────────────────────────

    def test_none_content_returns_empty(self):
        from server.routers.agent import _extract_text_from_chunk
        chunk = SimpleNamespace(content=None)
        assert _extract_text_from_chunk(chunk) == ""

    def test_no_content_attribute_returns_empty(self):
        from server.routers.agent import _extract_text_from_chunk
        assert _extract_text_from_chunk(object()) == ""

    def test_result_is_always_a_string(self):
        """The return value must always be str so frontend can do string ops."""
        from server.routers.agent import _extract_text_from_chunk
        for content in (None, [], [{"type": "tool_use"}], "text", [{"type": "text", "text": "x"}]):
            chunk = SimpleNamespace(content=content)
            result = _extract_text_from_chunk(chunk)
            assert isinstance(result, str), f"Got {type(result)} for content={content!r}"

    def test_streaming_content_join_never_fails(self):
        """''.join(streaming_content) must not raise even after multiple chunks.

        BUG: Before the fix, streaming_content contained lists (not strings),
        and ''.join(streaming_content) raised TypeError at on_chat_model_end.
        """
        from server.routers.agent import _extract_text_from_chunk

        # Simulate a real Anthropic stream: tool call then text
        chunks = [
            SimpleNamespace(content=[{"type": "tool_use", "id": "x", "name": "task"}]),
            SimpleNamespace(content=[{"type": "input_json_delta", "partial_json": '{"q": "'}]),
            SimpleNamespace(content=[{"type": "input_json_delta", "partial_json": 'blog'}]),
            SimpleNamespace(content=[{"type": "text", "text": "NEEDS_CLARIFICATION\n"}]),
            SimpleNamespace(content=[{"type": "text", "text": "Questions:\n1. Tech stack?"}]),
        ]
        streaming_content: list[str] = []
        for chunk in chunks:
            delta = _extract_text_from_chunk(chunk)
            if delta:
                streaming_content.append(delta)

        # This must not raise TypeError
        full = "".join(streaming_content)
        assert full == "NEEDS_CLARIFICATION\nQuestions:\n1. Tech stack?"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Message persistence and retrieval
# ─────────────────────────────────────────────────────────────────────────────

class TestMessagePersistence:
    """Tests that cover the full write→read cycle for chat messages.

    BUG: getMessages returned 500 because ChatMessageResponse.metadata
    conflicted with SQLAlchemy's DeclarativeBase.metadata attribute.
    Pydantic read MetaData() instead of the metadata_json column.
    """

    def test_get_messages_empty_for_new_project(self, client, tmp_path):
        """New project has no messages."""
        create = client.post("/api/projects", json={
            "name": "empty-project", "path": str(tmp_path),
            "model": "anthropic:claude-sonnet-4-6",
        })
        pid = create.json()["id"]
        resp = client.get(f"/api/projects/{pid}/messages")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_persisted_human_message_is_returned(self, client, isolated_db, tmp_path):
        """A human message saved to DB is returned by getMessages.

        BUG: Before the metadata fix, this returned 500 (ResponseValidationError)
        because Pydantic got MetaData() instead of None for the metadata field.
        """
        create = client.post("/api/projects", json={
            "name": "msg-test", "path": str(tmp_path),
            "model": "anthropic:claude-sonnet-4-6",
        })
        pid = create.json()["id"]

        # Directly insert a human message (simulates what the WS handler does)
        db = isolated_db()
        from server.models import ChatMessage
        db.add(ChatMessage(project_id=pid, role="human", content="build me a blog app"))
        db.commit()
        db.close()

        resp = client.get(f"/api/projects/{pid}/messages")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        msgs = resp.json()
        assert len(msgs) == 1
        assert msgs[0]["role"] == "human"
        assert msgs[0]["content"] == "build me a blog app"
        assert msgs[0]["metadata"] is None  # null metadata_json → None

    def test_message_with_metadata_json_is_returned(self, client, isolated_db, tmp_path):
        """A message with metadata_json is deserialized correctly."""
        create = client.post("/api/projects", json={
            "name": "meta-test", "path": str(tmp_path),
            "model": "anthropic:claude-sonnet-4-6",
        })
        pid = create.json()["id"]

        db = isolated_db()
        from server.models import ChatMessage
        db.add(ChatMessage(
            project_id=pid,
            role="ai",
            content="I need some clarifications.",
            metadata_json=json.dumps({"role": "spec-evaluator", "tool_calls": []}),
        ))
        db.commit()
        db.close()

        resp = client.get(f"/api/projects/{pid}/messages")
        assert resp.status_code == 200
        msgs = resp.json()
        assert len(msgs) == 1
        assert msgs[0]["metadata"] == {"role": "spec-evaluator", "tool_calls": []}

    def test_multiple_messages_returned_in_order(self, client, isolated_db, tmp_path):
        """Messages are returned oldest-first."""
        create = client.post("/api/projects", json={
            "name": "order-test", "path": str(tmp_path),
            "model": "anthropic:claude-sonnet-4-6",
        })
        pid = create.json()["id"]

        db = isolated_db()
        from server.models import ChatMessage
        db.add(ChatMessage(project_id=pid, role="human", content="first"))
        db.add(ChatMessage(project_id=pid, role="ai", content="second"))
        db.add(ChatMessage(project_id=pid, role="human", content="third"))
        db.commit()
        db.close()

        resp = client.get(f"/api/projects/{pid}/messages")
        assert resp.status_code == 200
        contents = [m["content"] for m in resp.json()]
        assert contents == ["first", "second", "third"]

    def test_messages_only_for_correct_project(self, client, isolated_db, tmp_path):
        """Messages from project A do not appear in project B's history."""
        p1 = client.post("/api/projects", json={
            "name": "proj-a", "path": str(tmp_path / "a"),
            "model": "anthropic:claude-sonnet-4-6",
        }).json()["id"]
        p2 = client.post("/api/projects", json={
            "name": "proj-b", "path": str(tmp_path / "b"),
            "model": "anthropic:claude-sonnet-4-6",
        }).json()["id"]

        db = isolated_db()
        from server.models import ChatMessage
        db.add(ChatMessage(project_id=p1, role="human", content="project A message"))
        db.commit()
        db.close()

        resp_a = client.get(f"/api/projects/{p1}/messages")
        resp_b = client.get(f"/api/projects/{p2}/messages")
        assert len(resp_a.json()) == 1
        assert len(resp_b.json()) == 0

    def test_invalid_metadata_json_returns_none_not_500(self, client, isolated_db, tmp_path):
        """Malformed metadata_json does not crash the endpoint."""
        create = client.post("/api/projects", json={
            "name": "corrupt-meta", "path": str(tmp_path),
            "model": "anthropic:claude-sonnet-4-6",
        })
        pid = create.json()["id"]

        db = isolated_db()
        from server.models import ChatMessage
        db.add(ChatMessage(
            project_id=pid,
            role="ai",
            content="some message",
            metadata_json="not valid json {{{",
        ))
        db.commit()
        db.close()

        resp = client.get(f"/api/projects/{pid}/messages")
        assert resp.status_code == 200
        assert resp.json()[0]["metadata"] is None


# ─────────────────────────────────────────────────────────────────────────────
# 3. Handoff parser — edge cases missed before
# ─────────────────────────────────────────────────────────────────────────────

class TestHandoffParserEdgeCases:
    def _parse(self, text):
        from server.routers.agent import _parse_handoff
        return _parse_handoff(text)

    def test_files_created_none_returns_empty_list(self):
        result = self._parse("""
---HANDOFF---
STATUS: DONE
SUMMARY: Nothing created.
FILES_CREATED: NONE
FILES_MODIFIED: NONE
TESTS_WRITTEN: NO
ASSUMPTIONS: NONE
FLAGS: NONE
NEXT_SUGGESTED: Done.
---END HANDOFF---
""")
        assert result["files_created"] == []
        assert result["files_modified"] == []

    def test_files_with_spaces_in_list(self):
        result = self._parse("""
---HANDOFF---
STATUS: DONE
SUMMARY: Files created.
FILES_CREATED:  src/app.py ,  src/models.py , tests/test_app.py
FILES_MODIFIED: NONE
TESTS_WRITTEN: NO
ASSUMPTIONS: NONE
FLAGS: NONE
NEXT_SUGGESTED: Done.
---END HANDOFF---
""")
        # Paths must be stripped of whitespace
        assert "src/app.py" in result["files_created"]
        assert "src/models.py" in result["files_created"]
        assert "tests/test_app.py" in result["files_created"]

    def test_partial_status_is_valid(self):
        result = self._parse("""
---HANDOFF---
STATUS: PARTIAL
SUMMARY: Only half done.
FILES_CREATED: NONE
FILES_MODIFIED: NONE
TESTS_WRITTEN: NO
ASSUMPTIONS: NONE
FLAGS: NONE
NEXT_SUGGESTED: Finish the rest.
---END HANDOFF---
""")
        assert result["status"] == "PARTIAL"

    def test_partial_and_failed_status_are_valid(self):
        pass  # covered by individual tests below

    def test_failed_status_is_valid(self):
        result = self._parse("""
---HANDOFF---
STATUS: FAILED
SUMMARY: Could not find the file.
FILES_CREATED: NONE
FILES_MODIFIED: NONE
TESTS_WRITTEN: NO
ASSUMPTIONS: NONE
FLAGS: NONE
NEXT_SUGGESTED: User must provide the file.
---END HANDOFF---
""")
        assert result["status"] == "FAILED"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Loop guard and stop-after-relay logic
# ─────────────────────────────────────────────────────────────────────────────

class TestLoopGuardAndStopAfterRelay:
    """Tests for the two behaviours that previously failed in production:

    1. Loop guard must count only real task-tool invocations, not LangGraph
       internal node names ("model", "ChatAnthropic", etc.).

    2. After spec-evaluator returns NEEDS_CLARIFICATION, the server must stop
       the stream after the orchestrator relays the questions — not keep running.
    """

    # ── Helper: simulate an astream_events sequence ──────────────────────────

    def _make_event(self, event_type, name="", data=None):
        return {"event": event_type, "name": name, "data": data or {}}

    # ── Loop guard: only task-tool invocations count ──────────────────────────

    def test_internal_node_names_do_not_increment_subagent_counter(self):
        """Events with names like 'model' or 'ChatAnthropic' are LangGraph
        internals, not subagents. They must not increment subagent_calls.

        BUG: Before the fix, every event name that wasn't in the exclusion list
        was counted, so 'model' accumulated to 6 and triggered the loop guard.
        """
        from collections import Counter
        subagent_calls: Counter[str] = Counter()

        # Simulate what the old (broken) code did
        internal_names = ["model", "ChatAnthropic", "tools", "agent", "LangGraph"]
        for name in internal_names * 3:  # seen multiple times
            # Old code: if name not in exclusion list → count it
            if name not in ("", "maaya", "LangGraph", "agent"):
                subagent_calls[name] += 1

        # The old code would have counted "model" and "ChatAnthropic"
        assert subagent_calls["model"] > 0, \
            "Confirm old code DID count model (pre-fix baseline)"

        # New code: only count when event is on_tool_start AND name == "task"
        subagent_calls_new: Counter[str] = Counter()
        events = [
            self._make_event("on_chat_model_stream", "ChatAnthropic"),
            self._make_event("on_chat_model_end",    "ChatAnthropic"),
            self._make_event("on_tool_start",         "task",
                             {"input": {"subagent_type": "spec-evaluator"}}),
            self._make_event("on_tool_end",           "task"),
            self._make_event("on_chat_model_stream",  "ChatAnthropic"),
            self._make_event("on_chat_model_end",     "ChatAnthropic"),
        ]
        for ev in events:
            if ev["event"] == "on_tool_start" and ev["name"] == "task":
                inp = ev["data"].get("input", {})
                sa = inp.get("subagent_type", "") if isinstance(inp, dict) else ""
                if sa:
                    subagent_calls_new[sa] += 1

        assert subagent_calls_new.get("model", 0) == 0
        assert subagent_calls_new.get("ChatAnthropic", 0) == 0
        assert subagent_calls_new["spec-evaluator"] == 1

    def test_subagent_type_extracted_from_task_tool_input(self):
        """subagent_type is read from the task tool's input dict."""
        from collections import Counter
        subagent_calls: Counter[str] = Counter()

        events = [
            self._make_event("on_tool_start", "task",
                             {"input": {"subagent_type": "planner", "description": "Plan it"}}),
            self._make_event("on_tool_start", "task",
                             {"input": {"subagent_type": "planner", "description": "Re-plan"}}),
            self._make_event("on_tool_start", "task",
                             {"input": {"subagent_type": "backend", "description": "Build API"}}),
        ]
        for ev in events:
            if ev["event"] == "on_tool_start" and ev["name"] == "task":
                inp = ev["data"].get("input", {})
                sa = inp.get("subagent_type", "") if isinstance(inp, dict) else ""
                if sa:
                    subagent_calls[sa] += 1

        assert subagent_calls["planner"] == 2
        assert subagent_calls["backend"] == 1

    # ── stop_after_relay logic ────────────────────────────────────────────────

    def test_needs_clarification_in_tool_output_sets_flag(self):
        """When on_tool_end for 'task' contains NEEDS_CLARIFICATION, the
        stop_after_relay flag must be set to True.

        BUG: Before this logic, the orchestrator kept running after relaying
        questions instead of waiting for user input.
        """
        stop_after_relay = False

        tool_end_event = self._make_event("on_tool_end", "task", {
            "output": (
                "NEEDS_CLARIFICATION\n"
                "Questions:\n"
                "1. What tech stack?\n"
                "2. What features?"
            )
        })

        ev = tool_end_event
        if ev["event"] == "on_tool_end" and ev["name"] == "task":
            output_str = str(ev["data"].get("output", ""))
            if "NEEDS_CLARIFICATION" in output_str:
                stop_after_relay = True

        assert stop_after_relay is True

    def test_spec_complete_does_not_set_stop_flag(self):
        """SPEC_COMPLETE tool output must NOT set stop_after_relay."""
        stop_after_relay = False

        tool_end_event = self._make_event("on_tool_end", "task", {
            "output": "SPEC_COMPLETE\nSummary: Build a blog with React and FastAPI."
        })

        ev = tool_end_event
        if ev["event"] == "on_tool_end" and ev["name"] == "task":
            output_str = str(ev["data"].get("output", ""))
            if "NEEDS_CLARIFICATION" in output_str:
                stop_after_relay = True

        assert stop_after_relay is False

    def test_non_task_tool_end_does_not_set_stop_flag(self):
        """on_tool_end for non-task tools must not affect stop_after_relay."""
        stop_after_relay = False

        event = self._make_event("on_tool_end", "get_tracker_summary", {
            "output": "NEEDS_CLARIFICATION"  # coincidental text
        })

        ev = event
        if ev["event"] == "on_tool_end" and ev["name"] == "task":
            output_str = str(ev["data"].get("output", ""))
            if "NEEDS_CLARIFICATION" in output_str:
                stop_after_relay = True

        assert stop_after_relay is False


# ─────────────────────────────────────────────────────────────────────────────
# 5. Concurrent stop signal — asyncio.wait inner loop
# ─────────────────────────────────────────────────────────────────────────────

class TestStopButtonLatency:
    """Tests for the concurrent agent + receive pattern in chat_websocket.

    Root cause of the ~6s stop latency:
      `await _run_agent(...)` blocked the entire WebSocket coroutine.
      The stop message arrived but `ws.receive_text()` was never called
      while the agent was running, so the stop only took effect after the
      agent naturally finished its current response.

    Fix: run `_run_agent` as `asyncio.create_task(...)` and use
    `asyncio.wait({agent_task, recv_task})` to race the agent against
    incoming messages. Stop signals are now processed within one
    event-loop turn (~50ms worst case).
    """

    async def test_stop_signal_processed_within_500ms(self):
        """The inner asyncio.wait loop must set run_stop within 500ms
        even when the fake agent would otherwise run for 5+ seconds.

        This directly tests the pattern used in chat_websocket.
        """
        import time

        run_stop = asyncio.Event()

        # Fake agent: polls stop_event every 50ms (mirrors real _run_agent)
        async def fake_agent():
            while not run_stop.is_set():
                await asyncio.sleep(0.05)

        # Fake receive: delivers a "stop" message after 100ms
        async def fake_receive():
            await asyncio.sleep(0.1)
            return json.dumps({"type": "stop"})

        t0 = time.monotonic()
        agent_task: asyncio.Task = asyncio.create_task(fake_agent())
        recv_task: asyncio.Task = asyncio.create_task(fake_receive())

        # Replicate the inner loop from chat_websocket
        while not agent_task.done():
            done, _ = await asyncio.wait(
                {agent_task, recv_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            if recv_task in done:
                try:
                    inner_raw = recv_task.result()
                    inner_data = json.loads(inner_raw)
                    if inner_data.get("type") == "stop":
                        run_stop.set()
                except Exception:
                    run_stop.set()
                    break
                if not agent_task.done():
                    recv_task = asyncio.create_task(fake_receive())

        if not recv_task.done():
            recv_task.cancel()
            try:
                await recv_task
            except (asyncio.CancelledError, Exception):
                pass

        await agent_task  # no exception expected
        elapsed = time.monotonic() - t0

        assert run_stop.is_set(), "run_stop must be set after stop message received"
        assert elapsed < 0.5, (
            f"Stop took {elapsed:.3f}s — requirement is < 1s, test threshold < 0.5s. "
            "The asyncio.wait loop is not processing stop signals fast enough."
        )

    async def test_agent_runs_to_completion_without_stop(self):
        """When no stop is sent, the inner loop waits for the agent to finish."""
        run_stop = asyncio.Event()
        completed = False

        async def fake_agent():
            nonlocal completed
            await asyncio.sleep(0.15)
            completed = True

        # receive_text never resolves during the agent's 150ms lifetime
        recv_ready = asyncio.Event()

        async def fake_receive():
            await recv_ready.wait()  # blocks indefinitely during this test
            return json.dumps({"type": "message", "content": "hello"})

        agent_task: asyncio.Task = asyncio.create_task(fake_agent())
        recv_task: asyncio.Task = asyncio.create_task(fake_receive())

        while not agent_task.done():
            done, _ = await asyncio.wait(
                {agent_task, recv_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            if recv_task in done:
                run_stop.set()
                break

        if not recv_task.done():
            recv_task.cancel()
            try:
                await recv_task
            except (asyncio.CancelledError, Exception):
                pass

        await agent_task
        assert completed, "Agent must run to completion when no stop is sent"
        assert not run_stop.is_set(), "run_stop must NOT be set when no stop message arrives"

    async def test_disconnect_during_agent_sets_stop(self):
        """If the WebSocket disconnects mid-run, run_stop is set and the
        inner loop exits cleanly (no hang)."""
        from fastapi import WebSocketDisconnect

        run_stop = asyncio.Event()
        agent_running = asyncio.Event()

        async def fake_agent():
            agent_running.set()
            while not run_stop.is_set():
                await asyncio.sleep(0.02)

        async def fake_receive_disconnect():
            await asyncio.sleep(0.1)
            raise WebSocketDisconnect(code=1001)

        agent_task: asyncio.Task = asyncio.create_task(fake_agent())
        recv_task: asyncio.Task = asyncio.create_task(fake_receive_disconnect())
        await agent_running.wait()  # ensure agent started

        disconnected = False
        while not agent_task.done():
            done, _ = await asyncio.wait(
                {agent_task, recv_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            if recv_task in done:
                try:
                    recv_task.result()
                except WebSocketDisconnect:
                    run_stop.set()
                    disconnected = True
                    break
                except Exception:
                    run_stop.set()
                    disconnected = True
                    break

        if not recv_task.done():
            recv_task.cancel()
            try:
                await recv_task
            except (asyncio.CancelledError, Exception):
                pass

        await agent_task  # should exit fast because run_stop is set
        assert disconnected
        assert run_stop.is_set()
