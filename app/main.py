from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel, Field
from threading import Lock
from uuid import uuid4

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


# --- Data models ---
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: Optional[str] = None
    status: str = Field(default="backlog", pattern="^(backlog|in_progress|done)$")
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# --- Repository (in-memory, thread-safe). Swap later for DB ---
class TaskRepository:
    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}
        self._lock = Lock()

    def list_all(self) -> List[Task]:
        with self._lock:
            return list(self._tasks.values())

    def list_by_status(self, status: str) -> List[Task]:
        with self._lock:
            return [t for t in self._tasks.values() if t.status == status]

    def create(self, data: TaskCreate) -> Task:
        task = Task(title=data.title, description=data.description, priority=data.priority)
        with self._lock:
            self._tasks[task.id] = task
        return task

    def get(self, task_id: str) -> Optional[Task]:
        with self._lock:
            return self._tasks.get(task_id)

    def update_status(self, task_id: str, status: str) -> Optional[Task]:
        if status not in {"backlog", "in_progress", "done"}:
            return None
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            task.status = status
            task.updated_at = datetime.utcnow()
            self._tasks[task_id] = task
            return task


repo = TaskRepository()

# --- FastAPI app ---
app = FastAPI(title="Tasker", version="0.1.0")

# Static and templates
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# Helpers
STATUSES = [
    ("backlog", "Backlog"),
    ("in_progress", "In Progress"),
    ("done", "Done"),
]


def group_tasks() -> Dict[str, List[Task]]:
    return {key: repo.list_by_status(key) for key, _ in STATUSES}


# Routes - HTML views
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    context = {
        "request": request,
        "statuses": STATUSES,
        "tasks": group_tasks(),
    }
    return templates.TemplateResponse("index.html", context)


@app.post("/tasks", response_class=HTMLResponse)
async def create_task_html(
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    priority: str = Form("medium"),
):
    repo.create(TaskCreate(title=title, description=description, priority=priority))
    # Re-render the board for simplicity
    context = {
        "request": request,
        "statuses": STATUSES,
        "tasks": group_tasks(),
    }
    return templates.TemplateResponse("partials/board.html", context)


@app.patch("/tasks/{task_id}/status", response_class=HTMLResponse)
async def move_task_html(request: Request, task_id: str, status: str = Form(...)):
    task = repo.update_status(task_id, status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or invalid status")
    context = {
        "request": request,
        "statuses": STATUSES,
        "tasks": group_tasks(),
    }
    return templates.TemplateResponse("partials/board.html", context)


@app.get("/tasks/{task_id}/analysis", response_class=HTMLResponse)
async def analyze_task_html(request: Request, task_id: str):
    task = repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # Placeholder for future LLM analysis
    insights = {
        "summary": "LLM analysis placeholder: will generate TODO steps and categorization.",
        "suggested_todos": [
            "Clarify requirements",
            "Identify dependencies",
            "Break down into actionable steps",
        ],
        "category": "general",
    }
    return templates.TemplateResponse(
        "partials/analysis.html",
        {"request": request, "task": task, "insights": insights},
    )


# Routes - JSON API (for future FE/BE split)
@app.get("/api/tasks", response_model=List[Task])
async def list_tasks_api():
    return repo.list_all()


@app.post("/api/tasks", response_model=Task)
async def create_task_api(payload: TaskCreate):
    return repo.create(payload)


@app.patch("/api/tasks/{task_id}/status", response_model=Task)
async def move_task_api(task_id: str, status: str):
    task = repo.update_status(task_id, status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or invalid status")
    return task


@app.get("/healthz")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})
