from pydantic import BaseModel
from typing import List
import json

class AgentInput(BaseModel):
    goal: str
    constraints: List[str] = []

    @staticmethod
    def from_file(path: str) -> "AgentInput":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return AgentInput(**data)
