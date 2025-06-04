"""
Process Manager - Lean version focused only on process management
Cleanup delegated to ProcessCleaner
"""
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional
import os
import psutil

# Import systemu logowania i cleanera
from logger import get_log_hub, LogLevel
from registry.process_cleaner import ProcessCleaner, quick_cleanup


class ProcessManager:
    """Lean Process Manager - tylko zarządzanie procesami, cleanup delegowany"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ProcessManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.processes: Dict[str, subprocess.Popen] = {}
        self.process_threads: Dict[str, threading.Thread] = {}
        self.running = False

        self.log_hub = get_log_hub()
        self.cleaner = ProcessCleaner(self.log_hub)

        self.poetry_commands = {
            "agent": ["poetry", "run", "agent"],
            "analyser": ["poetry", "run", "analyser-watch", "--mode", "watch"],
            "synthetiser": ["poetry", "run", "synthetiser", "--mode", "watch"]
        }
    
    def start_poetry_process(self, name: str, cmd: List[str], working_dir: Optional[str] = None) -> bool:
        """Uruchamia proces przez poetry"""
        if name in self.processes:
            self.log_hub.warn("MANAGER", f"Process {name} already running")
            return False
        
        try:
            self.log_hub.info("MANAGER", f"Starting {name}...")
            
            if working_dir:
                self.log_hub.debug("MANAGER", f"Starting {name} in directory: {working_dir}")
            
            # Uruchom proces przez poetry z encoding handling
            process = subprocess.Popen(
                cmd,  # ["poetry", "run", "agent"]
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding='utf-8',
                errors='replace',
                env={"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", **dict(__import__('os').environ)}
            )
            
            self.processes[name] = process
            self.log_hub.info("MANAGER", f"{name} started (PID: {process.pid})" + 
                             (f" in {working_dir}" if working_dir else ""))
            
            # Uruchom wątek do czytania output
            thread = threading.Thread(
                target=self._read_process_output,
                args=(name, process),
                daemon=True
            )
            thread.start()
            self.process_threads[name] = thread
            
            return True
            
        except Exception as e:
            self.log_hub.error("MANAGER", f"Failed to start {name}: {e}")
            return False
    
    def _read_process_output(self, name: str, process: subprocess.Popen) -> None:
        """Czyta output z procesu i przekazuje do GlobalLogHub"""
        try:
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    clean_line = line.strip()
                    # Przekaż bezpośrednio do GlobalLogHub
                    self.log_hub.info(name.upper(), clean_line)
                    
            # Sprawdź kod wyjścia
            return_code = process.wait()
            if return_code != 0:
                self.log_hub.error("MANAGER", f"{name} exited with code {return_code}")
            else:
                self.log_hub.info("MANAGER", f"{name} finished successfully")
                
        except Exception as e:
            self.log_hub.error("MANAGER", f"Error reading {name} output: {e}")
        finally:
            # Auto-cleanup po zakończeniu procesu
            self._cleanup_finished_process(name)
    
    def _cleanup_finished_process(self, name: str) -> None:
        """Czyści zakończony proces z rejestrów"""
        if name in self.processes:
            del self.processes[name]
        if name in self.process_threads:
            del self.process_threads[name]
        
        self.log_hub.debug("MANAGER", f"Cleaned up finished process {name}")
    
    def send_to_agent(self, prompt: str) -> bool:
        """Wysyła prompt do agenta przez stdin"""
        if "agent" not in self.processes:
            self.log_hub.warn("MANAGER", "Agent process not running")
            return False
        
        process = self.processes["agent"]
        
        # Sprawdź czy proces jeszcze żyje
        if process.poll() is not None:
            self.log_hub.error("MANAGER", "Agent process has terminated")
            return False
        
        try:
            # Wyślij prompt z nową linią
            process.stdin.write(prompt + "\n")
            process.stdin.flush()
            
            # Zaloguj wysłanie
            self.log_hub.info("MANAGER", f"Prompt sent to agent: {prompt}")
            
            return True
            
        except Exception as e:
            self.log_hub.error("MANAGER", f"Failed to send prompt to agent: {e}")
            return False
    
    def start_all(self) -> None:
        """Uruchamia wszystkie skonfigurowane procesy"""
        if self.running:
            self.log_hub.warn("MANAGER", "Processes already running")
            return
        
        self.running = True
        self.log_hub.group_start("MANAGER", "Starting all processes")
        
        success_count = 0
        for name, cmd in self.poetry_commands.items():
            if self.start_poetry_process(name, cmd, "."):
                success_count += 1
                # Krótka przerwa między uruchamianiem
                time.sleep(2)
        
        self.log_hub.group_end("MANAGER", f"Started {success_count}/{len(self.poetry_commands)} processes")
    
    def stop_process(self, name: str) -> bool:
        """Zatrzymuje pojedynczy proces używając cleanera"""
        if name not in self.processes:
            self.log_hub.warn("MANAGER", f"Process {name} not running")
            return False
        
        try:
            self.log_hub.info("MANAGER", f"Stopping {name}...")
            
            # Użyj cleaner do graceful shutdown
            process = self.processes[name]
            success = self.cleaner.cleanup_single_process(name, process)
            
            if success:
                # Usuń z rejestrów po udanym zamknięciu
                if name in self.processes:
                    del self.processes[name]
                if name in self.process_threads:
                    # Thread powinien się zakończyć automatycznie po zamknięciu procesu
                    thread = self.process_threads[name]
                    thread.join(timeout=2)  # Krótki timeout
                    del self.process_threads[name]
                
                self.log_hub.info("MANAGER", f"{name} stopped successfully")
                return True
            else:
                self.log_hub.error("MANAGER", f"Failed to stop {name}")
                return False
            
        except Exception as e:
            self.log_hub.error("MANAGER", f"Error stopping {name}: {e}")
            return False
    
    def stop_all(self) -> None:
        """Zatrzymuje wszystkie procesy używając ProcessCleaner"""
        if not self.running:
            self.log_hub.warn("MANAGER", "Already stopped")
            return
        
        self.log_hub.info("MANAGER", "Initiating complete shutdown...")
        
        # Deleguj do ProcessCleaner
        cleanup_report = self.cleaner.cleanup_all(self.processes, self.process_threads)
        
        # Wyczyść kolekcje po cleanup
        self.processes.clear()
        self.process_threads.clear()
        self.running = False
        
        # Log wyników
        if cleanup_report.errors:
            self.log_hub.warn("MANAGER", f"Shutdown completed with {len(cleanup_report.errors)} errors")
            for error in cleanup_report.errors:
                self.log_hub.error("MANAGER", f"Shutdown error: {error}")
        else:
            self.log_hub.info("MANAGER", f"Clean shutdown completed in {cleanup_report.cleanup_time:.2f}s")
        
        # Alert o zombie procesach jeśli są
        if cleanup_report.zombie_pids:
            pids_str = ', '.join(str(pid) for pid in cleanup_report.zombie_pids)
            self.log_hub.warn("MANAGER", f"Manual cleanup needed for PIDs: {pids_str}")
    
    def restart_process(self, name: str) -> bool:
        """Restartuje konkretny proces"""
        self.log_hub.info("MANAGER", f"Restarting {name}...")
        
        if name not in self.poetry_commands:
            self.log_hub.error("MANAGER", f"Unknown process: {name}")
            return False
        
        # Stop and start
        self.stop_process(name)
        time.sleep(1)  # Krótka przerwa
        return self.start_poetry_process(name, self.poetry_commands[name], ".")
    
    def emergency_stop_all(self) -> None:
        """Emergency stop wszystkich procesów - bez graceful shutdown"""
        self.log_hub.warn("MANAGER", "EMERGENCY STOP INITIATED")
        
        from registry.process_cleaner import emergency_kill_all
        killed_pids = emergency_kill_all(self.processes)
        
        # Force clear everything
        self.processes.clear()
        self.process_threads.clear()
        self.running = False
        
        self.log_hub.warn("MANAGER", f"Emergency stop complete - killed {len(killed_pids)} processes")
    
    # === Status and utility methods ===
    
    def get_running_processes(self) -> List[str]:
        """Zwraca listę uruchomionych procesów"""
        return [name for name, process in self.processes.items() 
                if process.poll() is None]
    
    def is_running(self, name: str) -> bool:
        """Sprawdza czy proces jest uruchomiony"""
        return name in self.processes and self.processes[name].poll() is None
    
    def get_status(self) -> Dict[str, str]:
        """Zwraca status wszystkich procesów dla ProcessFooter"""
        status = {}
        
        for process_name in self.poetry_commands.keys():
            if self.is_running(process_name):
                status[process_name] = "running"
            else:
                status[process_name] = "stopped"
        
        return status
    
    def get_process_info(self, name: str) -> Optional[Dict]:
        """Zwraca szczegółowe info o procesie"""
        if name not in self.processes:
            return None
        
        process = self.processes[name]
        thread = self.process_threads.get(name)
        
        return {
            "name": name,
            "pid": process.pid,
            "running": process.poll() is None,
            "exit_code": process.poll(),
            "thread_alive": thread.is_alive() if thread else False,
            "command": self.poetry_commands.get(name, [])
        }
    
    def get_system_status(self) -> Dict:
        """Zwraca pełny status systemu"""
        return {
            "manager_running": self.running,
            "total_processes": len(self.processes),
            "active_processes": len(self.get_running_processes()),
            "active_threads": len([t for t in self.process_threads.values() if t.is_alive()]),
            "total_system_threads": threading.active_count(),
            "processes": {name: self.get_process_info(name) for name in self.processes.keys()}
        }
    
    def start_custom_process(
        self,
        name: str,
        cmd: List[str],
        working_dir: str = ".",
        detached: bool = False,
        shell: bool = False,
        creation_flags: int = 0,
        preexec_fn=None
    ) -> bool:
        """
        Uruchamia dowolny proces (np. dev server) i rejestruje jego potomne procesy.

        Args:
            name: Nazwa procesu do rejestracji
            cmd: Lista komend lub string jeśli shell=True
            working_dir: Katalog roboczy
            detached: Czy uruchamiać jako proces w tle (bez logów)
            shell: Czy używać shella
            creation_flags: np. CREATE_NEW_PROCESS_GROUP dla Windows
            preexec_fn: np. os.setsid dla Linux/Mac
        """
        if name in self.processes:
            self.log_hub.warn("MANAGER", f"Process {name} already running")
            return False

        try:
            self.log_hub.info("MANAGER", f"Starting custom process {name}...")

            if working_dir:
                self.log_hub.debug("MANAGER", f"Working directory: {working_dir}")

            if detached:
                stdout = subprocess.PIPE
                stderr = subprocess.STDOUT
                stdin = subprocess.DEVNULL
                start_new_session = False  # <- kluczowe
                bufsize = 1
                text = True
                encoding = "utf-8"
                errors = "replace"
            else:
                stdout = subprocess.PIPE
                stderr = subprocess.STDOUT
                stdin = subprocess.PIPE
                start_new_session = False
                bufsize = 1
                text = True
                encoding = "utf-8"
                errors = "replace"

            env = {
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
                **os.environ
            }

            process = subprocess.Popen(
                cmd,
                cwd=working_dir,
                stdout=stdout,
                stderr=stderr,
                stdin=stdin,
                text=not detached,
                shell=shell,
                start_new_session=start_new_session,
                creationflags=creation_flags,
                preexec_fn=preexec_fn,
                bufsize=1 if not detached else 0,
                encoding='utf-8' if not detached else None,
                errors='replace' if not detached else None,
                env=env
            )

            self.processes[name] = process
            self.log_hub.info("MANAGER", f"{name} started (PID: {process.pid})")

            # Rejestruj dzieci (jeśli detached – np. dev-server spawnuje node itp.)
            try:
                proc = psutil.Process(process.pid)
                children = proc.children(recursive=True)
                for child in children:
                    child_key = f"{name}_child_{child.pid}"
                    self.processes[child_key] = child
                    self.log_hub.debug("MANAGER", f"Registered child process: {child_key}")
            except Exception as e:
                self.log_hub.warn("MANAGER", f"Failed to inspect child processes: {e}")

            # Czytaj output tylko jeśli nie jest detached
            if not detached:
                thread = threading.Thread(
                    target=self._read_process_output,
                    args=(name, process),
                    daemon=True
                )
                thread.start()
                self.process_threads[name] = thread

            return True

        except Exception as e:
            self.log_hub.error("MANAGER", f"Failed to start custom process {name}: {e}")
            return False