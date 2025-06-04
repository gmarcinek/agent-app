import subprocess
import os
from logger import get_log_hub

class ScriptRunner:
    def __init__(self):
        self.log_hub = get_log_hub()

    def run(self, command: str, cwd: str = ".", timeout: int = 30) -> dict:
        """
        Uniwersalne uruchamianie komend systemowych w zadanym katalogu roboczym.
        cwd może być ścieżką względną lub absolutną.
        """
        exec_path = os.path.abspath(cwd or ".")

        if not os.path.isdir(exec_path):
            self.log_hub.error("AGENT", f"Katalog roboczy nie istnieje: {exec_path}")
            return {
                "ok": False,
                "stdout": "",
                "stderr": f"❌ Katalog roboczy nie istnieje: {exec_path}",
                "exit_code": -1
            }

        self.log_hub.info("AGENT", f"Uruchamiam komendę: `{command}` (cwd={exec_path})")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=exec_path,
                timeout=timeout
            )
            
            if result.returncode != 0:
                self.log_hub.error("AGENT", f"Komenda '{command}' zakończona z kodem {result.returncode}: {result.stderr}")
            
            return {
                "ok": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            self.log_hub.error("AGENT", f"Timeout wykonania komendy '{command}' (>{timeout}s)")
            return {
                "ok": False,
                "stdout": "",
                "stderr": "⏰ Timeout (komenda trwała zbyt długo)",
                "exit_code": -1
            }

        except Exception as e:
            self.log_hub.error("AGENT", f"Błąd uruchamiania komendy '{command}': {e}")
            return {
                "ok": False,
                "stdout": "",
                "stderr": f"❌ Błąd uruchamiania: {str(e)}",
                "exit_code": -1
            }