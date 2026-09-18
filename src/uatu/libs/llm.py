import json
from functools import cache
from typing import Protocol

import httpx
from langsmith import traceable

from uatu.libs.config import settings


class LLM(Protocol):
    
    def complete(self, system: str, user: str) -> str: ...

    def complete_json(self, system: str, user: str, schema: dict) -> dict: ...


class OllamaLLM:
    def __init__(self, url: str, model: str, timeout: float = 180.0) -> None:
        self.url = url
        self.model = model
        self.timeout = timeout

    def _chat(self, system: str, user: str, fmt: dict | None) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": 0},
        }
        if fmt is not None:
            payload["format"] = fmt
        with httpx.Client(timeout=self.timeout) as c:
            r = c.post(f"{self.url}/api/chat", json=payload)
            if r.status_code >= 400:
                detail = r.json().get("error", r.text)
                raise RuntimeError(f"ollama {r.status_code}: {detail}")
            return r.json()["message"]["content"]
    @traceable(run_type="llm")
    def complete(self, system: str, user: str) -> str:
        return self._chat(system, user, None)
    @traceable(run_type="llm")
    def complete_json(self, system: str, user: str, schema: dict) -> dict:
        return json.loads(self._chat(system, user, schema))


@cache
def get_llm() -> LLM:
    if settings.llm_provider == "ollama":
        return OllamaLLM(settings.ollama_url, settings.ollama_model)
    raise ValueError(f"unknown llm_provider: {settings.llm_provider}")

