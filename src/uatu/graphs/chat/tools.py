from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from uatu.libs import github_service as gh
from uatu.libs.embedder import embed
from uatu.models.repo import Repo
from uatu.services import credential as credential_service
from uatu.services import investigate as investigate_service
from uatu.store import code_file as code_store
from uatu.store import knowledge as knowledge_store
from uatu.store import repo as repo_store
from uatu.libs.config import settings


MAX_FILE_CHARS = 6_000
SEARCH_LIMIT = 6


def _project_id(config: RunnableConfig) -> str:
    """Prefer the run config. Fall back to the dev setting for local UIs only.

    The config path is the one that matters: in production project_id comes from
    the request path, so the model can never reach another project's data.
    agent-chat-ui cannot send custom configurable keys, hence the dev fallback.
    """
    project_id = (config.get("configurable") or {}).get("project_id")
    if project_id:
        return project_id

    if settings.uatu_dev_project_id:
        return settings.uatu_dev_project_id

    raise RuntimeError(
        "no project_id: pass it in config['configurable'] or set"
        "UATU_DEV_PROJECT_ID for local dev"
    )


def _find_repo(project_id: str, slug: str) -> Repo | None:
    wanted = slug.strip().lower()
    for repo in repo_store.list_for_project(project_id):
        if repo.slug.lower() == wanted:
            return repo
    return None


@tool
def search_knowledge(query: str, config: RunnableConfig) -> str:
    """Search what humans have written ABOUT this project: its features, its
    integrations, its API endpoints, and its known issues.

    Use this for questions about intent, product behaviour, or business rules —
    what the project is supposed to do. It does not know what any file contains.

    If this returns nothing useful, call search_code instead. Do not call this
    again with a reworded query.
    """

    project_id = _project_id(config)
    vector = embed([query])[0]
    hits = knowledge_store.search_vector(vector, project_id, SEARCH_LIMIT)

    if not hits:
        return "No knowledge items matched. This project may have no indexed docs."

    return "\n".join(
        f"- [{item.label.value}] {item.title}: {item.text}" for _, item in hits
    )


@tool
def search_code(query: str, config: RunnableConfig) -> str:
    """Find which FILES in this project's repositories are relevant to a topic.

    Returns prose descriptions of files, written during indexing — never source
    code. It tells you which file to look at and why; it cannot tell you what
    any line says. Call read_file once you know the path.

    Use this for questions about implementation, structure, or where something
    lives. If this returns nothing useful, call search_knowledge instead.
    """
    project_id = _project_id(config)
    vector = embed([query])[0]
    hits = code_store.search_vector(vector, project_id=project_id, limit=SEARCH_LIMIT)

    if not hits:
        return "No code files matched. The repository may not be indexed yet."

    return "\n".join(
        f"- {p.repo_slug}/{p.path} [{p.kind}] {p.text} (relevance {score:.2f})"
        for score, p in hits
    )


@tool
def read_file(repo_slug: str, path: str, config: RunnableConfig) -> str:
    """Read the actual source of one file. `repo_slug` is 'owner/name' and
    `path` is the repository-relative path, both exactly as search_code
    printed them.

    This is the only way to see real code. Use it before making any claim about
    what a specific line, variable or condition does. Long files are truncated.
    """
    project_id = _project_id(config)

    repo = _find_repo(project_id, repo_slug)
    if repo is None:
        available = [r.slug for r in repo_store.list_for_project(project_id)]
        return f"No repo named {repo_slug!r}. Available: {', '.join(available) or 'none'}"

    token = credential_service.get_token(project_id, repo.provider)
    if token is None:
        return f"No {repo.provider.value} credential is configured for this project."


    # Read at the INDEXED commit, not HEAD. The summaries search_code returns
    # describe this commit; reading HEAD would let the agent quote a line that
    # no longer matches the file it was pointed at.
    sha = repo.last_indexed_sha
    if sha is None:
        return f"{repo.slug} has never been indexed, so there is no commit to read."

    try:
        content = gh.read_file(repo.owner, repo.name, path, sha, token)
    except Exception as exc:
        return f"Could not read {path!r} from {repo.slug}: {exc}"

    if len(content) > MAX_FILE_CHARS:
        cut = len(content) - MAX_FILE_CHARS
        content = content[:MAX_FILE_CHARS] + f"\n\n[TRUNCATED: {cut} more characters]"

    return f"{repo.slug}/{path} @ {sha[:7]}\n\n{content}"


@tool
def diagnose(error: str, config: RunnableConfig) -> str:
    """Run the full diagnosis pipeline on a production error or stack trace.

    Use this ONLY when the user pastes an actual error and wants it explained.
    It retrieves context and returns ranked causes, suspect files, severity and
    impact. For ordinary questions about the project, use search_knowledge or
    search_code — this is far more expensive.

    Pass the error text verbatim, including the stack trace. Do not summarise it.
    """

    project_id = _project_id(config)

    try:
        d = investigate_service.investigate(error, project_id)
    except Exception as exc:
        return f"Diagnosis failed: {exc}"

    causes = "\n".join(
        f"  {i}. [{c.likelihood}] {c.hypothesis} — evidence: {c.evidence}"
        for i, c in enumerate(d.causes, 1)
    )
    return (
        f"{d.summary}\n"
        f"component: {d.affected_component or 'unknown'}\n"
        f"severity: {d.severity} | confidence: {d.confidence}\n"
        f"impact: {d.impact}\n"
        f"suspect files: {', '.join(d.suspect_files) or 'none'}\n"
        f"causes:\n{causes}\n"
        f"suggestions:\n" + "\n".join(f"  - {s}" for s in d.suggestions)
    )


TOOLS = [search_knowledge, search_code, read_file, diagnose]
