from enum import Enum

from pydantic import BaseModel


class RepoProvider(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class Repo(BaseModel):
    project_id: str
    provider: RepoProvider = RepoProvider.GITHUB
    owner: str
    name: str
    branch: str = "main"
    description: str | None = None
    last_indexed_sha: str | None = None
    schema_version: int = 1
    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.name}"