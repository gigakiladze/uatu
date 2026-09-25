from enum import Enum

from pydantic import BaseModel

from uatu.models.base import Document


class RepoProvider(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class RepoCreate(BaseModel):
    owner: str
    name: str
    branch: str = "main"
    provider: RepoProvider = RepoProvider.GITHUB
    description: str | None = None




class Repo(RepoCreate, Document):
    project_id: str
    last_indexed_sha: str | None = None
    schema_version: int = 1

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.name}"