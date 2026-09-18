from uatu.libs.config import settings
from uatu.libs.repository import MongoRepository
from uatu.libs.vector_repository import QdrantRepository
from uatu.models import CodeFile

COLLECTION = "code_files"

docs = MongoRepository(COLLECTION, CodeFile)
vectors = QdrantRepository(
    COLLECTION,
    CodeFile,
    vector_size=settings.embedding_dim,
    indexed_fields=("project", "repo", "path", "language"),
)


def ensure_indexes() -> None:
    docs.col.create_index([("project", 1), ("repo", 1)])
    docs.col.create_index([("repo", 1), ("path", 1)])


def ensure_collection() -> None:
    vectors.ensure_collection()


def save(files: list[CodeFile]) -> int:
    return docs.upsert_many({f.doc_id: f for f in files})


def index(files: list[CodeFile], vecs: list[list[float]]) -> int:
    return vectors.upsert({str(f.point_id): (v, f) for f, v in zip(files, vecs)})


def search_vector(
    vector: list[float], project: str | None = None,
    repo: str | None = None, limit: int = 5,
) -> list[tuple[float, CodeFile]]:
    where = {k: v for k, v in (("project", project), ("repo", repo)) if v}
    return vectors.search(vector, where or None, limit)