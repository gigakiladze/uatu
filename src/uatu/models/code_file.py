from typing import Literal
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel


class FileSummary(BaseModel):
    """What the LLM returns for one file."""

    purpose: str
    responsibilities: list[str]
    integrations: list[str] = []


class CodePoint(BaseModel):
    project_id: str
    repo_id: str
    repo_slug: str                    
    path: str
    blob_sha: str
    commit_sha: str
    language: str | None = None
    kind: Literal["purpose", "responsibility"]
    text: str
    index: int = 0

    @property
    def point_id(self) -> str:
        key = (
            f"uatu://{self.project_id}:{self.repo_id}:{self.path}"
            f"#{self.kind}{self.index}"
        )
        return str(uuid5(NAMESPACE_URL, key))


class CodeFile(BaseModel):
    project_id: str
    repo_id: str
    repo_slug: str
    path: str
    size: int
    blob_sha: str
    commit_sha: str
    language: str | None = None
    summary: FileSummary | None = None
    prompt_version: int | None = None
    schema_version: int = 1

    @property
    def doc_id(self) -> str:
         return f"{self.project_id}:{self.repo_id}:{self.path}"

    def points(self) -> list[CodePoint]:
        """One CodePoint per searchable text: the purpose, then each responsibility."""
        if self.summary is None:
            return []
        texts: list[tuple[str, str]] = [("purpose", self.summary.purpose)]
        texts += [("responsibility", r) for r in self.summary.responsibilities]
        return [
            CodePoint(
                project_id=self.project_id,
                repo_id=self.repo_id,
                repo_slug=self.repo_slug,
                path=self.path,
                blob_sha=self.blob_sha,
                commit_sha=self.commit_sha,
                language=self.language,
                kind=kind,
                text=text,
                index=i,
            )
            for i, (kind, text) in enumerate(texts)
        ]