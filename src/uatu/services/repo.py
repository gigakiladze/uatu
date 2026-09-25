from uatu.models import Repo, RepoCreate
from uatu.store import repo as store


def attach(project_id: str, repos: list[RepoCreate]) -> list[Repo]:
    return [store.save(Repo(project_id=project_id, **r.model_dump())) for r in repos]


def get(project_id: str, repo_id: str) -> Repo | None:
    return store.get(project_id, repo_id)


def list_for_project(project_id: str) -> list[Repo]:
    return store.list_for_project(project_id)