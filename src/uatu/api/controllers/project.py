from fastapi import APIRouter, HTTPException
from uatu.libs.error_message import ErrorMessage

from uatu.models.project import Project
from uatu.services.project import getProjectByName

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/")
def create_project(project: Project) -> dict:
    isProjectExists = getProjectByName(project.name)
    if isProjectExists:
        raise HTTPException(status_code=400, detail=ErrorMessage.PROJECT_ALREADY_EXISTS)
    from uatu.services import project as service
    return {"saved": service.create_project(project)}