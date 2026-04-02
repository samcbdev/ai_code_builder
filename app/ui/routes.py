from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.storage.project_store import ProjectStore

router = APIRouter()
templates = Jinja2Templates(directory="app/ui/templates")
store = ProjectStore()

@router.get("/")
def index(request: Request):
    projects = store.list()
    return templates.TemplateResponse("index.html", {"request": request, "projects": projects})

@router.get("/project/{project_id}")
def get_project(request: Request, project_id: str):
    state = store.load(project_id)
    return templates.TemplateResponse("project.html", {"request": request, "state": state})

@router.post("/project/{project_id}/message")
def send_message(project_id: str, message: str = Form(...)):
    store.enqueue_ui_message(project_id, message)
    return RedirectResponse(f"/project/{project_id}", status_code=303)