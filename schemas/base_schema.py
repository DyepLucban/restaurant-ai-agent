from pydantic import BaseModel, Field

class QueryBody(BaseModel):
    query: str
    session_id: str | None = None

class SharedState(BaseModel):
    cart: dict[str, int] = Field(default_factory=dict)
    history: list = Field(default_factory=list)