"""WebSocket endpoint for streaming Maaya agent responses.

Implements:
- Token-level streaming via astream_events
- Cooperative stop via asyncio.Event
- Auto-continue guard (max 10 passes per user message)
- Loop guard (same subagent > 5 times → halt)
- Handoff block parsing → handoff frame to frontend
- 15-second ping keepalive
- done always sent in finally block
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from collections import Counter
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from server.database import SessionLocal
from server.models import ChatMessage, Project

logger = logging.getLogger(__name__)
router = APIRouter(tags=["agent"])

# ── Constants ────────────────────────────────────────────────────────────────

MAX_PASSES = 200         # hard emergency backstop (should never be reached in normal use)
LOOP_GUARD_LIMIT = 5     # max times same subagent may be called in one run
STALL_LIMIT = 15         # orchestrator passes in a row with NO subagent call → stalled
PING_INTERVAL = 15.0     # seconds between WS keepalive pings

# ── Per-project session state ────────────────────────────────────────────────

# project_id → MemorySaver
_project_checkpointers: dict[int, Any] = {}

# project_id → asyncio.Event (set = stop requested)
_stop_events: dict[int, asyncio.Event] = {}


def clear_project_session(project_id: int) -> None:
    """Remove the in-memory LangGraph checkpointer for this project.

    Called by reset-session and delete-project endpoints so the next message
    starts with a completely clean LangGraph thread.
    """
    _project_checkpointers.pop(project_id, None)


def _get_checkpointer(project_id: int) -> Any:
    """Return (or create) the MemorySaver for this project."""
    if project_id not in _project_checkpointers:
        from langgraph.checkpoint.memory import MemorySaver
        _project_checkpointers[project_id] = MemorySaver()
    return _project_checkpointers[project_id]


def _get_stop_event(project_id: int) -> asyncio.Event:
    """Return (or create) the stop event for this project."""
    if project_id not in _stop_events:
        _stop_events[project_id] = asyncio.Event()
    return _stop_events[project_id]


# ── DB helpers ───────────────────────────────────────────────────────────────

def _persist_message(
    db: Session,
    project_id: int,
    role: str,
    content: str,
    metadata: dict | None = None,
) -> None:
    """Save a chat message to the database."""
    msg = ChatMessage(
        project_id=project_id,
        role=role,
        content=content,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(msg)
    db.commit()


# ── Handoff block parser ─────────────────────────────────────────────────────

_HANDOFF_RE = re.compile(
    r"---HANDOFF---\s*(.*?)\s*---END HANDOFF---",
    re.DOTALL | re.IGNORECASE,
)
_CP1_RE = re.compile(
    r"---CHECKPOINT_1---\s*(.*?)\s*---END CHECKPOINT_1---",
    re.DOTALL | re.IGNORECASE,
)
_CP2_RE = re.compile(
    r"---CHECKPOINT_2---\s*(.*?)\s*---END CHECKPOINT_2---",
    re.DOTALL | re.IGNORECASE,
)
_FIELD_RE = re.compile(r"^(\w+):\s*(.+)$", re.MULTILINE)


def _parse_checkpoint_1(text: str) -> dict | None:
    """Parse a ---CHECKPOINT_1--- block from the orchestrator's message.

    Returns a dict ready to use as a checkpoint WebSocket frame payload,
    or None if no block is found.
    """
    m = _CP1_RE.search(text)
    if not m:
        return None

    body = m.group(1)
    fields: dict[str, str] = {}
    for fm in _FIELD_RE.finditer(body):
        fields[fm.group(1).strip().upper()] = fm.group(2).strip()

    summary = fields.get("SUMMARY", "Plan is ready for review.")
    epics = fields.get("EPICS", "?")
    stories = fields.get("STORIES", "?")
    points = fields.get("ESTIMATED_POINTS", "?")

    body_text = f"{summary}\n\n• {epics} epic(s)  ·  {stories} stories  ·  {points} estimated story points"

    return {
        "title": "Plan Ready — Approve to start building",
        "body": body_text,
        "options": [
            {"label": "Approve", "value": "approve"},
            {"label": "Request changes", "value": "request_changes"},
        ],
    }


def _parse_checkpoint_2(text: str) -> dict | None:
    """Parse a ---CHECKPOINT_2--- block from the orchestrator's message.

    Returns a dict ready to use as a checkpoint WebSocket frame payload,
    or None if no block is found.
    """
    m = _CP2_RE.search(text)
    if not m:
        return None

    body = m.group(1)
    fields: dict[str, str] = {}
    for fm in _FIELD_RE.finditer(body):
        fields[fm.group(1).strip().upper()] = fm.group(2).strip()

    story = fields.get("STORY", "current story")
    test_files = fields.get("TEST_FILES", "")
    ac_count = fields.get("AC_COUNT", "?")
    summary = fields.get("SUMMARY", "Tests are ready for review.")

    body_text = (
        f"{summary}\n\n"
        f"• Story: {story}\n"
        f"• Test files: {test_files or 'see above'}\n"
        f"• Acceptance criteria covered: {ac_count}"
    )

    return {
        "title": "Tests Written — Approve to start implementation",
        "body": body_text,
        "options": [
            {"label": "Approve", "value": "approve"},
            {"label": "Skip tests", "value": "skip_tests"},
        ],
    }


def _parse_handoff(text: str) -> dict | None:
    """Parse a ---HANDOFF--- block from agent response text.

    Returns:
        Dict with handoff fields, or None if no block found.
    """
    m = _HANDOFF_RE.search(text)
    if not m:
        return None

    body = m.group(1)
    fields: dict[str, str] = {}
    for fm in _FIELD_RE.finditer(body):
        key = fm.group(1).strip().upper()
        val = fm.group(2).strip()
        fields[key] = val

    # Parse structured sub-fields
    files_created = [p.strip() for p in fields.get("FILES_CREATED", "NONE").split(",") if p.strip() and p.strip() != "NONE"]
    files_modified = [p.strip() for p in fields.get("FILES_MODIFIED", "NONE").split(",") if p.strip() and p.strip() != "NONE"]
    tests_raw = fields.get("TESTS_WRITTEN", "NO").upper()
    tests_written = tests_raw.startswith("YES")
    flags_raw = fields.get("FLAGS", "NONE")
    flags = [] if flags_raw.strip().upper() == "NONE" else [f.strip() for f in flags_raw.split(",")]

    return {
        "status": fields.get("STATUS", "DONE").upper(),
        "summary": fields.get("SUMMARY", ""),
        "files_created": files_created,
        "files_modified": files_modified,
        "tests_written": tests_written,
        "assumptions": fields.get("ASSUMPTIONS", "NONE"),
        "flags": flags,
        "next_suggested": fields.get("NEXT_SUGGESTED", ""),
    }


# ── WebSocket send helpers ───────────────────────────────────────────────────

async def _send(ws: WebSocket, payload: dict) -> None:
    """Send a JSON frame; silently swallow errors if connection is closed."""
    try:
        await ws.send_text(json.dumps(payload))
    except Exception:
        pass


# ── Content extraction helpers ───────────────────────────────────────────────

def _extract_text_from_chunk(chunk: object) -> str:
    """Extract only human-readable text from an Anthropic AIMessageChunk.

    Anthropic streams content as a list of typed blocks, e.g.:
      [{"type": "text",             "text": "Hello"}]          — text
      [{"type": "tool_use",         "id": "...", ...}]         — tool call start (skip)
      [{"type": "input_json_delta", "partial_json": "..."}]    — tool args (skip)

    Only "text" blocks are forwarded to the frontend as token deltas.
    All other block types (tool_use, input_json_delta, etc.) are silently ignored.

    Args:
        chunk: An AIMessageChunk from LangChain (or any object with a .content attribute).

    Returns:
        The concatenated text from all text-type content blocks, or "" if none.
    """
    raw = getattr(chunk, "content", None)
    if isinstance(raw, list):
        return "".join(
            block.get("text", "")
            for block in raw
            if isinstance(block, dict) and block.get("type") == "text"
        )
    if isinstance(raw, str):
        return raw
    return ""


# ── Streaming runner ─────────────────────────────────────────────────────────

async def _run_agent(
    ws: WebSocket,
    project: Project,
    user_text: str,
    stop_event: asyncio.Event,
    db: Session,
) -> None:
    """Run the Maaya agent for one user message, streaming all events to ws.

    Sends frames: start, agent_status, token, message, task_complete,
                  handoff, flags_alert, error, done.

    The done frame is ALWAYS sent (in finally), even if stop was requested.
    """
    from agents.maaya import create_maaya_agent
    from agents.tracker_tools import set_current_project

    set_current_project(project.id)
    checkpointer = _get_checkpointer(project.id)
    agent = create_maaya_agent(
        project_path=project.path,
        checkpointer=checkpointer,
        model=project.model or None,
    )

    thread_id = f"project-{project.id}"
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": int(__import__("os").getenv("MAAYA_RECURSION_LIMIT", "100")),
    }

    input_msg = {"messages": [{"role": "user", "content": user_text}]}

    await _send(ws, {"type": "start"})

    pass_count = 0
    stall_passes = 0          # orchestrator model calls since last subagent invocation
    subagent_calls: Counter[str] = Counter()
    current_agent = "maaya"
    streaming_content: list[str] = []  # accumulates the current AI message
    total_input_tokens = 0
    total_output_tokens = 0
    run_start = time.monotonic()
    # Set to True when a subagent signals NEEDS_CLARIFICATION so the server
    # stops the loop after the orchestrator relays the questions to the user.
    stop_after_relay = False

    try:
        async for event in agent.astream_events(input_msg, config=config, version="v2"):
            # ── Cooperative stop check ────────────────────────────────────────
            if stop_event.is_set():
                logger.info("Stop requested for project %d", project.id)
                break

            event_name = event.get("event", "")
            event_data = event.get("data", {})

            # ── Detect subagent entry/exit via task tool calls ────────────────
            # LangGraph emits many internal node names ("model", "ChatAnthropic",
            # etc.) via event["name"]. Counting those as subagents is wrong.
            # Instead, track the deepagents `task` tool: subagent_type comes from
            # the tool's input args, which is the real subagent name.
            if event_name == "on_tool_start" and event.get("name") == "task":
                tool_input = event_data.get("input", {})
                subagent_type: str = (
                    tool_input.get("subagent_type", "")
                    if isinstance(tool_input, dict) else ""
                )
                if subagent_type:
                    current_agent = subagent_type
                    subagent_calls[subagent_type] += 1
                    stall_passes = 0  # any subagent call proves the orchestrator is making progress

                    # Loop guard — only real subagent invocations count
                    if subagent_calls[subagent_type] > LOOP_GUARD_LIMIT:
                        msg = (
                            f"Loop detected: subagent '{subagent_type}' has been called "
                            f"{subagent_calls[subagent_type]} times in this run. "
                            "Stopping to prevent an infinite loop."
                        )
                        await _send(ws, {"type": "error", "content": msg})
                        _persist_message(db, project.id, "error", msg)
                        return

                    await _send(ws, {
                        "type": "agent_status",
                        "agent": subagent_type,
                        "action": "running",
                        "step": sum(subagent_calls.values()),
                    })

            elif event_name == "on_tool_end" and event.get("name") == "task":
                # Subagent finished — reset label back to orchestrator
                current_agent = "maaya"
                # If the subagent signalled it needs more info from the user,
                # let the orchestrator relay the questions then stop the loop.
                tool_output = event_data.get("output", "")
                output_str = str(tool_output) if tool_output else ""
                if "NEEDS_CLARIFICATION" in output_str:
                    stop_after_relay = True

            # ── Token streaming ───────────────────────────────────────────────
            if event_name == "on_chat_model_stream":
                chunk = event_data.get("chunk", {})
                text_delta = _extract_text_from_chunk(chunk)
                if text_delta:
                    streaming_content.append(text_delta)
                    # Include the speaking role so the frontend can style
                    # subagent tokens as an inner monolog (gray) vs normal (white)
                    await _send(ws, {"type": "token", "delta": text_delta, "role": current_agent})

            # ── Completed AI message ──────────────────────────────────────────
            elif event_name == "on_chat_model_end":
                output = event_data.get("output", {})

                # Extract token usage
                usage = None
                if hasattr(output, "usage_metadata"):
                    usage = output.usage_metadata
                elif isinstance(output, dict):
                    usage = output.get("usage_metadata")

                input_tokens = 0
                output_tokens = 0
                if usage:
                    input_tokens = getattr(usage, "input_tokens", 0) or usage.get("input_tokens", 0)
                    output_tokens = getattr(usage, "output_tokens", 0) or usage.get("output_tokens", 0)
                    total_input_tokens += input_tokens
                    total_output_tokens += output_tokens

                # Assemble full content
                full_content = "".join(streaming_content)
                streaming_content.clear()

                # Extract tool calls if any
                tool_calls_raw = []
                if hasattr(output, "tool_calls"):
                    tool_calls_raw = output.tool_calls or []
                elif isinstance(output, dict):
                    tool_calls_raw = output.get("tool_calls", [])

                tool_calls = [
                    {
                        "id": tc.get("id", "") if isinstance(tc, dict) else getattr(tc, "id", ""),
                        "name": tc.get("name", "") if isinstance(tc, dict) else getattr(tc, "name", ""),
                        "args": tc.get("args", {}) if isinstance(tc, dict) else getattr(tc, "args", {}),
                    }
                    for tc in tool_calls_raw
                ]

                if full_content:
                    if current_agent == "maaya":
                        # Check for CHECKPOINT_1 signal before sending to frontend.
                        # Strip the block from the displayed message so users see only
                        # the human-readable plan summary, then show the approval card.
                        checkpoint_1 = _parse_checkpoint_1(full_content)
                        display_content = re.sub(
                            r"\s*---CHECKPOINT_1---.*?---END CHECKPOINT_1---",
                            "",
                            full_content,
                            flags=re.DOTALL | re.IGNORECASE,
                        ).strip()

                        # Orchestrator user-facing message — full chat bubble
                        msg_payload: dict = {
                            "type": "message",
                            "data": {
                                "type": "ai",
                                "content": display_content or full_content,
                                "tool_calls": tool_calls,
                                "timestamp": int(time.time() * 1000),
                                "role": current_agent,
                            },
                        }
                        await _send(ws, msg_payload)
                        _persist_message(
                            db, project.id, "ai", display_content or full_content,
                            metadata={"role": current_agent, "tool_calls": tool_calls} if tool_calls else None,
                        )

                        # Emit checkpoint frame and stop — server waits for user response
                        if checkpoint_1:
                            cp_id = f"cp1-{project.id}-{int(time.time())}"
                            await _send(ws, {"type": "checkpoint", "id": cp_id, **checkpoint_1})
                            _persist_message(
                                db, project.id, "checkpoint",
                                json.dumps(checkpoint_1),
                                metadata={"id": cp_id},
                            )
                            logger.info("Checkpoint 1 sent for project %d — stopping run", project.id)
                            return  # pause; chat_websocket handles checkpoint_response

                        checkpoint_2 = _parse_checkpoint_2(display_content or full_content)
                        if checkpoint_2:
                            cp_id = f"cp2-{project.id}-{int(time.time())}"
                            # Strip the CP2 block from the displayed message
                            display_content = re.sub(
                                r"\s*---CHECKPOINT_2---.*?---END CHECKPOINT_2---",
                                "",
                                display_content or full_content,
                                flags=re.DOTALL | re.IGNORECASE,
                            ).strip()
                            # Re-send the cleaned message (replaces the one sent above)
                            await _send(ws, {
                                "type": "checkpoint", "id": cp_id, **checkpoint_2,
                            })
                            _persist_message(
                                db, project.id, "checkpoint",
                                json.dumps(checkpoint_2),
                                metadata={"id": cp_id},
                            )
                            logger.info("Checkpoint 2 sent for project %d — stopping run", project.id)
                            return  # pause; chat_websocket handles checkpoint_response
                    else:
                        # Subagent internal response — inner monolog (gray collapsible)
                        await _send(ws, {
                            "type": "inner",
                            "role": current_agent,
                            "content": full_content,
                        })
                        _persist_message(
                            db, project.id, "inner", full_content,
                            metadata={"role": current_agent},
                        )
                # Tool-call-only frames (no text) are intentionally skipped — they
                # are already surfaced via agent_status and would just clutter the chat.

                # Parse handoff block (subagents always embed one in their response)
                if full_content:
                    handoff = _parse_handoff(full_content)
                    if handoff:
                        await _send(ws, {"type": "handoff", "agent": current_agent, **handoff})
                        _persist_message(
                            db, project.id, "handoff", json.dumps(handoff),
                            metadata={"agent": current_agent},
                        )

                        # Surface flags
                        if handoff["flags"]:
                            await _send(ws, {
                                "type": "flags_alert",
                                "agent": current_agent,
                                "flags": handoff["flags"],
                            })

                        # Stop pipeline on BLOCKED or FAILED
                        if handoff["status"] in ("BLOCKED", "FAILED"):
                            error_msg = (
                                f"Subagent '{current_agent}' reported {handoff['status']}: "
                                f"{handoff['summary']}"
                            )
                            await _send(ws, {"type": "error", "content": error_msg})
                            _persist_message(db, project.id, "error", error_msg)
                            return

                # Emit cost frame
                if input_tokens or output_tokens:
                    cost_usd = _estimate_cost(project.model, input_tokens, output_tokens)
                    await _send(ws, {
                        "type": "task_complete",
                        "agent": current_agent,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "cost_usd": cost_usd,
                    })

                # Only count orchestrator (maaya) model calls against the limits.
                # Subagent internal model calls (planner creating tracker entries, etc.)
                # must not consume the budget — they are one logical step.
                if current_agent == "maaya":
                    pass_count += 1
                    stall_passes += 1

                    # Stall guard: orchestrator spinning without calling any subagent.
                    # A healthy orchestrator always calls a subagent within a few passes;
                    # if it hasn't in STALL_LIMIT consecutive passes, it's looping on
                    # tools (ls, read_file, tracker reads) without making progress.
                    if stall_passes >= STALL_LIMIT:
                        warn = (
                            f"Orchestrator has made {stall_passes} consecutive passes "
                            "without delegating to any subagent. "
                            "Stopping to prevent a stalled loop."
                        )
                        await _send(ws, {"type": "error", "content": warn})
                        _persist_message(db, project.id, "error", warn)
                        return

                    # Hard emergency backstop — should never be reached in normal use.
                    if pass_count >= MAX_PASSES:
                        warn = (
                            f"Emergency limit reached ({MAX_PASSES} orchestrator passes). "
                            "Stopping to avoid runaway agent loop."
                        )
                        await _send(ws, {"type": "error", "content": warn})
                        _persist_message(db, project.id, "error", warn)
                        return

                # ── Stop-after-relay: spec-evaluator said NEEDS_CLARIFICATION ──
                # The orchestrator has just relayed the questions. Stop here and
                # wait for the user's next message instead of continuing the loop.
                if stop_after_relay and full_content:
                    logger.info("Stopping after relaying NEEDS_CLARIFICATION questions")
                    return

            # ── Tool result (file writes etc.) ────────────────────────────────
            elif event_name == "on_tool_end":
                tool_name: str = event.get("name", "")
                output_val = event_data.get("output", "")
                if tool_name in ("write_file", "edit_file"):
                    # Extract file path from the tool input
                    tool_input = event_data.get("input", {})
                    fpath = (
                        tool_input.get("path", "")
                        if isinstance(tool_input, dict)
                        else ""
                    )
                    content_val = (
                        tool_input.get("content", "")
                        if isinstance(tool_input, dict)
                        else ""
                    )
                    if fpath:
                        await _send(ws, {
                            "type": "file_delta",
                            "path": fpath,
                            "content": content_val,
                            "op": "write" if tool_name == "write_file" else "edit",
                        })

                # Tracker tool updates
                if tool_name in (
                    "update_epic_status", "update_story_status", "update_task_status"
                ):
                    result_str = str(output_val)
                    # Emit a tracker_update frame so the panel refreshes
                    await _send(ws, {
                        "type": "tracker_update",
                        "tool": tool_name,
                        "result": result_str,
                    })

    finally:
        elapsed = time.monotonic() - run_start
        logger.info(
            "Agent run complete: project=%d passes=%d tokens_in=%d tokens_out=%d elapsed=%.1fs",
            project.id, pass_count, total_input_tokens, total_output_tokens, elapsed,
        )
        await _send(ws, {"type": "done"})


def _estimate_cost(model: str | None, input_tokens: int, output_tokens: int) -> float:
    """Rough USD cost estimate based on model tier.

    Prices per million tokens (approximate, as of 2025-Q1):
      haiku-4-5:  $0.80 in / $4.00 out
      sonnet-4-6: $3.00 in / $15.00 out
      opus-4-6:   $15.00 in / $75.00 out
    """
    m = (model or "").lower()
    if "haiku" in m:
        rate_in, rate_out = 0.80, 4.00
    elif "opus" in m:
        rate_in, rate_out = 15.00, 75.00
    else:  # sonnet default
        rate_in, rate_out = 3.00, 15.00

    return round(
        (input_tokens / 1_000_000) * rate_in + (output_tokens / 1_000_000) * rate_out,
        6,
    )


# ── Ping keepalive task ──────────────────────────────────────────────────────

async def _ping_loop(ws: WebSocket, stop_event: asyncio.Event) -> None:
    """Send a ping frame every PING_INTERVAL seconds until stop_event is set."""
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(
                asyncio.shield(asyncio.sleep(PING_INTERVAL)),
                timeout=PING_INTERVAL + 1,
            )
            await ws.send_text(json.dumps({"type": "ping"}))
        except asyncio.CancelledError:
            break
        except Exception:
            break


# ── Main WebSocket handler ───────────────────────────────────────────────────

@router.websocket("/ws/chat/{project_id}")
async def chat_websocket(ws: WebSocket, project_id: int) -> None:
    """Main WebSocket endpoint. Accepts chat messages and streams agent responses."""
    await ws.accept()

    db = SessionLocal()
    stop_event = _get_stop_event(project_id)
    ping_task: asyncio.Task | None = None

    try:
        project = db.get(Project, project_id)
        if not project:
            await _send(ws, {"type": "error", "content": f"Project {project_id} not found."})
            await ws.close()
            return

        # Start keepalive ping
        ping_task = asyncio.create_task(_ping_loop(ws, stop_event))

        while True:
            try:
                raw = await ws.receive_text()
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected: project %d", project_id)
                break

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON from client: %r", raw[:200])
                continue

            msg_type = data.get("type")

            # ── Stop ─────────────────────────────────────────────────────────
            if msg_type == "stop":
                stop_event.set()
                # Reset for future messages
                _stop_events[project_id] = asyncio.Event()
                continue

            # ── User message ──────────────────────────────────────────────────
            if msg_type == "message":
                user_text = data.get("content", "").strip()
                if not user_text:
                    continue

                # Persist human message
                _persist_message(db, project_id, "human", user_text)

                # Fresh stop event for this run
                run_stop = asyncio.Event()
                _stop_events[project_id] = run_stop

                # Run agent as a concurrent task so the receive loop stays alive.
                # Previously `await _run_agent(...)` blocked the entire coroutine,
                # meaning stop messages from the client arrived but were never read
                # until the agent naturally finished (~6s). Now we use asyncio.wait()
                # to race the agent against incoming WebSocket messages, so a stop
                # signal is processed within one event-loop cycle (<50ms).
                agent_task: asyncio.Task = asyncio.create_task(
                    _run_agent(ws, project, user_text, run_stop, db)
                )

                recv_task: asyncio.Task = asyncio.create_task(ws.receive_text())
                disconnected = False
                while not agent_task.done():
                    done, _ = await asyncio.wait(
                        {agent_task, recv_task},
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    if recv_task in done:
                        try:
                            inner_raw = recv_task.result()
                        except WebSocketDisconnect:
                            run_stop.set()
                            disconnected = True
                            break
                        except Exception:
                            run_stop.set()
                            disconnected = True
                            break

                        try:
                            inner_data = json.loads(inner_raw)
                            if inner_data.get("type") == "stop":
                                run_stop.set()
                        except json.JSONDecodeError:
                            pass

                        # Re-arm receive for the next message
                        if not agent_task.done():
                            recv_task = asyncio.create_task(ws.receive_text())

                # Cancel any pending receive (agent finished before next client message)
                if not recv_task.done():
                    recv_task.cancel()
                    try:
                        await recv_task
                    except (asyncio.CancelledError, Exception):
                        pass

                if disconnected:
                    # Give agent up to 2 s to send its finally/done frame then exit
                    try:
                        await asyncio.wait_for(agent_task, timeout=2.0)
                    except (asyncio.TimeoutError, Exception):
                        pass
                    break

                # Agent task is done — propagate any exception
                try:
                    await agent_task
                except Exception as exc:
                    logger.exception("Agent run error for project %d", project_id)
                    await _send(ws, {"type": "error", "content": str(exc)})
                    await _send(ws, {"type": "done"})

                continue

            # ── Checkpoint response ───────────────────────────────────────────
            if msg_type == "checkpoint_response":
                choice = data.get("choice", "approve")
                feedback = data.get("feedback", "")
                cp_id = data.get("id", "")

                if cp_id.startswith("cp2-"):
                    # Checkpoint 2 — test approval
                    if choice == "approve":
                        synthetic_text = (
                            "CHECKPOINT_2_APPROVED: The user has approved the tests. "
                            "Proceed to Step 4d: delegate to the implementation agent."
                        )
                    else:
                        synthetic_text = (
                            "CHECKPOINT_2_SKIP: The user chose to skip tests. "
                            "Proceed directly to Step 4d: delegate to the implementation agent."
                        )
                else:
                    # Checkpoint 1 — plan approval (default)
                    if choice == "approve":
                        synthetic_text = (
                            "CHECKPOINT_1_APPROVED: The user has approved the plan. "
                            "Acknowledge briefly, then proceed to Step 3 and delegate to architect."
                        )
                    else:
                        synthetic_text = (
                            f"CHECKPOINT_1_FEEDBACK: {feedback}. "
                            "Please revise the plan: call planner again with the original spec plus "
                            "this feedback, then present a new Checkpoint 1."
                        )

                _persist_message(db, project_id, "human", synthetic_text)

                run_stop = asyncio.Event()
                _stop_events[project_id] = run_stop

                agent_task = asyncio.create_task(
                    _run_agent(ws, project, synthetic_text, run_stop, db)
                )
                recv_task: asyncio.Task = asyncio.create_task(ws.receive_text())
                disconnected = False
                while not agent_task.done():
                    done, _ = await asyncio.wait(
                        {agent_task, recv_task},
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    if recv_task in done:
                        try:
                            inner_raw = recv_task.result()
                        except WebSocketDisconnect:
                            run_stop.set()
                            disconnected = True
                            break
                        except Exception:
                            run_stop.set()
                            disconnected = True
                            break
                        try:
                            inner_data = json.loads(inner_raw)
                            if inner_data.get("type") == "stop":
                                run_stop.set()
                        except json.JSONDecodeError:
                            pass
                        if not agent_task.done():
                            recv_task = asyncio.create_task(ws.receive_text())

                if not recv_task.done():
                    recv_task.cancel()
                    try:
                        await recv_task
                    except (asyncio.CancelledError, Exception):
                        pass

                if disconnected:
                    try:
                        await asyncio.wait_for(agent_task, timeout=2.0)
                    except (asyncio.TimeoutError, Exception):
                        pass
                    break

                try:
                    await agent_task
                except Exception as exc:
                    logger.exception("Checkpoint agent error for project %d", project_id)
                    await _send(ws, {"type": "error", "content": str(exc)})
                    await _send(ws, {"type": "done"})
                continue

            # ── HIL response ──────────────────────────────────────────────────
            if msg_type == "hil_response":
                logger.info("HIL response for project %d: %s", project_id, data)
                continue

    except Exception as exc:
        logger.exception("WebSocket outer error for project %d", project_id)
        try:
            await ws.send_text(json.dumps({"type": "error", "content": str(exc)}))
        except Exception:
            pass
    finally:
        if ping_task:
            ping_task.cancel()
        db.close()
