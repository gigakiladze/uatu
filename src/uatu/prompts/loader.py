
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import yaml

PROMPTS_DIR = Path(__file__).parent


@dataclass(frozen=True)
class Prompt:
    name: str
    version: int
    system: str
    schema: dict | None   # None when the caller owns the contract
    model: dict


def _split(raw: str) -> tuple[str, str]:
    if not raw.lstrip().startswith("---"):
        raise ValueError("prompty file must start with '---'")
    _, front, body = raw.split("---", 2)
    return front, body.strip()


@cache
def load(name: str) -> Prompt:
    path = PROMPTS_DIR / f"{name}.prompty"
    if not path.exists():
        raise FileNotFoundError(f"no prompt named {name!r} in {PROMPTS_DIR}")

    front, body = _split(path.read_text(encoding="utf-8"))
    meta = yaml.safe_load(front) or {}

    missing = {"name", "version"} - meta.keys()
    if missing:
        raise ValueError(f"{path.name} frontmatter missing: {sorted(missing)}")
    if not body:
        raise ValueError(f"{path.name} has no prompt body")

    return Prompt(
        name=meta["name"],
        version=meta["version"],
        system=body,
        schema=meta.get("outputs"),
        model=meta.get("model", {}),
    )
