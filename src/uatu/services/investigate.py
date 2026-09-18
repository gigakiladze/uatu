from uatu.libs.embedder import embed
from uatu.libs.llm import get_llm
from uatu.models import Diagnosis
from uatu.store import code_file
from uatu.store import knowledge as knowledge_store

SYSTEM = """You are a senior engineer diagnosing a production error.

You are given an error, a description of the project, and a list of files from
its codebase. Use ONLY that context.

Rules:
- If the context does not explain the error, set confidence to "low" and say so
  in the summary. Do not speculate beyond what you were given.
- Every cause must cite specific evidence from the context.
- suspect_files may only contain paths that appear in the CODE FILES section.
- Be concrete. "Check the logs" is not a suggestion."""


def build_prompt(error: str, project_id: str, k_limit: int = 3, f_limit: int = 8) -> str:
    vector = embed([error])[0]                      # embed once, search twice
    knowledge = knowledge_store.search_vector(vector, project_id, k_limit)
    files = code_file.search_vector(vector, project_id=project_id, limit=f_limit)

    parts = [f"ERROR:\n{error}\n"]

    parts.append("PROJECT CONTEXT:")
    if knowledge:
        for score, item in knowledge:
            parts.append(f"- [{item.label.value}] {item.title}: {item.text}")
    else:
        parts.append("- (none found)")

    parts.append("\nCODE FILES (ranked by relevance):")
    if files:
        for score, f in files:
            summary = f" — {f.summary}" if f.summary else ""
            parts.append(f"- {f.path} ({f.language}, relevance {score:.2f}){summary}")
    else:
        parts.append("- (none found)")

    return "\n".join(parts)


def investigate(error: str, project_id: str) -> Diagnosis:
    prompt = build_prompt(error, project_id)
    raw = get_llm().complete_json(SYSTEM, prompt, Diagnosis.model_json_schema())
    return Diagnosis.model_validate(raw)
