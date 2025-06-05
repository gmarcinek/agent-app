import os
import shutil
from agent.commands.base import Command
from agent.state import AgentState, StepResult

class DeleteCommand(Command):
    def run(self, state: AgentState) -> AgentState:
        path = self.params["params"]["path"]
        deleted = False

        try:
            if os.path.isfile(path):
                os.remove(path)
                deleted = True
            elif os.path.isdir(path):
                shutil.rmtree(path)
                deleted = True

            print(f"🗑️ Usunięto: {path}" if deleted else f"⚠️ Nie znaleziono: {path}")
        except Exception as e:
            print(f"❌ Błąd przy usuwaniu {path}: {e}")

        state.history.append(StepResult(
            step_name="delete",
            input=self.params,
            output={"deleted": deleted, "path": path}
        ))

        return state