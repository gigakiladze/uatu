from sympy import re

from uatu.libs.repository import MongoRepository
from uatu.models import Credential
from uatu.models.repo import RepoProvider
  

COLLECTION = "credentials"

docs = MongoRepository(COLLECTION, Credential)

def ensure_indexes() -> None:
    docs.col.create_index([("project_id", 1), ("provider", 1)], unique=True)

def create_credential(project_id: str, provider: RepoProvider, encrypted_token: str, token_fingerprint: str) -> dict:
 return docs.upsert_by(
        {"project_id": project_id, "provider": provider},
        Credential(
            project_id=project_id,
            provider=provider,
            token=encrypted_token,
            token_fingerprint=token_fingerprint,
        ),
    )

def get_credential(project_id: str, provider: RepoProvider ) -> Credential | None:
    return docs.find_one({"project_id": project_id, "provider": provider})


def get_credentials(project_id: str) -> list[Credential]:
    return docs.find({"project_id": project_id})
