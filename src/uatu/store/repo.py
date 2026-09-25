from bson import ObjectId

from uatu.libs.repository import MongoRepository
from uatu.models import Repo

docs = MongoRepository("repos", Repo)


def ensure_indexes() -> None:
    docs.col.create_index(
        [("project_id", 1), ("owner", 1), ("name", 1)], unique=True
    )


def save(repo: Repo) -> Repo | None:
    """Idempotent: re-attaching the same repo updates it. Returns the stored row."""
    where = {"project_id": repo.project_id, "owner": repo.owner, "name": repo.name}
    docs.upsert_by(where, repo)
    return docs.find_one(where)


def get(project_id: str, repo_id: str) -> Repo | None:
    """Scoped lookup — a repo id belonging to another project is invisible."""
    if not ObjectId.is_valid(repo_id):
        return None
    return docs.find_one({"_id": ObjectId(repo_id), "project_id": project_id})


def list_for_project(project_id: str) -> list[Repo]:
    return docs.find({"project_id": project_id})


def set_indexed_sha(repo_id: str, sha: str) -> None:
    docs.col.update_one(
        {"_id": ObjectId(repo_id)}, {"$set": {"last_indexed_sha": sha}}
    )
