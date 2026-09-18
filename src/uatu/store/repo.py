from uatu.libs.repository import MongoRepository
from uatu.models import Repo

docs = MongoRepository("repos", Repo)


def ensure_indexes() -> None:
    docs.col.create_index([("project", 1)])


def save(repos: list[Repo]) -> int:
    return docs.upsert_many({r.slug: r for r in repos})


def get(slug: str) -> Repo | None:
    return docs.get(slug)


def list_for_project(project: str) -> list[Repo]:
    return docs.find({"project": project})


def set_indexed_sha(slug: str, sha: str) -> None:
    docs.col.update_one({"_id": slug}, {"$set": {"last_indexed_sha": sha}})