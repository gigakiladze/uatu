from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


PyObjectId = Annotated[str, BeforeValidator(str)]

class Document(BaseModel):
    """Base for anything persisted in Mongo. The store owns these three fields."""

    model_config = ConfigDict(populate_by_name=True)

    id: PyObjectId | None = Field(default=None, alias="_id", json_schema_extra={"readOnly": True})
    created_at: datetime | None = Field(default=None, alias="created_at", json_schema_extra={"readOnly": True})
    updated_at: datetime | None = Field(default=None, alias="updated_at", json_schema_extra={"readOnly": True})