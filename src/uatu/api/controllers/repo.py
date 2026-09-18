from fastapi import APIRouter, HTTPException

from uatu.models import Repo
from uatu.services import repo as service

router = APIRouter(prefix="/repos", tags=["repos"])


@router.post("")
def attach(repos: list[Repo]) -> dict:
    return {"saved": service.attach(repos)}


@router.get("")
def list_repos(project: str) -> list[Repo]:
    return service.list_for_project(project)


@router.get("/{owner}/{name}")
def get_repo(owner: str, name: str) -> Repo:
    found = service.get(f"{owner}/{name}")
    if not found:
        raise HTTPException(404, "repo not found")
    return found