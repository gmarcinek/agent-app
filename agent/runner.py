import subprocess
import os

class ScriptRunner:
    def run(self, command: str, cwd: str = ".", timeout: int = 30) -> dict:
        """
        Uniwersalne uruchamianie komend systemowych w zadanym katalogu roboczym.
        cwd może być ścieżką względną lub absolutną.
        """
        exec_path = os.path.abspath(cwd or ".")

        if not os.path.isdir(exec_path):
            return {
                "ok": False,
                "stdout": "",
                "stderr": f"❌ Katalog roboczy nie istnieje: {exec_path}",
                "exit_code": -1
            }

        print(f"🛠️  Uruchamiam komendę: `{command}` (cwd={exec_path})")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=exec_path,
                timeout=timeout
            )
            return {
                "ok": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "stdout": "",
                "stderr": "⏰ Timeout (komenda trwała zbyt długo)",
                "exit_code": -1
            }

        except Exception as e:
            return {
                "ok": False,
                "stdout": "",
                "stderr": f"❌ Błąd uruchamiania: {str(e)}",
                "exit_code": -1
            }
