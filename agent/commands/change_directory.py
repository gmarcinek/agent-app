from agent.commands.base import Command
from agent.state import AgentState, StepResult

class ChangeDirectoryCommand(Command):
    def run(self, state: AgentState) -> AgentState:
        path = self.params["params"]["path"]

        # aktualizujemy stan, ale nie wpływamy na systemowy cwd
        state.outputs["cwd"] = path

        print(f"📂 Zmieniono katalog roboczy agenta: {path}")

        state.history.append(StepResult(
            step_name="cd",
            input=self.params,
            output={"cwd": path}
        ))

        return state