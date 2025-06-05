from agent.commands.base import Command
from agent.state import AgentState, StepResult
import os
import shutil

class WriteFileCommand(Command):
    def run(self, state: AgentState) -> AgentState:
        path = self.params["params"]["path"]
        name = os.path.splitext(os.path.basename(path))[0]

        # 🔁 Zmieniono ścieżkę źródłową na validated
        src_path = os.path.join("output", "validated", f"{name}.tsx")

        if not os.path.exists(src_path):
            raise FileNotFoundError(f"Nie znaleziono zwalidowanego komponentu: {src_path}")

        final_path = path
        conflict = False

        if os.path.exists(path):
            with open(path, encoding="utf-8") as f1, open(src_path, encoding="utf-8") as f2:
                if f1.read() != f2.read():
                    alt_path = os.path.splitext(path)[0] + ".generated.tsx"
                    shutil.copyfile(src_path, alt_path)
                    final_path = alt_path
                    conflict = True
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            shutil.copyfile(src_path, path)

        component_name = name
        state.artifacts[component_name] = final_path

        state.history.append(StepResult(
            step_name="write_file",
            input=self.params,
            output={
                "copied_from": src_path,
                "copied_to": final_path,
                "component_name": component_name,
                "conflict": conflict
            }
        ))

        return state