from fastapi import APIRouter, Depends
from pydantic import BaseModel

from uatu.models.knowledge import KnowledgeItemCreate
from uatu.services import knowledge
from uatu.services.project import resolve_project

router = APIRouter(
    prefix="/projects/{project_id}/knowledge",
    tags=["knowledge"],
    dependencies=[Depends(resolve_project)],
)


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


@router.post("")
def add(project_id: str, items: list[KnowledgeItemCreate]) -> dict:
    return knowledge.ingest(items, project_id=project_id)


@router.get("")
def list_all(project_id: str, limit: int = 50) -> list[dict]:
    return knowledge.list_items(project_id, limit)


@router.post("/search")
def search(project_id: str, req: SearchRequest) -> list[dict]:
    return knowledge.search(req.query, project_id, req.limit)
