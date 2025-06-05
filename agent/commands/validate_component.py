from agent.commands.base import Command
from agent.state import AgentState, StepResult
from agent.validation.static import analyze_tsx_file
import os
import shutil

class ValidateComponentCommand(Command):
    def run(self, state: AgentState) -> AgentState:
        name = self.params["component_name"]
        src = os.path.join("output", "components", f"{name}.tsx")
        dst = os.path.join("output", "validated", f"{name}.tsx")

        passed, report = analyze_tsx_file(src)

        if passed:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(src, dst)

        state.history.append(StepResult(
            step_name="validate_component",
            input=self.params,
            output={
                "component_name": name,
                "source_path": src,
                "validated_path": dst if passed else None,
                "passed": passed,
                "report": report.strip()
            }
        ))

        return state