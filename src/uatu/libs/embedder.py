from functools import cache
from sentence_transformers import SentenceTransformer

from uatu.libs.config import settings

@cache
def get_model() -> SentenceTransformer: 
    return SentenceTransformer(settings.embedding_model)

def embed(text: list[str]) -> list [list[float]]:
    vectors = get_model().encode(
        text,
        normalize_embeddings=True,
        batch_size=32
    )
    return vectors.tolist()