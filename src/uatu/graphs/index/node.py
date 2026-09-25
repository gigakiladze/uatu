from uatu.libs import github_service as gh
from uatu.libs.embedder import embed
from uatu.models.code_file import CodeFile
from uatu.models.repo import RepoProvider
from uatu.prompts import load
from uatu.services import credential as credential_service
from uatu.services.indexer import _language
from uatu.services.summarize import summarize_file
from uatu.store import code_file as store
from uatu.store import repo as repo_store
from uatu.graphs.index.state import IndexState
from uatu.models.repo import Repo



def _build(
    project_id: str, repo: Repo, sha: str, entry: dict, summary, version: int
) -> CodeFile:
    return CodeFile(
        project_id=project_id,
        repo_id=repo.id,
        repo_slug=repo.slug,
        path=entry["path"],
        size=entry["size"],
        blob_sha=entry["blob_sha"],
        commit_sha=sha,
        language=_language(entry["path"]),
        summary=summary,
        prompt_version=version,
    )


def resolve(state: IndexState) -> dict:
    project_id, repo_id = state["project_id"], state["repo_id"]

    repo = repo_store.get(project_id, repo_id)
    if repo is None:
        raise LookupError(f"repo not found in project: {repo_id}")

    token = credential_service.get_token(project_id, repo.provider)
    if token is None:
        raise LookupError(f"no {repo.provider.value} credential for project {project_id}")

    sha = gh.head_sha(repo.owner, repo.name, token, repo.branch)
    skip = sha == repo.last_indexed_sha

    return {
        "repo": repo,
        "token": token,
        "sha": sha,
        "skip": skip,
        "result": {"status": "up_to_date", "sha": sha} if skip else {},
    }



def list_files(state: IndexState) -> dict:
    """Tree, filter, cache. Splits into work to do and summaries to reuse."""
    project_id, repo = state["project_id"], state["repo"]
    repo, sha, token = state["repo"], state["sha"], state["token"]

    tree = gh.list_tree(repo.owner, repo.name, sha, token)
    entries = [e for e in tree if gh.is_indexable(e)]

    version = load("summarize").version
    cached = store.summaries_by_blob(
        project_id, [e["blob_sha"] for e in entries], version
    )

    todo = [e for e in entries if e["blob_sha"] not in cached]
    reused = [
        _build(project_id, repo, sha, e, cached[e["blob_sha"]], version)
        for e in entries
        if e["blob_sha"] in cached
    ]

    return {
        "version": version,
        "todo": todo,
        "files": reused,
        "scanned": len(tree),
        "kept": len(entries),
        "reused": len(reused),
    }


def summarize_one(state: IndexState) -> dict:
    """One file. Runs once per Send; the reducer concatenates the results."""
    entry = state["entry"]
    repo, sha, token = state["repo"], state["sha"], state["token"]

    content = gh.read_file(repo.owner, repo.name, entry["path"], sha, token)
    summary = summarize_file(entry["path"], content)

    return {
        "files": [
            _build(
                state["project_id"], state["repo"], sha, entry, summary, state["version"]
            )
        ]
    }


def persist(state: IndexState) -> dict:
    """Runs once, after every Send has completed."""
    project_id, repo, sha = state["project_id"], state["repo"], state["sha"]
    files = state.get("files", [])

    saved = store.save(files)
    points = [p for f in files for p in f.points()]
    indexed = store.index(points, embed([p.text for p in points])) if points else 0
    removed = store.sweep(project_id, repo.id, sha)
    repo_store.set_indexed_sha(repo.id, sha)

    return {
        "result": {
            "status": "indexed",
            "sha": sha,
            "scanned": state.get("scanned", 0),
            "kept": state.get("kept", 0),
            "saved": saved,
            "points": len(points),
            "indexed": indexed,
            "llm_calls": len(state.get("todo", [])),
            "reused": state.get("reused", 0),
            "removed": removed,
        }
    }
