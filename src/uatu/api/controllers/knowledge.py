from fastapi import APIRouter, Depends
from pydantic import BaseModel

from uatu.models.knowledge import KnowledgeItemCreate
from uatu.services import knowledge
from uatu.services.project import resolve_project
from uatu.graphs.ingest.graph import graph


router = APIRouter(
    prefix="/projects/{project_id}/knowledge",
    tags=["knowledge"],
    dependencies=[Depends(resolve_project)],
)


class SearchRequest(BaseModel):
    query: str
    limit: int = 5


class DocumentRequest(BaseModel):
    raw_text: str

@router.post("")
def add(project_id: str, items: list[KnowledgeItemCreate]) -> dict:
    return knowledge.ingest(items, project_id=project_id)


@router.get("")
def list_all(project_id: str, limit: int = 50) -> list[dict]:
    return knowledge.list_items(project_id, limit)


@router.post("/search")
def search(project_id: str, req: SearchRequest) -> list[dict]:
    return knowledge.search(req.query, project_id, req.limit)

@router.post("/document")
def add_document(project_id: str, req: DocumentRequest) -> dict:
    result = graph.invoke({"project_id": project_id, "raw_text": req.raw_text})
    return {"saved": result["saved"], "indexed": result["indexed"]}
