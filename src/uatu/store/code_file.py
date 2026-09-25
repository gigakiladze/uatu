from uatu.libs.config import settings
from uatu.libs.repository import MongoRepository
from uatu.libs.vector_repository import QdrantRepository
from uatu.models.code_file import CodeFile, CodePoint, FileSummary

COLLECTION = "code_files"

docs = MongoRepository(COLLECTION, CodeFile)
vectors = QdrantRepository(
    COLLECTION,
    CodePoint,
    vector_size=settings.embedding_dim,
    indexed_fields=("project_id", "repo_id", "path", "commit_sha", "kind"),
)


def ensure_indexes() -> None:
    docs.col.create_index([("project_id", 1), ("repo", 1)])
    docs.col.create_index([("project_id", 1), ("blob_sha", 1)])


def ensure_collection() -> None:
    vectors.ensure_collection()


# ---------- write ----------

def save(files: list[CodeFile]) -> int:
    return docs.upsert_many({f.doc_id: f for f in files})


def index(points: list[CodePoint], vecs: list[list[float]]) -> int:
    return vectors.upsert({p.point_id: (v, p) for p, v in zip(points, vecs)})


def sweep(project_id: str, repo_id: str, commit_sha: str) -> int:
    vectors.delete_where(
        {"project_id": project_id, "repo_id": repo_id},
        {"commit_sha": commit_sha},
    )
    return docs.col.delete_many(
        {"project_id": project_id, "repo_id": repo_id,
         "commit_sha": {"$ne": commit_sha}}
    ).deleted_count


# ---------- read ----------

def summaries_by_blob(
    project_id: str, blob_shas: list[str], prompt_version: int
) -> dict[str, FileSummary]:
    """blob_sha -> existing summary. These files can skip the LLM."""
    cursor = docs.col.find(
        {
            "project_id": project_id,
            "blob_sha": {"$in": blob_shas},
            "prompt_version": prompt_version,
            "summary": {"$ne": None},
        },
        {"blob_sha": 1, "summary": 1},
    )
    return {d["blob_sha"]: FileSummary(**d["summary"]) for d in cursor}


def search_vector(
    vector: list[float],
    project_id: str | None = None,
    repo_id: str | None = None,
    limit: int = 5,
) -> list[tuple[float, CodePoint]]:
    where = {k: v for k, v in (("project_id", project_id), ("repo_id", repo_id)) if v}
    return vectors.search(vector, where or None, limit)