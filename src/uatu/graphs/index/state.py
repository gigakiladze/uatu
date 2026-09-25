import operator
from typing import Annotated, TypedDict

from uatu.models.code_file import CodeFile
from uatu.models.repo import Repo

class IndexState(TypedDict, total=False):
    # inputs
    project_id: str
    repo_id: str
    # set by resolve
    repo: Repo
    token: str
    sha: str
    skip: bool

    # set by list_files
    version: int
    todo: list[dict]
    scanned: int
    kept: int
    reused: int

    # per-Send payload for summarize_one
    entry: dict

    # gathered from the fan-out — operator.add concatenates instead of overwriting
    files: Annotated[list[CodeFile], operator.add]

    # set by persist
    result: dict