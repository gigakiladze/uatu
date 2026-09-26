from uatu.libs.embedder import embed
from uatu.libs.llm import get_llm
from uatu.models import Diagnosis
from uatu.prompts import load
from uatu.store import code_file
from uatu.store import knowledge as knowledge_store



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
        for score, p in files:
            parts.append(
                f"- {p.repo_slug}/{p.path} [{p.kind}] {p.text} (relevance {score:.2f})"
            )
    else:
        parts.append("- (none found)")

    return "\n".join(parts)


def investigate(error: str, project_id: str) -> Diagnosis:
    prompt = load("investigate")
    user = build_prompt(error, project_id)
    raw = get_llm().complete_json(prompt.system, user, Diagnosis.model_json_schema())
    return Diagnosis.model_validate(raw)
