from fastapi import APIRouter, Depends, HTTPException

from uatu.graphs.index.graph import graph
from uatu.models import Repo, RepoCreate
from uatu.services import repo as service
from uatu.services.project import resolve_project


router = APIRouter(
    prefix="/projects/{project_id}/repos",
    tags=["repos"],
    dependencies=[Depends(resolve_project)],
)


@router.post("")
def attach(project_id: str, repos: list[RepoCreate]) -> list[Repo]:
    return service.attach(project_id, repos)


@router.get("")
def list_repos(project_id: str) -> list[Repo]:
    return service.list_for_project(project_id)


@router.get("/{repo_id}")
def get_repo(project_id: str, repo_id: str) -> Repo:
    found = service.get(project_id, repo_id)
    if not found:
        raise HTTPException(404, "repo not found")
    return found


@router.post("/{repo_id}/index")
def index(project_id: str, repo_id: str) -> dict:
    state = graph.invoke(
        {"project_id": project_id, "repo_id": repo_id},
        config={"max_concurrency": 5},
    )
    return state["result"]