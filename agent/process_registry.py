import subprocess
from typing import List

class ProcessRegistry:
    def __init__(self):
        self._processes: List[subprocess.Popen] = []

    def register(self, process: subprocess.Popen):
        self._processes.append(process)

    def kill_all(self):
        for proc in self._processes:
            if proc.poll() is None:  # jeśli nadal żyje
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    proc.kill()
        self._processes.clear()
    
    def has_active_processes(self) -> bool:
        return any(proc.poll() is None for proc in self._processes)

# Singleton instance
process_registry = ProcessRegistry()
