from uatu.libs.config import settings
from uatu.libs.repository import MongoRepository
from uatu.libs.vector_repository import QdrantRepository
from uatu.models import KnowledgeItem

COLLECTION = "knowledge"

docs = MongoRepository(COLLECTION, KnowledgeItem)
vectors = QdrantRepository(
    COLLECTION,
    KnowledgeItem,
    vector_size=settings.embedding_dim,
    indexed_fields=("project_id", "label"),
)


# ---------- schema setup (idempotent, runs at startup) ----------

def ensure_indexes() -> None:
    docs.col.create_index([("project_id", 1), ("label", 1)])


def ensure_collection() -> None:
    vectors.ensure_collection()


# ---------- write ----------

def save_raw(items: list[KnowledgeItem]) -> int:
    return docs.upsert_many({str(i.point_id): i for i in items})


def index(items: list[KnowledgeItem], vecs: list[list[float]]) -> int:
    return vectors.upsert({str(i.point_id): (v, i) for i, v in zip(items, vecs)})


# ---------- read ----------

def list_raw(project_id: str | None = None, limit: int = 50) -> list[KnowledgeItem]:
    query = {"project_id": project_id} if project_id else {}
    return list(docs.col.find(query).limit(limit))


def search_vector(
    vector: list[float], project_id: str | None = None, limit: int = 5
) -> list[tuple[float, KnowledgeItem]]:
    where = {"project_id": project_id} if project_id else None
    return vectors.search(vector, where, limit)
