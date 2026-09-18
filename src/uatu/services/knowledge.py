from uatu.libs.embedder import embed
from uatu.models import KnowledgeItem
from uatu.models.knowledge import KnowledgeItemCreate
from uatu.store import knowledge as store
from uatu.prompts import load
from uatu.libs.llm import get_llm


def ingest(items: list[KnowledgeItemCreate], project_id: str) -> dict:
    """Raw text first (durable), vectors second (rebuildable)."""
    records = [KnowledgeItem(project_id=project_id, **i.model_dump()) for i in items]
    saved = store.save_raw(records)
    vectors = embed([i.text for i in records])
    indexed = store.index(records, vectors)
    return {"saved": saved, "indexed": indexed}


def search(query: str, project_id: str | None = None, limit: int = 5) -> list[dict]:
    vector = embed([query])[0]
    hits = store.search_vector(vector, project_id, limit)
    return [{"score": score, **item.model_dump(mode="json")} for score, item in hits]


def list_items(project_id: str | None = None, limit: int = 50) -> list[dict]:
    return store.list_raw(project_id, limit)


def extract(raw_text: str) -> list[KnowledgeItemCreate]:
    prompt = load("extract")
    raw = get_llm().complete_json(prompt.system, raw_text, prompt.schema)
    return [KnowledgeItemCreate(**i) for i in raw["items"]]
