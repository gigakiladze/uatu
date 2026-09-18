from fastapi import APIRouter
from pydantic import BaseModel

from uatu.models import Diagnosis
from uatu.services import investigate as service

router = APIRouter(prefix="/investigate", tags=["investigate"])


class InvestigateRequest(BaseModel):
    error: str
    project: str


@router.post("")
def investigate(req: InvestigateRequest) -> Diagnosis:
    return service.investigate(req.error, req.project)


@router.post("/preview")
def preview(req: InvestigateRequest) -> dict:
    """See exactly what the model will receive. No LLM call."""
    return {"prompt": service.build_prompt(req.error, req.project)}