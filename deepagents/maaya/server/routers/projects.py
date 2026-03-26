"""Project CRUD, tracker read, and session-reset endpoints."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.database import get_db
from server.models import ChatMessage, Epic, Project, Story, Task
from server.schemas import (
    EpicResponse,
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
    ChatMessageResponse,
    TrackerResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/projects", tags=["projects"])


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------

@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    """Create a new project."""
    project = Project(name=body.name, path=body.path, model=body.model)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    """Return all projects ordered by most recently updated."""
    return db.query(Project).order_by(Project.updated_at.desc()).all()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)) -> Project:
    """Return a single project by ID."""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found", headers={"code": "PROJECT_NOT_FOUND"})
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, body: ProjectUpdate, db: Session = Depends(get_db)) -> Project:
    """Update project name or model."""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found", headers={"code": "PROJECT_NOT_FOUND"})
    if body.name is not None:
        project.name = body.name
    if body.model is not None:
        project.model = body.model
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a project and all its data. Also clears the in-memory LangGraph checkpointer."""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found", headers={"code": "PROJECT_NOT_FOUND"})
    db.delete(project)
    db.commit()
    # Clear in-memory session so no stale state remains
    _clear_session(project_id)


# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------

@router.get("/{project_id}/messages", response_model=list[ChatMessageResponse])
def get_messages(project_id: int, db: Session = Depends(get_db)) -> list[ChatMessage]:
    """Return chat history for a project, oldest first."""
    if not db.get(Project, project_id):
        raise HTTPException(status_code=404, detail="Project not found", headers={"code": "PROJECT_NOT_FOUND"})
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.project_id == project_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


@router.post("/{project_id}/reset-session", status_code=204)
def reset_session(project_id: int, db: Session = Depends(get_db)) -> None:
    """Clear chat history and the in-memory LangGraph checkpointer for this project.

    Tracker data (epics/stories/tasks) is NOT cleared — it persists across sessions.
    """
    if not db.get(Project, project_id):
        raise HTTPException(status_code=404, detail="Project not found", headers={"code": "PROJECT_NOT_FOUND"})
    db.query(ChatMessage).filter(ChatMessage.project_id == project_id).delete()
    db.commit()
    _clear_session(project_id)


# ---------------------------------------------------------------------------
# Tracker read endpoints
# ---------------------------------------------------------------------------

@router.get("/{project_id}/tracker", response_model=TrackerResponse)
def get_tracker(project_id: int, db: Session = Depends(get_db)) -> dict:
    """Return the full epic → story → task tree for a project."""
    if not db.get(Project, project_id):
        raise HTTPException(status_code=404, detail="Project not found", headers={"code": "PROJECT_NOT_FOUND"})
    epics = (
        db.query(Epic)
        .filter(Epic.project_id == project_id)
        .order_by(Epic.created_at.asc())
        .all()
    )
    return {"project_id": project_id, "epics": epics}


@router.get("/{project_id}/tracker/epics", response_model=list[EpicResponse])
def list_epics(project_id: int, db: Session = Depends(get_db)) -> list[Epic]:
    """Return all epics for a project with their stories."""
    if not db.get(Project, project_id):
        raise HTTPException(status_code=404, detail="Project not found", headers={"code": "PROJECT_NOT_FOUND"})
    return db.query(Epic).filter(Epic.project_id == project_id).order_by(Epic.created_at.asc()).all()


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _clear_session(project_id: int) -> None:
    """Remove the in-memory LangGraph checkpointer for this project.

    Imported lazily to avoid circular imports at module load time.
    """
    try:
        from server.routers.agent import clear_project_session
        clear_project_session(project_id)
    except Exception:
        # Agent module may not be loaded yet during startup
        pass
