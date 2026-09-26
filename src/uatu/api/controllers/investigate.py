from fastapi import APIRouter, Depends
from pydantic import BaseModel

from uatu.models import Diagnosis
from uatu.prompts import load
from uatu.services import investigate as service
from uatu.services.project import resolve_project

router = APIRouter(
    prefix="/projects/{project_id}/investigate",
    tags=["investigate"],
    dependencies=[Depends(resolve_project)],
)


class InvestigateRequest(BaseModel):
    error: str


@router.post("")
def investigate(req: InvestigateRequest, project_id: str) -> Diagnosis:
    return service.investigate(req.error, project_id)


@router.post("/preview")
def preview(project_id: str, req: InvestigateRequest) -> dict:
    """See exactly what the model will receive. No LLM call."""
    prompt = load("investigate")
    return {
        "prompt_version": prompt.version,
        "system": prompt.system,
        "user": service.build_prompt(req.error, project_id),
    }
