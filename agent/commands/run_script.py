import subprocess
import webbrowser
import re
import os
from agent.commands.base import Command
from agent.state import AgentState, StepResult
from agent.runner import ScriptRunner
from registry.process_manager import ProcessManager

class RunScriptCommand(Command):
    def run(self, state: AgentState) -> StepResult:
        process_manager = ProcessManager()
        
        command = self.params["params"]["command"]
        cwd = self.params["params"].get("cwd", ".")
        dev_server = self.params["params"].get("dev_server_mode", False)

        if dev_server:
            print(f"🚀 Uruchamiam dev-server w tle: `{command}` (cwd={cwd})")
            
            # Platform-specific process independence
            creation_flags = 0
            preexec_fn = None
            
            if os.name == 'nt':  # Windows
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP
            else:  # Linux/Mac
                preexec_fn = os.setsid
            
            # 🔍 Spróbuj wyciągnąć port z komendy
            port_match = re.search(r"--port[ =](\d+)", command)
            port = port_match.group(1) if port_match else "3000"
            
            # Użyj ProcessManager zamiast bezpośredniego subprocess.Popen
            process_name = f"dev_server_{port}"
            success = process_manager.start_custom_process(
                name=process_name,
                cmd=command,  # jako string
                working_dir=cwd,
                detached=True,
                shell=True,
                creation_flags=creation_flags,
                preexec_fn=preexec_fn
            )
            
            if success:
                # Pobierz PID z zarejestrowanego procesu
                process = process_manager.processes[process_name]
                pid = process.pid
                
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
                        "pid": pid
                    }
                ))
            else:
                # Błąd uruchomienia
                state.history.append(StepResult(
                    step_name="run_script",
                    input=self.params,
                    output={
                        "ok": False,
                        "stdout": "",
                        "stderr": f"Failed to start dev server: {command}",
                        "pid": None
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