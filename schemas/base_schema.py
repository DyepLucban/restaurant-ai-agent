from pydantic import BaseModel

class QueryBody(BaseModel):
    query: str
    session_id: str | None = None
