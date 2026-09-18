from enum import Enum
from uuid  import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel


class Label(str, Enum):
    OVERVIEW = "overview"
    FEATURE = "feature"
    INTEGRATION = "integration"
    ENDPOINT = "endpoint"
    KNOWN_ISSUE = "known_issue"


class KnowledgeItemCreate(BaseModel):
    label: Label
    title: str
    text: str    


class KnowledgeItem(KnowledgeItemCreate):
    project_id: str
    schema_version: int = 1
    
    @property
    def point_id(self) -> UUID:
        """
        Generate a deterministic UUID based on the project, label, and title.
        This ensures that the same combination of these fields will always produce the same UUID.
        """
        unique_string = f"{self.project_id }:{self.label.value}:{self.title}"
        return uuid5(NAMESPACE_URL, unique_string)

     