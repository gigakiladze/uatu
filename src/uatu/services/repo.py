from uatu.libs.config import settings
from uatu.libs.repository import MongoRepository
from uatu.libs.vector_repository import QdrantRepository



from uatu.models import Repo
from uatu.services import indexer
from uatu.store import repo as store


def attach(repos: list[Repo]) -> dict:
    saved = store.save(repos)

    results = []
    for r in repos:
        try:
            results.append(indexer.index_repo(r.slug))
        except Exception as e:
            results.append({"repo": r.slug, "status": "failed", "error": str(e)})

    return {"saved": saved, "index": results}



def get(slug: str) -> Repo | None:
    return store.get(slug)


def list_for_project(project: str) -> list[Repo]:
    return store.list_for_project(project)