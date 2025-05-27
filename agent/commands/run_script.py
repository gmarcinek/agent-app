import subprocess
import webbrowser
import re
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

            # 🔍 Spróbuj wyciągnąć port z komendy
            port_match = re.search(r"--port[ =](\d+)", command)
            port = port_match.group(1) if port_match else "3000"
            url = f"http://localhost:{port}"

            # 🌐 Otwórz przeglądarkę z dynamicznym portem
            print(f"🌐 Otwieram przeglądarkę: {url}")
            webbrowser.open(url)

            # 🧠 Zapisz wynik do historii
            state.history.append(StepResult(
                step_name="run_script",
                input=self.params,
                output={
                    "ok": True,
                    "stdout": f"Dev server started in background on port {port}.",
                    "stderr": "",
                    "pid": process.pid
                }
            ))
            return state

        # 🔁 Tryb blokujący (nie dev-server)
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
