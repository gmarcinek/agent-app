import os
import json
from agent.commands.base import Command
from agent.state import AgentState, StepResult
from agent.prompt.builder import build_prompt
from agent.codegen.patch_strategy import validate_and_patch

class PatchFileCommand(Command):
    def run(self, state: AgentState) -> AgentState:
        print(f"🔧 Patch Params: {self.params}")
        prompt_text = self.params["params"]["prompt"]
        artifact = self.params["params"]["artifact"]

        artifact_name = artifact["name"]
        filepath = artifact["path"]
        extension = artifact.get("extension", "")
        context_mode = self.params.get("context_mode", "meta_only")

        # 📁 Sprawdź czy plik istnieje (patch wymaga istniejącego pliku)
        if not os.path.exists(filepath):
            print(f"❌ Nie można patch'ować nieistniejącego pliku: {filepath}")
            state.history.append(StepResult(
                step_name="patch_file",
                input=self.params,
                output={
                    "error": f"File does not exist: {filepath}",
                    "success": False
                }
            ))
            return state

        # 📂 Jeśli to folder - błąd
        if not extension and not os.path.splitext(filepath)[1]:
            print(f"❌ Nie można patch'ować folderu: {filepath}")
            state.history.append(StepResult(
                step_name="patch_file", 
                input=self.params,
                output={
                    "error": f"Cannot patch directory: {filepath}",
                    "success": False
                }
            ))
            return state

        # 🧠 Budujemy prompt i patch'ujemy kod z walidacją
        prompt = build_prompt(
            prompt_text=prompt_text,
            artifact_name=artifact_name,
            artifact_path=filepath,
            context_mode=context_mode
        )

        code, validation_report = validate_and_patch(
            prompt=prompt,
            filepath=filepath,
            extension=extension,
            max_attempts=3  # Mniej prób niż przy generowaniu
        )

        # 💾 Zapis kodu (patch'owanego)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        # 💾 Aktualizacja metadanych
        meta = {
            "name": artifact_name,
            "path": filepath,
            "extension": extension,
            "prompt": prompt_text,
            "operation": "patch"  # Oznacz że to był patch
        }
        context_path = os.path.join("output", "context", f"{artifact_name}.meta.json")
        os.makedirs(os.path.dirname(context_path), exist_ok=True)
        
        # Jeśli meta już istnieje, dodaj historię patches
        if os.path.exists(context_path):
            with open(context_path, "r", encoding="utf-8") as f:
                existing_meta = json.load(f)
            
            if "patch_history" not in existing_meta:
                existing_meta["patch_history"] = []
            
            existing_meta["patch_history"].append({
                "prompt": prompt_text,
                "timestamp": context_path  # lub datetime.now().isoformat()
            })
            meta = existing_meta
        
        with open(context_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

        # 📜 Zapis do historii agenta
        state.history.append(StepResult(
            step_name="patch_file",
            input=self.params,
            output={
                "code_path": filepath,
                "meta_path": context_path,
                "validation_report": validation_report,
                "success": validation_report.get("ok", False)
            }
        ))

        return state