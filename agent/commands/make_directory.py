import os
from agent.commands.base import Command
from agent.state import AgentState, StepResult

class MakeDirectoryCommand(Command):
    def run(self, state: AgentState) -> AgentState:
        print(f"📦 Params: {self.params}")
        path = self.params["params"]["path"]
        try:
            os.makedirs(path, exist_ok=True)
            print(f"📁 Utworzono folder: {path}")
            success = True
        except Exception as e:
            print(f"❌ Błąd podczas mkdir: {e}")
            success = False

        state.history.append(StepResult(
            step_name="mkdir",
            input=self.params,
            output={"path": path, "success": success}
        ))

        return state
