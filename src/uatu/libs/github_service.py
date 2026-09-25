import httpx


from pathlib import Path

API = "https://api.github.com"

MAX_FILE_BYTES = 500_000


SKIP_DIRS = {
    "node_modules", "vendor", "dist", "build", ".next", "out",
    "__pycache__", ".venv", "venv", "target", "coverage",
}

SKIP_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "uv.lock", "poetry.lock", "Cargo.lock", "go.sum",
}

CODE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".go", ".rs",
    ".java", ".kt", ".rb", ".php", ".cs", ".swift", ".c", ".cpp", ".h",
}


def _client(token: str) -> httpx.Client:
    return httpx.Client(
        base_url=API,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Authorization": f"Bearer {token}",
        },
        timeout=30.0,
        follow_redirects=True,
    )


def head_sha(owner: str, repo: str, token: str, branch: str | None = None) -> str:
    with _client(token) as c:
        if branch is None:
            r = c.get(f"/repos/{owner}/{repo}")
            r.raise_for_status()
            branch = r.json()["default_branch"]
        r = c.get(f"/repos/{owner}/{repo}/commits/{branch}")
        r.raise_for_status()
        return r.json()["sha"]


def list_tree(owner: str, repo: str, sha: str, token: str) -> list[dict]:
    """Every blob in the repo at this commit: path, size, blob sha. One request."""
    with _client(token) as c:
        r = c.get(f"/repos/{owner}/{repo}/git/trees/{sha}", params={"recursive": "1"})
        r.raise_for_status()
        data = r.json()

    if data.get("truncated"):
        raise RuntimeError(f"tree truncated for {owner}/{repo} — needs paged walk")

    return [
        {"path": e["path"], "size": e.get("size", 0), "blob_sha": e["sha"]}
        for e in data["tree"]
        if e["type"] == "blob"
    ]


def read_file(owner: str, repo: str, path: str, sha: str, token: str) -> str:
    """Raw file contents at an exact commit. Never at HEAD."""
    with _client(token) as c:
        r = c.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": sha},
            headers={"Accept": "application/vnd.github.raw"},
        )
        r.raise_for_status()
        return r.text


def is_indexable(entry: dict) -> bool:
    """Is this tree entry worth embedding?"""
    p = Path(entry["path"])
    if any(part in SKIP_DIRS for part in p.parts):
        return False
    if p.name in SKIP_FILES:
        return False
    if p.suffix not in CODE_EXTENSIONS:
        return False
    return entry["size"] <= MAX_FILE_BYTES
