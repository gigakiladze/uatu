from pathlib import Path

from uatu.libs import github_service as gh
from uatu.libs.embedder import embed
from uatu.models.code_file import CodeFile
from uatu.models.repo import RepoProvider
from uatu.prompts import load
from uatu.services import credential as credential_service
from uatu.services.summarize import summarize_file
from uatu.store import code_file as store
from uatu.store import repo as repo_store

_EXT = {".py": "python", ".ts": "typescript", ".tsx": "typescript",
        ".js": "javascript", ".jsx": "javascript", ".go": "go",
        ".rs": "rust", ".java": "java", ".rb": "ruby", ".php": "php"}


def _language(path: str) -> str | None:
    return _EXT.get(Path(path).suffix)


def index_repo(project_id: str, slug: str) -> dict:
    doc_id = f"{project_id}:{slug}"

    repo = repo_store.get(doc_id)
    if repo is None:
        raise LookupError(f"repo not registered: {slug}")

    token = credential_service.get_token(project_id, RepoProvider.GITHUB)
    if token is None:
        raise LookupError(f"no github credential for project {project_id}")

    sha = gh.head_sha(repo.owner, repo.name, token, repo.branch)
    if sha == repo.last_indexed_sha:
        return {"status": "up_to_date", "sha": sha}

    tree = gh.list_tree(repo.owner, repo.name, sha, token)
    entries = [e for e in tree if gh.is_indexable(e)]

    version = load("summarize").version
    cached = store.summaries_by_blob(
        project_id, [e["blob_sha"] for e in entries], version
    )

    files: list[CodeFile] = []
    llm_calls = 0
    for e in entries:
        summary = cached.get(e["blob_sha"])
        if summary is None:
            content = gh.read_file(repo.owner, repo.name, e["path"], sha, token)
            summary = summarize_file(e["path"], content)
            llm_calls += 1
        files.append(
            CodeFile(
                project_id=project_id,
                repo=slug,
                path=e["path"],
                size=e["size"],
                blob_sha=e["blob_sha"],
                commit_sha=sha,
                language=_language(e["path"]),
                summary=summary,
                prompt_version=version,
            )
        )

    saved = store.save(files)
    points = [p for f in files for p in f.points()]
    indexed = store.index(points, embed([p.text for p in points])) if points else 0
    removed = store.sweep(project_id, slug, sha)
    repo_store.set_indexed_sha(doc_id, sha)

    return {
        "status": "indexed", "sha": sha,
        "scanned": len(tree), "kept": len(files), "saved": saved,
        "points": len(points), "indexed": indexed,
        "llm_calls": llm_calls, "reused": len(cached), "removed": removed,
    }