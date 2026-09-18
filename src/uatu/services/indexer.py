from pathlib import Path

from uatu.libs import github_service as gh
from uatu.libs.embedder import embed
from uatu.models import CodeFile
from uatu.store import code_file as store
from uatu.store import repo as repo_store

BATCH = 256

_EXT = {".py": "python", ".ts": "typescript", ".tsx": "typescript",
        ".js": "javascript", ".jsx": "javascript", ".go": "go",
        ".rs": "rust", ".java": "java", ".rb": "ruby", ".php": "php"}


def _language(path: str) -> str | None:
    return _EXT.get(Path(path).suffix)


def index_repo(slug: str) -> dict:
    repo = repo_store.get(slug)
    if repo is None:
        raise LookupError(f"repo not registered: {slug}")

    sha = gh.head_sha(repo.owner, repo.name, repo.branch)
    if sha == repo.last_indexed_sha:
        return {"status": "up_to_date", "sha": sha, "indexed": 0}

    tree = gh.list_tree(repo.owner, repo.name, sha)
    entries = [e for e in tree if gh.is_indexable(e)]

    files = [
        CodeFile(
            project_id=repo.project_id,
            repo=slug,
            path=e["path"],
            size=e["size"],
            blob_sha=e["blob_sha"],
            commit_sha=sha,
            language=_language(e["path"]),
        )
        for e in entries
    ]

    saved = indexed = 0
    for i in range(0, len(files), BATCH):
        batch = files[i : i + BATCH]
        saved += store.save(batch)
        indexed += store.index(batch, embed([f.embed_text for f in batch]))

    repo_store.set_indexed_sha(slug, sha)   # last, deliberately

    return {"status": "indexed", "sha": sha, "scanned": len(tree),
            "kept": len(files), "saved": saved, "indexed": indexed}