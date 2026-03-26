"""CRUD endpoints for Epics, Stories, and Tasks."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from server.database import get_db
from server.models import Epic, Priority, Status, Story, Task

router = APIRouter(prefix="/api/tracker", tags=["tracker"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class EpicCreate(BaseModel):
    title: str
    description: str | None = None
    priority: Priority = Priority.MEDIUM
    project_id: int | None = None


class EpicUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: Status | None = None
    priority: Priority | None = None


class StoryCreate(BaseModel):
    epic_id: int
    title: str
    description: str | None = None
    priority: Priority = Priority.MEDIUM
    story_points: int | None = None


class StoryUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: Status | None = None
    priority: Priority | None = None
    story_points: int | None = None


class TaskCreate(BaseModel):
    story_id: int
    title: str
    description: str | None = None
    priority: Priority = Priority.MEDIUM
    assigned_agent: str | None = None
    notes: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: Status | None = None
    priority: Priority | None = None
    assigned_agent: str | None = None
    notes: str | None = None


# ── Epics ─────────────────────────────────────────────────────────────────────

@router.get("/epics")
def list_epics(project_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Epic)
    if project_id is not None:
        query = query.filter(Epic.project_id == project_id)
    epics = query.order_by(Epic.id).all()
    result = []
    for epic in epics:
        stories = []
        for story in epic.stories:
            stories.append({
                "id": story.id,
                "epic_id": story.epic_id,
                "title": story.title,
                "description": story.description,
                "status": story.status,
                "priority": story.priority,
                "story_points": story.story_points,
                "tasks": [
                    {
                        "id": t.id,
                        "story_id": t.story_id,
                        "title": t.title,
                        "description": t.description,
                        "status": t.status,
                        "priority": t.priority,
                        "assigned_agent": t.assigned_agent,
                        "notes": t.notes,
                        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                    }
                    for t in story.tasks
                ],
            })
        result.append({
            "id": epic.id,
            "title": epic.title,
            "description": epic.description,
            "status": epic.status,
            "priority": epic.priority,
            "updated_at": epic.updated_at.isoformat() if epic.updated_at else None,
            "stories": stories,
        })
    return result


@router.post("/epics", status_code=201)
def create_epic(body: EpicCreate, db: Session = Depends(get_db)):
    epic = Epic(**body.model_dump())
    db.add(epic)
    db.commit()
    db.refresh(epic)
    return {"id": epic.id, "title": epic.title}


@router.patch("/epics/{epic_id}")
def update_epic(epic_id: int, body: EpicUpdate, db: Session = Depends(get_db)):
    epic = db.get(Epic, epic_id)
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(epic, field, value)
    db.commit()
    return {"ok": True}


@router.delete("/epics/{epic_id}", status_code=204)
def delete_epic(epic_id: int, db: Session = Depends(get_db)):
    epic = db.get(Epic, epic_id)
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")
    db.delete(epic)
    db.commit()


# ── Stories ───────────────────────────────────────────────────────────────────

@router.post("/stories", status_code=201)
def create_story(body: StoryCreate, db: Session = Depends(get_db)):
    story = Story(**body.model_dump())
    db.add(story)
    db.commit()
    db.refresh(story)
    return {"id": story.id, "title": story.title}


@router.patch("/stories/{story_id}")
def update_story(story_id: int, body: StoryUpdate, db: Session = Depends(get_db)):
    story = db.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(story, field, value)
    db.commit()
    return {"ok": True}


@router.delete("/stories/{story_id}", status_code=204)
def delete_story(story_id: int, db: Session = Depends(get_db)):
    story = db.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    db.delete(story)
    db.commit()


# ── Tasks ─────────────────────────────────────────────────────────────────────

@router.post("/tasks", status_code=201)
def create_task(body: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**body.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return {"id": task.id, "title": task.title}


@router.patch("/tasks/{task_id}")
def update_task(task_id: int, body: TaskUpdate, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(task, field, value)
    db.commit()
    return {"ok": True}


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
