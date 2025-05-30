import os
import psutil  # ✅ Dodaj psutil dla ubijania dzieci
# Wymuś UTF-8 na Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

import subprocess
import threading
import queue
import time

import json
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# ✅ Dodaj registry
from registry.process_registry import process_registry

class ProcessStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"

@dataclass
class LogEntry:
    source: str  # "agent", "analyser", "synthetiser"
    message: str
    timestamp: float
    level: str = "info"  # "info", "error", "warning"

class ProcessManager:
    """Zarządza wszystkimi procesami i centralizuje logi"""
    
    def __init__(self):
        self.processes: Dict[str, subprocess.Popen] = {}
        self.process_status: Dict[str, ProcessStatus] = {}
        self.log_queue = queue.Queue()
        self.log_handlers: list[Callable[[LogEntry], None]] = []
        
        # Threading dla monitorowania procesów
        self.monitor_thread = None
        self.stop_monitoring = threading.Event()
        
        # Ścieżki i komendy
        self.commands = {
            "agent": ["poetry", "run", "agent"],
            "analyser": ["poetry", "run", "analyser-watch", "--mode", "watch"],
            "synthetiser": ["poetry", "run", "synthetiser", "--mode", "watch"]
        }
        
        # Inicjalne statusy
        for name in self.commands:
            self.process_status[name] = ProcessStatus.STOPPED
    
    def get_project_root(self) -> Path:
        """Zwraca katalog główny projektu (root/)"""
        # Z root/gui/process_manager.py wracamy do root/
        return Path(__file__).parent.parent
    
    def add_log_handler(self, handler: Callable[[LogEntry], None]):
        """Dodaje handler do obsługi logów"""
        self.log_handlers.append(handler)
    
    def _emit_log(self, source: str, message: str, level: str = "info"):
        """Emituje log do wszystkich handlerów"""
        entry = LogEntry(source, message, time.time(), level)
        self.log_queue.put(entry)
        
        for handler in self.log_handlers:
            try:
                handler(entry)
            except Exception as e:
                print(f"Error in log handler: {e}")
    
    def start_process(self, name: str) -> bool:
        """Uruchamia konkretny proces"""
        if name not in self.commands:
            self._emit_log("manager", f"Unknown process: {name}", "error")
            return False
        
        if self.process_status[name] == ProcessStatus.RUNNING:
            self._emit_log("manager", f"{name} already running", "warning")
            return True
        
        try:
            self.process_status[name] = ProcessStatus.STARTING
            self._emit_log("manager", f"Starting {name}...")
            
            cmd = self.commands[name]
            project_root = str(self.get_project_root())  # ✅ Użyj root/ zamiast gui/
            
            # Loguj CWD dla debugowania
            self._emit_log("manager", f"Starting {name} in directory: {project_root}")
            
            # Agent z pipe'ami - teraz powinien działać
            if name == "agent":
                proc = subprocess.Popen(
                    cmd,
                    cwd=project_root,
                    stdout=subprocess.PIPE,  # ✅ Logi do GUI
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                    env=os.environ.copy(),
                    bufsize=1,
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace'
                )
            else:
                proc = subprocess.Popen(
                    cmd,
                    cwd=project_root,  # ✅ Poprawiony CWD
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=os.environ.copy(),
                    bufsize=1,
                    universal_newlines=True,
                    encoding='utf-8',
                    errors='replace'
                )
            
            self.processes[name] = proc
            process_registry.register(proc)  # ✅ Rejestruj proces
            
            # Uruchom monitoring tego procesu (dla wszystkich procesów)
            self._start_process_monitoring(name)
            
            self.process_status[name] = ProcessStatus.RUNNING
            self._emit_log("manager", f"{name} started (PID: {proc.pid}) in {project_root}")
            
            return True
            
        except Exception as e:
            self.process_status[name] = ProcessStatus.ERROR
            self._emit_log("manager", f"Failed to start {name}: {e}", "error")
            return False
    
    def stop_process(self, name: str) -> bool:
        """Zatrzymuje konkretny proces"""
        if name not in self.processes:
            return True
        
        try:
            proc = self.processes[name]
            if proc.poll() is None:  # Proces jeszcze żyje
                proc.terminate()
                
                # Czekaj na zakończenie
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            
            del self.processes[name]
            self.process_status[name] = ProcessStatus.STOPPED
            self._emit_log("manager", f"{name} stopped")
            return True
            
        except Exception as e:
            self._emit_log("manager", f"Error stopping {name}: {e}", "error")
            return False
    
    def start_all(self):
        """Uruchamia wszystkie procesy w odpowiedniej kolejności"""
        # Najpierw agent
        if self.start_process("agent"):
            time.sleep(2)  # Czekaj na agenta
            
            # Potem analyser
            if self.start_process("analyser"):
                time.sleep(3)  # Czekaj na analyser
                
                # Na końcu synthetiser
                self.start_process("synthetiser")
    
    def stop_all(self):
        """Zatrzymuje wszystkie procesy"""
        # ✅ Debug - sprawdź czy się wywołuje
        print("🛑 DEBUG: stop_all() called!")
        self._emit_log("manager", "🛑 Stopping all processes via registry...")
        
        # Sprawdź ile procesów jest aktywnych
        active_count = len([p for p in self.processes.values() if p.poll() is None])
        print(f"🛑 DEBUG: Active processes: {active_count}")
        self._emit_log("manager", f"Active processes before kill: {active_count}")
        
        # ✅ Ubij drzewo procesów (parent + dzieci)
        self._kill_process_trees()
        
        process_registry.kill_all()
        
        # Sprawdź czy faktycznie umarły
        time.sleep(1)
        remaining = len([p for p in self.processes.values() if p.poll() is None])
        print(f"🛑 DEBUG: Remaining processes after kill: {remaining}")
        self._emit_log("manager", f"Remaining processes after kill: {remaining}")
        
        # Zatrzymaj monitoring
        self.stop_monitoring.set()
        
        # Wyczyść lokalne struktury
        for name in list(self.processes.keys()):
            self.process_status[name] = ProcessStatus.STOPPED
            self._emit_log("manager", f"{name} stopped via registry")
        
        self.processes.clear()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
    
    def _kill_process_trees(self):
        """Ubija procesy wraz z ich dziećmi (dev server problem)"""
        for name, proc in self.processes.items():
            if proc.poll() is None:  # Proces żyje
                try:
                    # Użyj psutil do ubicia całego drzewa
                    parent = psutil.Process(proc.pid)
                    children = parent.children(recursive=True)
                    
                    # Ubij dzieci
                    for child in children:
                        try:
                            child.terminate()
                        except psutil.NoSuchProcess:
                            pass
                    
                    # Ubij rodzica
                    parent.terminate()
                    
                    # Poczekaj na zakończenie
                    gone, alive = psutil.wait_procs(children + [parent], timeout=3)
                    
                    # Jeśli coś zostało, zabij na siłę
                    for p in alive:
                        try:
                            p.kill()
                        except psutil.NoSuchProcess:
                            pass
                    
                    self._emit_log("manager", f"Killed process tree for {name} (PID: {proc.pid})")
                    
                except (psutil.NoSuchProcess, ProcessLookupError):
                    # Proces już nie istnieje
                    pass
                except Exception as e:
                    self._emit_log("manager", f"Error killing process tree for {name}: {e}", "error")
    
    def _start_process_monitoring(self, name: str):
        """Uruchamia monitoring pojedynczego procesu"""
        def monitor():
            proc = self.processes.get(name)
            if not proc:
                return
            
            # Monitor stdout
            def read_stdout():
                for line in iter(proc.stdout.readline, ''):
                    if not line:
                        break
                    self._emit_log(name, line.strip())
            
            # Monitor stderr  
            def read_stderr():
                for line in iter(proc.stderr.readline, ''):
                    if not line:
                        break
                    self._emit_log(name, line.strip(), "error")
            
            # Uruchom wątki do czytania output'u
            stdout_thread = threading.Thread(target=read_stdout, daemon=True)
            stderr_thread = threading.Thread(target=read_stderr, daemon=True)
            
            stdout_thread.start()
            stderr_thread.start()
            
            # Monitoruj status procesu
            while not self.stop_monitoring.is_set():
                if proc.poll() is not None:
                    # Proces zakończył się
                    self.process_status[name] = ProcessStatus.STOPPED
                    self._emit_log("manager", f"{name} exited with code {proc.returncode}")
                    break
                time.sleep(0.5)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def get_status(self) -> Dict[str, str]:
        """Zwraca status wszystkich procesów"""
        return {name: status.value for name, status in self.process_status.items()}
    
    def send_to_agent(self, data: str) -> bool:
        """Wysyła dane do agenta przez stdin"""
        if "agent" not in self.processes:
            return False
        
        try:
            proc = self.processes["agent"]
            if proc.poll() is None:  # Proces żyje
                proc.stdin.write(data + "\n")
                proc.stdin.flush()
                return True
        except Exception as e:
            self._emit_log("manager", f"Error sending to agent: {e}", "error")
        
        return False
    
    def get_logs(self) -> list[LogEntry]:
        """Pobiera wszystkie logi z kolejki"""
        logs = []
        while not self.log_queue.empty():
            try:
                logs.append(self.log_queue.get_nowait())
            except queue.Empty:
                break
        return logs
    
    def test_log(self):
        """Test - emituje testowy log"""
        self._emit_log("test", "🧪 Test log message - czy to widać?")