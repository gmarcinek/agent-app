import subprocess
import webbrowser
import re
import os
from pathlib import Path

from agent.commands.base import Command
from agent.state import AgentState, StepResult
from agent.runner import ScriptRunner
from registry.process_manager import ProcessManager
from logger import get_log_hub

class RunScriptCommand(Command):
    def run(self, state: AgentState) -> AgentState:
        log = get_log_hub()
        process_manager = ProcessManager()

        command = self.params["params"]["command"]
        cwd = self.params["params"].get("cwd", ".")
        dev_server = self.params["params"].get("dev_server_mode", False)

        if dev_server:
            return self._run_dev_server(state, command, cwd, process_manager, log)
        else:
            return self._run_normal_command(state, command, cwd, log)

    def _run_dev_server(self, state: AgentState, command: str, cwd: str, process_manager: ProcessManager, log) -> AgentState:
        """Uruchamia dev server w tle bez zaśmiecania konsoli"""
        log.info("RUNSCRIPT", f"🚀 Dev-server: `{command}` (cwd={cwd})")
        
        # Wykryj port z komendy
        port_match = re.search(r"--port[ =](\d+)", command)
        port = port_match.group(1) if port_match else "3000"
        process_name = f"dev_server_{port}"
        
        # Przygotuj ścieżki dla logów dev servera
        log_dir = Path("output/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        stdout_log = log_dir / f"dev_server_{port}_stdout.log"
        stderr_log = log_dir / f"dev_server_{port}_stderr.log"
        
        try:
            # Uruchom process w tle z przekierowaniem outputu do plików
            with open(stdout_log, 'w') as stdout_file, open(stderr_log, 'w') as stderr_file:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=os.path.abspath(cwd),
                    stdout=stdout_file,
                    stderr=stderr_file,
                    # Proces nie będzie detached, ale w tle
                )
            
            # Zarejestruj w ProcessManager
            process_manager.processes[process_name] = process
            log.info("RUNSCRIPT", f"✅ Dev server started (PID: {process.pid})")
            log.info("RUNSCRIPT", f"📝 Logs: {stdout_log}, {stderr_log}")
            
            # Otwórz przeglądarkę
            url = f"http://localhost:{port}"
            log.info("RUNSCRIPT", f"🌐 Opening browser: {url}")
            webbrowser.open(url)
            
            state.history.append(StepResult(
                step_name="run_script",
                input=self.params,
                output={
                    "ok": True,
                    "stdout": f"Dev server started on port {port}",
                    "stderr": "",
                    "pid": process.pid,
                    "logs": {
                        "stdout": str(stdout_log),
                        "stderr": str(stderr_log)
                    }
                }
            ))
            
        except Exception as e:
            error_msg = f"Failed to start dev server: {e}"
            log.error("RUNSCRIPT", error_msg)
            state.history.append(StepResult(
                step_name="run_script", 
                input=self.params,
                output={
                    "ok": False,
                    "stdout": "",
                    "stderr": error_msg,
                    "pid": None
                }
            ))
        
        return state

    def _run_normal_command(self, state: AgentState, command: str, cwd: str, log) -> AgentState:
        """Uruchamia normalną komendę z pełnym outputem"""
        log.info("RUNSCRIPT", f"💻 Running: `{command}` (cwd={cwd})")
        
        result = ScriptRunner().run(command, cwd=cwd)
        
        # Pokaż output w konsoli dla normalnych komend
        if result["stdout"]:
            log.info("RUNSCRIPT", f"STDOUT:\n{result['stdout']}")
        if result["stderr"]:
            log.warn("RUNSCRIPT", f"STDERR:\n{result['stderr']}")
            
        state.history.append(StepResult(
            step_name="run_script",
            input=self.params,
            output=result
        ))
        
        return state