from typing import List, Dict, Any
from pydantic import BaseModel, Field

class StepResult(BaseModel):
    step_name: str
    input: Dict[str, Any]
    output: Dict[str, Any]

class AgentState(BaseModel):
    history: List[StepResult] = Field(default_factory=list)
    current_step_index: int = 0
    outputs: Dict[str, Any] = Field(default_factory=dict)
    done: bool = False
    artifacts: Dict[str, str] = Field(default_factory=dict)

class Scenario:
    def __init__(self, goal: str, steps: List[Dict[str, Any]]):
        self.goal = goal
        self.steps = steps
