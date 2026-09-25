from uatu.models.base import Document
from uatu.models.repo import RepoProvider



class CreateCredentialRequest(Document):
    provider: RepoProvider
    token: str

class Credential(CreateCredentialRequest):
    project_id: str
    token_fingerprint: str

