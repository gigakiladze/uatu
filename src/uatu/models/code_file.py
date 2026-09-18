from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel


class CodeFile(BaseModel):
    project_id: str
    repo: str
    path: str
    size: int
    blob_sha: str
    commit_sha: str
    language: str | None = None
    summary: str | None = None      # stays None in stage A
    schema_version: int = 1

    @property
    def doc_id(self) -> str:
        """Mongo _id — readable."""
        return f"{self.repo}:{self.path}"

    @property
    def point_id(self) -> UUID:
        return uuid5(NAMESPACE_URL, f"uatu://{self.doc_id}")

    @property
    def embed_text(self) -> str:
        return f"{self.path}\n{self.summary}" if self.summary else self.path