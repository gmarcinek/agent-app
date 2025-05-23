from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import os
import json

class StepResult(BaseModel):
    step_name: str
    input: Dict[str, Any]
    output: Dict[str, Any]

class AgentState(BaseModel):
    history: List[StepResult] = Field(default_factory=list)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    done: bool = False
    current_step_index: int = 0
    artifacts: Dict[str, str] = Field(default_factory=dict)

    def to_json(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.dict(), f, indent=2, ensure_ascii=False)

    @staticmethod
    def from_json(path: str) -> "AgentState":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return AgentState(**data)

class Scenario:
    def __init__(self, goal: str, steps: List[Dict[str, Any]]):
        self.goal = goal
        self.steps = steps
