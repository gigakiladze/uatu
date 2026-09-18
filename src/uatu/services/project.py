from fastapi import HTTPException

from uatu.libs.error_message import ErrorMessage
from uatu.models.project import Project
from uatu.store.project import project_store

def getProjectByName(name: str) -> Project | None:
    projects = project_store.find({"name": name})
    return projects[0] if projects else None

def create_project(project: Project) -> Project:
    return project_store.insert(project)

def resolve_project(project_id: str) -> Project:
    project = project_store.get(project_id)
    if not project:
        raise HTTPException(404, ErrorMessage.PROJECT_NOT_FOUND)
    return project
