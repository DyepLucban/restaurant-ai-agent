from pydantic import BaseModel
from typing import Literal

class Route(BaseModel):
    intent: Literal["faq", "reservation", "chitchat", "out_of_scope"]