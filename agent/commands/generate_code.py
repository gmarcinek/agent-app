import os
import json
from agent.commands.base import Command
from agent.state import AgentState, StepResult
from agent.prompt.builder import build_prompt
from agent.codegen.strategy import validate_and_recreate

class GenerateCodeCommand(Command):
    def run(self, state: AgentState) -> AgentState:
        print(f"📦 Params: {self.params}")
        prompt_text = self.params["params"]["prompt"]
        artifact = self.params["params"]["artifact"]

        artifact_name = artifact["name"]
        filepath = artifact["path"]  # Mamy już path!
        extension = artifact.get("extension", "")
        context_mode = self.params.get("context_mode", "meta_only")

        # 📁 Jeśli to folder – tylko utwórz katalog
        if not extension and not os.path.splitext(filepath)[1]:
            print(f"📂 Tworzę folder: {filepath}")
            os.makedirs(filepath, exist_ok=True)

            state.history.append(StepResult(
                step_name="mkdir",
                input=self.params,
                output={"created_path": filepath}
            ))
            return state

        # 🧠 Budujemy prompt i generujemy kod z walidacją
        prompt = build_prompt(
            prompt_text=prompt_text,
            artifact_name=artifact_name,
            artifact_path=filepath,  # ← DODAJ PATH
            context_mode=context_mode
        )

        code, validation_report = validate_and_recreate(
            prompt=prompt,
            filepath=filepath,
            extension=extension,
            max_attempts=5
        )

        # 💾 Zapis kodu
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        # 💾 Zapis metadanych
        meta = {
            "name": artifact_name,
            "path": filepath,
            "extension": extension,
            "prompt": prompt_text
        }
        context_path = os.path.join("output", "context", f"{artifact_name}.meta.json")
        os.makedirs(os.path.dirname(context_path), exist_ok=True)
        with open(context_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        # 📜 Zapis do historii agenta
        state.history.append(StepResult(
            step_name="generate_code",
            input=self.params,
            output={
                "code_path": filepath,
                "meta_path": context_path,
                "validation_report": validation_report
            }
        ))

        return state