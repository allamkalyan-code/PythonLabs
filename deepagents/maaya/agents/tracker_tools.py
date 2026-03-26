"""LangChain tools for interacting with the Maaya task tracker (Epic/Story/Task).

All tools operate on the project set via `set_current_project()`.
Each tool creates its own DB session to be safe for concurrent subagent use.
"""

import json
import logging
from typing import Optional

from langchain_core.tools import tool
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Set before each agent run by the server
_current_project_id: int | None = None


def set_current_project(project_id: int) -> None:
    """Bind all tracker tools to a specific project."""
    global _current_project_id
    _current_project_id = project_id


def _get_project_id() -> int:
    """Return the current project ID or raise if not set."""
    if _current_project_id is None:
        raise RuntimeError("No project set — call set_current_project() before using tracker tools.")
    return _current_project_id


def _db() -> Session:
    """Open a new DB session. Caller must close it."""
    from server.database import SessionLocal
    return SessionLocal()


# ---------------------------------------------------------------------------
# Epic tools
# ---------------------------------------------------------------------------

@tool
def create_epic(title: str, description: str, priority: str = "medium", success_criteria: str = "") -> str:
    """Create a new Epic in the task tracker.

    An Epic is a major feature area (2-6 stories). Use Standard 1 format.

    Args:
        title: Short epic title, e.g. 'User Authentication'.
        description: What this area does and why it exists.
        priority: One of 'low', 'medium', 'high', 'critical'.
        success_criteria: Observable definition of done for the entire epic.

    Returns:
        Confirmation with the new epic ID.
    """
    from server.models import Epic, Priority
    db = _db()
    try:
        epic = Epic(
            project_id=_get_project_id(),
            title=title,
            description=description,
            success_criteria=success_criteria or None,
            priority=Priority(priority.lower()),
        )
        db.add(epic)
        db.commit()
        db.refresh(epic)
        return f"Epic created: id={epic.id} title='{epic.title}'"
    except Exception as exc:
        logger.exception("create_epic failed")
        return f"Error creating epic: {exc}"
    finally:
        db.close()


@tool
def update_epic_status(epic_id: int, status: str) -> str:
    """Update the status of an Epic.

    Args:
        epic_id: ID of the epic to update.
        status: One of 'not_started', 'wip', 'done', 'blocked'.

    Returns:
        Confirmation or error message.
    """
    from server.models import Epic, Status
    db = _db()
    try:
        epic = db.get(Epic, epic_id)
        if not epic:
            return f"Error: Epic {epic_id} not found."
        epic.status = Status(status.lower())
        db.commit()
        return f"Epic {epic_id} status → {status}"
    except Exception as exc:
        return f"Error updating epic: {exc}"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Story tools
# ---------------------------------------------------------------------------

@tool
def create_story(
    epic_id: int,
    title: str,
    user_story: str,
    acceptance_criteria: list[str],
    assigned_agent: str,
    priority: str = "medium",
    story_points: int = 2,
    depends_on: Optional[list[int]] = None,
) -> str:
    """Create a new Story under an Epic.

    A Story is a user-facing capability (one layer only — never cross frontend and backend).
    Use Standard 1 format: user story + Gherkin acceptance criteria.

    Args:
        epic_id: ID of the parent epic.
        title: Action-subject title, e.g. 'Create user registration POST endpoint'.
        user_story: 'As a [user], I want [action] so that [outcome].'
        acceptance_criteria: List of Gherkin 'Given/When/Then' strings (min 3: happy path, error, integration).
        assigned_agent: One of: planner, architect, frontend, backend, database, devops, tester.
        priority: One of 'low', 'medium', 'high', 'critical'.
        story_points: 1 (trivial) | 2 (small) | 3 (medium) | 5 (large — split it).
        depends_on: List of story IDs that must complete first.

    Returns:
        Confirmation with the new story ID.
    """
    from server.models import Story, Priority
    db = _db()
    try:
        story = Story(
            epic_id=epic_id,
            title=title,
            user_story=user_story,
            acceptance_criteria_json=json.dumps(acceptance_criteria),
            assigned_agent=assigned_agent,
            priority=Priority(priority.lower()),
            story_points=story_points,
            depends_on_json=json.dumps(depends_on or []),
        )
        db.add(story)
        db.commit()
        db.refresh(story)
        return f"Story created: id={story.id} title='{story.title}' epic={epic_id}"
    except Exception as exc:
        logger.exception("create_story failed")
        return f"Error creating story: {exc}"
    finally:
        db.close()


@tool
def update_story_status(story_id: int, status: str) -> str:
    """Update the status of a Story.

    Args:
        story_id: ID of the story to update.
        status: One of 'not_started', 'wip', 'done', 'blocked'.

    Returns:
        Confirmation or error message.
    """
    from server.models import Story, Status
    db = _db()
    try:
        story = db.get(Story, story_id)
        if not story:
            return f"Error: Story {story_id} not found."
        story.status = Status(status.lower())
        db.commit()
        return f"Story {story_id} status → {status}"
    except Exception as exc:
        return f"Error updating story: {exc}"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Task tools
# ---------------------------------------------------------------------------

@tool
def create_task(
    story_id: int,
    title: str,
    description: str,
    assigned_agent: str,
    file_path: str = "",
    input_output_types: str = "",
    priority: str = "medium",
    parallel_group: Optional[int] = None,
    depends_on: Optional[list[int]] = None,
) -> str:
    """Create a new Task under a Story.

    A Task is a single unit of work: one file, one function, one concern.
    The description must be self-contained (Standard 5): include exact file path,
    function/class names, input types, output types, and the pattern to follow.

    Args:
        story_id: ID of the parent story.
        title: Verb-noun title, e.g. 'Create UserCreate Pydantic request schema'.
        description: Self-contained description with file path, names, I/O types, pattern.
        assigned_agent: One of: frontend, backend, database, devops, tester.
        file_path: Exact file to create or edit (relative to project root).
        input_output_types: Parameter and return types the agent must implement.
        priority: One of 'low', 'medium', 'high', 'critical'.
        parallel_group: Tasks in the same group run concurrently. Use integers (1, 2, ...).
        depends_on: List of task IDs that must complete first.

    Returns:
        Confirmation with the new task ID.
    """
    from server.models import Task, Priority
    db = _db()
    try:
        task = Task(
            story_id=story_id,
            title=title,
            description=description,
            assigned_agent=assigned_agent,
            file_path=file_path or None,
            input_output_types=input_output_types or None,
            priority=Priority(priority.lower()),
            parallel_group=parallel_group,
            depends_on_json=json.dumps(depends_on or []),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return f"Task created: id={task.id} title='{task.title}' story={story_id}"
    except Exception as exc:
        logger.exception("create_task failed")
        return f"Error creating task: {exc}"
    finally:
        db.close()


@tool
def update_task_status(task_id: int, status: str, notes: str = "") -> str:
    """Update the status of a Task. Call this ONLY after verifying the DoD checklist.

    Args:
        task_id: ID of the task to update.
        status: One of 'not_started', 'wip', 'done', 'blocked'.
        notes: Optional notes about what was done or what is blocking.

    Returns:
        Confirmation or error message.
    """
    from server.models import Task, Status
    db = _db()
    try:
        task = db.get(Task, task_id)
        if not task:
            return f"Error: Task {task_id} not found."
        task.status = Status(status.lower())
        if notes:
            task.notes = notes
        db.commit()
        return f"Task {task_id} status → {status}" + (f" | notes: {notes}" if notes else "")
    except Exception as exc:
        return f"Error updating task: {exc}"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Query tools
# ---------------------------------------------------------------------------

@tool
def get_tracker_summary() -> str:
    """Get a summary of all epics, stories, and tasks with their statuses.

    Returns:
        Formatted text summary of the entire tracker for the current project.
    """
    from server.models import Epic
    db = _db()
    try:
        epics = (
            db.query(Epic)
            .filter(Epic.project_id == _get_project_id())
            .order_by(Epic.created_at)
            .all()
        )
        if not epics:
            return "No epics yet."

        lines: list[str] = []
        for epic in epics:
            lines.append(f"Epic {epic.id}: [{epic.status.value}] {epic.title}")
            for story in epic.stories:
                lines.append(f"  Story {story.id}: [{story.status.value}] {story.title} ({story.story_points}pts)")
                for task in story.tasks:
                    lines.append(f"    Task {task.id}: [{task.status.value}] {task.title} → {task.assigned_agent}")
        return "\n".join(lines)
    except Exception as exc:
        return f"Error fetching tracker: {exc}"
    finally:
        db.close()


@tool
def get_next_task() -> str:
    """Get the next NOT_STARTED task to work on, ordered by epic/story/task priority.

    Returns:
        Task details or a message if all tasks are complete.
    """
    from server.models import Epic, Story, Task, Status
    db = _db()
    try:
        task = (
            db.query(Task)
            .join(Story, Task.story_id == Story.id)
            .join(Epic, Story.epic_id == Epic.id)
            .filter(
                Epic.project_id == _get_project_id(),
                Task.status == Status.NOT_STARTED,
            )
            .order_by(Epic.id, Story.id, Task.id)
            .first()
        )
        if not task:
            return "All tasks are complete or in progress."
        story = db.get(Story, task.story_id)
        return (
            f"Task {task.id}: {task.title}\n"
            f"Story: {story.title if story else '?'}\n"
            f"Agent: {task.assigned_agent}\n"
            f"File: {task.file_path or 'TBD'}\n"
            f"Description: {task.description or ''}"
        )
    except Exception as exc:
        return f"Error fetching next task: {exc}"
    finally:
        db.close()


@tool
def get_story_changed_files(story_id: int) -> str:
    """Get all files created or modified by tasks in a given story.

    Useful for passing context to the next agent: 'here are the files the previous agent produced'.

    Args:
        story_id: ID of the story to query.

    Returns:
        Comma-separated list of file paths, or a message if none recorded.
    """
    from server.models import Task
    db = _db()
    try:
        tasks = db.query(Task).filter(Task.story_id == story_id).all()
        files: list[str] = []
        for task in tasks:
            if task.changed_files_json:
                try:
                    files.extend(json.loads(task.changed_files_json))
                except (json.JSONDecodeError, ValueError):
                    pass
        if not files:
            return f"No changed files recorded for story {story_id}."
        unique = list(dict.fromkeys(files))  # deduplicate while preserving order
        return ", ".join(unique)
    except Exception as exc:
        return f"Error: {exc}"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# User memory tools
# ---------------------------------------------------------------------------

@tool
def save_user_preference(key: str, value: str) -> str:
    """Save a user preference that persists across all projects and sessions.

    Use this to remember things like preferred tech stack, coding style, or workflow choices.

    Args:
        key: Short descriptive key, e.g. 'preferred_database', 'test_framework'.
        value: The preference value.

    Returns:
        Confirmation message.
    """
    from server.models import UserMemory
    db = _db()
    try:
        existing = db.query(UserMemory).filter(UserMemory.key == key).first()
        if existing:
            existing.value = value
        else:
            db.add(UserMemory(key=key, value=value))
        db.commit()
        return f"Preference saved: {key} = {value}"
    except Exception as exc:
        return f"Error saving preference: {exc}"
    finally:
        db.close()


@tool
def get_user_preferences() -> str:
    """Load all saved user preferences.

    Returns:
        Formatted key-value list, or a message if no preferences are saved.
    """
    from server.models import UserMemory
    db = _db()
    try:
        prefs = db.query(UserMemory).order_by(UserMemory.key).all()
        if not prefs:
            return "No user preferences saved yet."
        return "\n".join(f"{p.key}: {p.value}" for p in prefs)
    except Exception as exc:
        return f"Error loading preferences: {exc}"
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Exported list of all tracker tools
# ---------------------------------------------------------------------------

ALL_TRACKER_TOOLS = [
    create_epic,
    update_epic_status,
    create_story,
    update_story_status,
    create_task,
    update_task_status,
    get_tracker_summary,
    get_next_task,
    get_story_changed_files,
    save_user_preference,
    get_user_preferences,
]
