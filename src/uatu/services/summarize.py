from uatu.libs.llm import get_llm
from uatu.models.code_file import FileSummary
from uatu.prompts import load

MAX_CHARS = 8_000


def summarize_file(path: str, content: str) -> FileSummary:
      prompt = load("summarize")

      body = content[:MAX_CHARS]
      if len(content) > MAX_CHARS:
          body += f"\n\n[TRUNCATED: {len(content) - MAX_CHARS} more characters not shown]"

      user = f"PATH: {path}\n\nSOURCE:\n{body}"
      raw = get_llm().complete_json(prompt.system, user, prompt.schema)
      return FileSummary(**raw)