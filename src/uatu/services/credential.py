from uatu.libs.crypto import encrypt, decrypt, fingerprint
from uatu.models import Credential
from uatu.models.repo import RepoProvider
from uatu.store import credential as store


def get_token(project_id: str, provider: RepoProvider) -> str | None:
    """The decrypted secret, or None. The only function that returns plaintext."""
    cred = store.get_credential(project_id, provider)
    return decrypt(cred.token) if cred else None

def get_credentials(project_id: str) -> list[Credential]:
    """Get all credentials for a project."""
    creds = store.get_credentials(project_id)
    return creds


def create_credential(project_id: str, provider: RepoProvider, token: str) -> dict:
    """Create the credential for a project."""
    encrypted_token = encrypt(token)
    token_fingerprint = fingerprint(token)
    return store.create_credential(project_id, provider, encrypted_token, token_fingerprint)