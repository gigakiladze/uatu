from functools import cache

from qdrant_client import QdrantClient

from uatu.libs.config import settings



@cache
def get_client() -> QdrantClient:
    return QdrantClient(
        url=settings.qdrant_url,
        timeout=settings.qdrant_timeout_s,
    )

def ping() -> bool:
    get_client().info()
    return True