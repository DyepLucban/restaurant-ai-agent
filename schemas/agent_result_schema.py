from pydantic import BaseModel, Field
from typing import Literal

class AgentResult(BaseModel):
    status: Literal["done", "needs_info", "needs_confirmation", "failed"]
    summary: str
    data: dict = Field(default_factory=dict)
    missing_fields = list[str] = Field(default_factory=list)