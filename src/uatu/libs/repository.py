from datetime import datetime, timezone
from typing import Generic, TypeVar

from bson import ObjectId
from pydantic import BaseModel
from pymongo import UpdateOne
from pymongo.collection import Collection

from uatu.libs.db_service import get_db

T = TypeVar("T", bound=BaseModel)

# Store-owned. The repository stamps these; a model must never write them.
_META = {"id", "created_at", "updated_at"}


class MongoRepository(Generic[T]):
    """Shared Mongo access. One instance per collection."""

    def __init__(self, collection: str, model: type[T]) -> None:
        self.name = collection
        self.model = model

    @property
    def col(self) -> Collection:
        return get_db()[self.name]

    # ---------- write ----------

    def insert(self, model: T) -> str:
        """Insert with a Mongo-generated _id. Returns it as a string."""
        now = datetime.now(timezone.utc)
        doc = model.model_dump(mode="json", exclude=_META)
        doc["created_at"] = now
        doc["updated_at"] = now
        return str(self.col.insert_one(doc).inserted_id)

    def upsert_many(self, docs: dict[str, T]) -> int:
        """docs maps _id -> model. Stamps created_at once, updated_at always."""
        if not docs:
            return 0
        now = datetime.now(timezone.utc)
        ops = [
            UpdateOne(
                {"_id": self._key(_id)},
                {
                    "$set": {
                        **m.model_dump(mode="json", exclude=_META),
                        "updated_at": now,
                    },
                    "$setOnInsert": {"created_at": now},
                },
                upsert=True,
            )
            for _id, m in docs.items()
        ]
        result = self.col.bulk_write(ops)
        return result.upserted_count + result.modified_count

    def delete(self, _id: str) -> bool:
        return self.col.delete_one({"_id": self._key(_id)}).deleted_count == 1

    # ---------- read ----------

    def get(self, _id: str) -> T | None:
        doc = self.col.find_one({"_id": self._key(_id)})
        return self.model.model_validate(doc) if doc else None

    def find(self, query: dict | None = None, limit: int = 50) -> list[T]:
        docs = self.col.find(query or {}).limit(limit)
        return [self.model.model_validate(d) for d in docs]

    def exists(self, _id: str) -> bool:
        return self.col.count_documents({"_id": self._key(_id)}, limit=1) == 1

    def find_one(self, filter: dict) -> T | None:
        """First document matching an arbitrary filter, as a model."""
        doc = self.col.find_one(filter)
        return self.model.model_validate(doc) if doc else None

    # ---------- helpers ----------

    @staticmethod
    def _key(_id: str) -> ObjectId | str:
        """Mongo-generated ids are ObjectId; deterministic uuid5 ids stay strings."""
        return ObjectId(_id) if ObjectId.is_valid(_id) else _id
        
    def upsert_by(self, filter: dict, model: T) -> bool:
     now = datetime.now(timezone.utc)
     doc = model.model_dump(mode="json", exclude=_META)
     result = self.col.update_one(
        filter,                                    # ← was {"_id": self._key(_id)}
        {
            "$set": {**doc, "updated_at": now},
            "$setOnInsert": {"created_at": now},
        },
        upsert=True,
    )
     return result.upserted_id is not None




