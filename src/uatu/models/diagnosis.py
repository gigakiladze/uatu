
from typing import Literal

from pydantic import BaseModel, Field


class Cause(BaseModel):
    hypothesis: str = Field(description="What went wrong, in one sentence")
    evidence: str = Field(description="Which provided context supports this")
    likelihood: Literal["high", "medium", "low"]


class Diagnosis(BaseModel):
    summary: str = Field(description="One line, suitable for a Slack notification")
    affected_component: str | None = Field(
        description="Feature or integration named in the project's own vocabulary"
    )
    suspect_files: list[str] = Field(description="Paths from the provided code context")
    causes: list[Cause] = Field(description="Ranked hypotheses of what went wrong")
    suggestions: list[str] = Field(description="Concrete next steps for a developer")
    impact: str = Field(description="Who or what is affected, and how badly")
    severity: Literal["critical", "high", "medium", "low"]
    confidence: Literal["high", "medium", "low"] = Field(
        description="low if the provided context does not actually explain the error"
    )