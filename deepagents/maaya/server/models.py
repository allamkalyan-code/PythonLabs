"""SQLAlchemy models for Maaya v2."""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from server.database import Base


def _now() -> datetime:
    """Return current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


class Status(str, enum.Enum):
    """Lifecycle status shared by Epic, Story, and Task."""
    NOT_STARTED = "not_started"
    WIP = "wip"
    DONE = "done"
    BLOCKED = "blocked"


class Priority(str, enum.Enum):
    """Priority level shared by Epic, Story, and Task."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Project(Base):
    """A user project that Maaya is building."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    path = Column(String(1024), nullable=False)
    model = Column(String(100), nullable=False, default="anthropic:claude-sonnet-4-6")
    created_at = Column(DateTime, nullable=False, default=_now)
    updated_at = Column(DateTime, nullable=False, default=_now, onupdate=_now)

    messages = relationship("ChatMessage", back_populates="project", cascade="all, delete-orphan")
    epics = relationship("Epic", back_populates="project", cascade="all, delete-orphan")


class ChatMessage(Base):
    """A single message in a project's chat history."""
    __tablename__ = "chat_messages"

    # Valid roles:
    #   human          — user typed this
    #   ai             — orchestrator or subagent text response
    #   tool           — tool call result (abbreviated)
    #   system         — server-generated status message
    #   task_complete  — token/cost summary frame
    #   error          — error message
    #   checkpoint     — human checkpoint request/response
    #   handoff        — parsed subagent handoff block
    VALID_ROLES = frozenset({
        "human", "ai", "tool", "system",
        "task_complete", "error", "checkpoint", "handoff",
    })

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False, default="")
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=_now)

    project = relationship("Project", back_populates="messages")


class UserMemory(Base):
    """Persistent key-value store for user preferences across projects."""
    __tablename__ = "user_memory"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, nullable=False, default=_now, onupdate=_now)


class Epic(Base):
    """A major feature area, composed of stories."""
    __tablename__ = "epics"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    success_criteria = Column(Text, nullable=True)
    status = Column(SAEnum(Status), nullable=False, default=Status.NOT_STARTED)
    priority = Column(SAEnum(Priority), nullable=False, default=Priority.MEDIUM)
    created_at = Column(DateTime, nullable=False, default=_now)
    updated_at = Column(DateTime, nullable=False, default=_now, onupdate=_now)

    project = relationship("Project", back_populates="epics")
    stories = relationship("Story", back_populates="epic", cascade="all, delete-orphan")


class Story(Base):
    """A user-facing capability within an epic (one layer only per Standard 1)."""
    __tablename__ = "stories"

    id = Column(Integer, primary_key=True, index=True)
    epic_id = Column(Integer, ForeignKey("epics.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    user_story = Column(Text, nullable=True)            # "As a X, I want Y so that Z"
    acceptance_criteria_json = Column(Text, nullable=True)  # JSON list of Gherkin strings
    status = Column(SAEnum(Status), nullable=False, default=Status.NOT_STARTED)
    priority = Column(SAEnum(Priority), nullable=False, default=Priority.MEDIUM)
    story_points = Column(Integer, nullable=True)
    assigned_agent = Column(String(50), nullable=True)
    depends_on_json = Column(Text, nullable=True)       # JSON list of story IDs
    created_at = Column(DateTime, nullable=False, default=_now)
    updated_at = Column(DateTime, nullable=False, default=_now, onupdate=_now)

    epic = relationship("Epic", back_populates="stories")
    tasks = relationship("Task", back_populates="story", cascade="all, delete-orphan")


class Task(Base):
    """A single unit of work within a story (one file, one concern per Standard 1)."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    story_id = Column(Integer, ForeignKey("stories.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SAEnum(Status), nullable=False, default=Status.NOT_STARTED)
    priority = Column(SAEnum(Priority), nullable=False, default=Priority.MEDIUM)
    assigned_agent = Column(String(50), nullable=True)
    file_path = Column(String(1024), nullable=True)     # exact file to create/edit
    input_output_types = Column(Text, nullable=True)    # param + return types
    notes = Column(Text, nullable=True)
    parallel_group = Column(Integer, nullable=True)     # stories with same group run concurrently
    depends_on_json = Column(Text, nullable=True)       # JSON list of task IDs
    changed_files_json = Column(Text, nullable=True)    # FILES_CREATED + FILES_MODIFIED from handoff
    dod_checklist_json = Column(Text, nullable=True)    # DoD verification result
    created_at = Column(DateTime, nullable=False, default=_now)
    updated_at = Column(DateTime, nullable=False, default=_now, onupdate=_now)

    story = relationship("Story", back_populates="tasks")
