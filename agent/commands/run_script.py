import subprocess
import webbrowser
from agent.commands.base import Command
from agent.state import AgentState, StepResult
from agent.runner import ScriptRunner
from agent.process_registry import process_registry

class RunScriptCommand(Command):
    def run(self, state: AgentState) -> AgentState:
        command = self.params["params"]["command"]
        cwd = self.params["params"].get("cwd", ".")
        dev_server = self.params["params"].get("dev_server_mode", False)

        if dev_server:
            print(f"🚀 Uruchamiam dev-server w tle: `{command}` (cwd={cwd})")
            process = subprocess.Popen(
                command,
                cwd=cwd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            process_registry.register(process)

            # Otwórz w domyślnej przeglądarce
            print("🌐 Otwieram przeglądarkę na http://localhost:3000")
            webbrowser.open("http://localhost:3000")

            # Dodaj wpis do historii, ale nie czekaj na zakończenie
            state.history.append(StepResult(
                step_name="run_script",
                input=self.params,
                output={
                    "ok": True,
                    "stdout": "Dev server started in background.",
                    "stderr": "",
                    "pid": process.pid
                }
            ))
            return state

        # Tryb zwykły — blokujący
        runner = ScriptRunner()
        result = runner.run(command, cwd=cwd)

        print(f"💻 Uruchomiono: `{command}` (cwd={cwd})")
        print(result["stdout"])
        if not result["ok"]:
            print(f"❌ Błąd: {result['stderr']}")

        state.history.append(StepResult(
            step_name="run_script",
            input=self.params,
            output=result
        ))

        return state
