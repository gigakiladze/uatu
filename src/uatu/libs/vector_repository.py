from typing import Generic, TypeVar

from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, FieldCondition, Filter, FilterSelector, MatchValue, PointStruct, VectorParams,
)

from uatu.libs.qdrant_service import get_client

T = TypeVar("T", bound=BaseModel)


class QdrantRepository(Generic[T]):
    """Shared vector access. One instance per collection."""

    def __init__(
        self,
        collection: str,
        model: type[T],
        vector_size: int,
        indexed_fields: tuple[str, ...] = (),
        distance: Distance = Distance.COSINE,
    ) -> None:
        self.name = collection
        self.model = model
        self.vector_size = vector_size
        self.indexed_fields = indexed_fields
        self.distance = distance

    @property
    def client(self) -> QdrantClient:
        return get_client()

    def ensure_collection(self) -> None:
        """Idempotent. Call at startup."""
        if not self.client.collection_exists(self.name):
            self.client.create_collection(
                self.name,
                vectors_config=VectorParams(
                    size=self.vector_size, distance=self.distance
                ),
            )
        for field in self.indexed_fields:
            self.client.create_payload_index(
                self.name, field_name=field, field_schema="keyword"
            )


    def upsert(self, points: dict[str, tuple[list[float], T]]) -> int:
        """points maps id -> (vector, model). The model becomes the payload."""
        if not points:
            return 0
        structs = [
            PointStruct(id=pid, vector=vec, payload=m.model_dump(mode="json"))
            for pid, (vec, m) in points.items()
        ]
        self.client.upsert(self.name, points=structs)
        return len(structs)

    def delete(self, ids: list[str]) -> None:
        self.client.delete(self.name, points_selector=ids)

    # ---------- read ----------

    def search(
        self, vector: list[float], where: dict | None = None, limit: int = 5
    ) -> list[tuple[float, T]]:
        hits = self.client.query_points(
            self.name,
            query=vector,
            query_filter=self._filter(where),
            limit=limit,
            with_payload=True,
        ).points
        return [(h.score, self.model.model_validate(h.payload)) for h in hits]

    def count(self) -> int:
        return self.client.count(self.name).count

    @staticmethod
    def _filter(where: dict | None) -> Filter | None:
        """{'project': 'pinokey'} -> Qdrant Filter. Pass a Filter directly for complex cases."""
        if not where:
            return None
        if isinstance(where, Filter):
            return where
        return Filter(
            must=[
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in where.items()
            ]
        )
    
    def delete_where(self, must: dict, must_not: dict | None = None) -> None:
        """Delete every point matching `must` and not matching `must_not`."""
        self.client.delete(
            self.name,
            points_selector=FilterSelector(
                filter=Filter(
                    must=[
                        FieldCondition(key=k, match=MatchValue(value=v))
                        for k, v in must.items()
                    ],
                    must_not=[
                        FieldCondition(key=k, match=MatchValue(value=v))
                        for k, v in (must_not or {}).items()
                    ],
                )
            ),
        )


