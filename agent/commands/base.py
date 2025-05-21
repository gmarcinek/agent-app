from abc import ABC, abstractmethod
from agent.state import AgentState
from typing import Dict, Any

class Command(ABC):
    def __init__(self, params: Dict[str, Any]):
        self.params = params

    @abstractmethod
    def run(self, state: AgentState) -> AgentState:
        ...
