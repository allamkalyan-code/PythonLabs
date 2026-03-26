"""Pydantic request and response schemas (kept separate per Standard 2.4)."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field, field_validator

from server.models import Priority, Status


# ---------------------------------------------------------------------------
# Project schemas
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    """Request body for creating a new project."""
    name: str
    path: str
    model: str = "anthropic:claude-sonnet-4-6"


class ProjectUpdate(BaseModel):
    """Request body for updating a project (all fields optional)."""
    name: str | None = None
    model: str | None = None


class ProjectResponse(BaseModel):
    """Response schema for a project. Excludes internal fields."""
    id: int
    name: str
    path: str
    model: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Chat message schemas
# ---------------------------------------------------------------------------

class ChatMessageResponse(BaseModel):
    """Response schema for a single chat message."""
    id: int
    project_id: int
    role: str
    content: str
    # Read from metadata_json column (avoids conflict with SQLAlchemy's MetaData attribute)
    metadata: dict[str, Any] | None = Field(None, validation_alias="metadata_json")
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}

    @field_validator("metadata", mode="before")
    @classmethod
    def parse_metadata(cls, value: Any) -> dict[str, Any] | None:
        """Deserialize metadata_json string to dict."""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return None
        if value is None or isinstance(value, dict):
            return value
        return None  # discard any non-dict (e.g. SQLAlchemy MetaData object)


# ---------------------------------------------------------------------------
# Tracker schemas
# ---------------------------------------------------------------------------

class TaskResponse(BaseModel):
    """Response schema for a task."""
    id: int
    story_id: int
    title: str
    description: str | None
    status: Status
    priority: Priority
    assigned_agent: str | None
    file_path: str | None
    input_output_types: str | None
    notes: str | None
    parallel_group: int | None
    depends_on: list[int] = []
    changed_files: list[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("depends_on", mode="before")
    @classmethod
    def parse_depends_on(cls, value: Any) -> list[int]:
        """Deserialize depends_on_json."""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return []
        return value or []

    @field_validator("changed_files", mode="before")
    @classmethod
    def parse_changed_files(cls, value: Any) -> list[str]:
        """Deserialize changed_files_json."""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return []
        return value or []


class StoryResponse(BaseModel):
    """Response schema for a story, including its tasks."""
    id: int
    epic_id: int
    title: str
    user_story: str | None
    acceptance_criteria: list[str] = []
    status: Status
    priority: Priority
    story_points: int | None
    assigned_agent: str | None
    depends_on: list[int] = []
    tasks: list[TaskResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("acceptance_criteria", mode="before")
    @classmethod
    def parse_acceptance_criteria(cls, value: Any) -> list[str]:
        """Deserialize acceptance_criteria_json."""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return []
        return value or []

    @field_validator("depends_on", mode="before")
    @classmethod
    def parse_depends_on(cls, value: Any) -> list[int]:
        """Deserialize depends_on_json."""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return []
        return value or []


class EpicResponse(BaseModel):
    """Response schema for an epic, including its stories and tasks."""
    id: int
    project_id: int
    title: str
    description: str | None
    success_criteria: str | None
    status: Status
    priority: Priority
    stories: list[StoryResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TrackerResponse(BaseModel):
    """Full tracker tree for a project."""
    project_id: int
    epics: list[EpicResponse] = []
