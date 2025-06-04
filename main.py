#!/usr/bin/env python3
"""
Root Main.py - Process Orchestrator
Zarządza wszystkimi procesami używając ProcessManager z registry
"""

import os
import sys
import signal
import time
import atexit
from pathlib import Path

# Ustaw encoding przed importami
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Upewnij się że katalog output istnieje
os.makedirs("output", exist_ok=True)

from registry.process_manager import ProcessManager
from logger import get_log_hub

# Globalne instancje
process_manager = None
log_hub = None
shutdown_initiated = False

def setup_logging():
    """Konfiguruje system logowania"""
    global log_hub
    log_hub = get_log_hub()
    
    def console_listener(entry):
        formatted = log_hub.format_entry(entry)
        print(formatted)
    
    log_hub.add_listener(console_listener)
    return log_hub

def signal_handler(signum, frame):
    """Handler dla sygnałów SIGINT/SIGTERM"""
    global shutdown_initiated
    
    if shutdown_initiated:
        log_hub.warn("MAIN", "Force shutdown requested - emergency stop")
        process_manager.emergency_stop_all()
        sys.exit(1)
    
    shutdown_initiated = True
    signal_name = "SIGINT" if signum == signal.SIGINT else f"Signal {signum}"
    log_hub.info("MAIN", f"🛑 {signal_name} received - initiating graceful shutdown...")
    
    graceful_shutdown()
    sys.exit(0)

def graceful_shutdown():
    """Graceful shutdown wszystkich procesów"""
    if process_manager:
        log_hub.info("MAIN", "🧹 Stopping all processes...")
        process_manager.stop_all()
        log_hub.info("MAIN", "✅ Shutdown complete")

def emergency_cleanup():
    """Emergency cleanup przy wyjściu z programu"""
    if process_manager and not shutdown_initiated:
        log_hub.warn("MAIN", "⚠️ Emergency cleanup on exit")
        process_manager.emergency_stop_all()

def wait_for_processes():
    """Oczekuje na zakończenie procesów lub przerwanie przez użytkownika"""
    log_hub.info("MAIN", "🔄 System running. Press Ctrl+C to stop gracefully, Ctrl+C twice for emergency stop")
    
    try:
        while True:
            # Sprawdź status procesów co 5 sekund
            running = process_manager.get_running_processes()
            
            if not running:
                log_hub.info("MAIN", "📭 All processes finished - shutting down")
                break
                
            time.sleep(5)
            
    except KeyboardInterrupt:
        # To zostanie przechwycone przez signal_handler
        pass

def start_default_processes():
    """Uruchamia domyślne procesy systemu"""
    log_hub.info("MAIN", "🚀 Starting default processes...")
    
    # Lista procesów do uruchomienia
    default_processes = [
        ("agent", ["poetry", "run", "agent"]),
        ("analyser", ["poetry", "run", "analyser-watch", "--mode", "watch"]),
        ("synthetiser", ["poetry", "run", "synthetiser", "--mode", "watch"])
    ]
    
    success_count = 0
    for name, cmd in default_processes:
        log_hub.info("MAIN", f"🔧 Starting {name}...")
        if process_manager.start_poetry_process(name, cmd, "."):
            success_count += 1
            log_hub.info("MAIN", f"✅ {name} started successfully")
            # Krótka przerwa między procesami
            time.sleep(2)
        else:
            log_hub.error("MAIN", f"❌ Failed to start {name}")
    
    log_hub.info("MAIN", f"📊 Started {success_count}/{len(default_processes)} processes")
    return success_count > 0

def main():
    """Główna funkcja orchestratora"""
    global process_manager
    
    # Setup
    log_hub = setup_logging()
    log_hub.info("MAIN", "🎯 Starting Process Orchestrator")
    
    # Zarejestruj signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Zarejestruj emergency cleanup
    atexit.register(emergency_cleanup)
    
    try:
        # Inicjalizuj ProcessManager (singleton)
        process_manager = ProcessManager()
        log_hub.info("MAIN", "🏗️ ProcessManager initialized")
        
        # Uruchom domyślne procesy
        if not start_default_processes():
            log_hub.error("MAIN", "❌ Failed to start any processes - exiting")
            return 1
        
        # Pokaż status
        status = process_manager.get_system_status()
        log_hub.info("MAIN", f"📈 System status: {status['active_processes']}/{status['total_processes']} processes active")
        
        # Oczekuj na zakończenie lub przerwanie
        wait_for_processes()
        
        # Graceful shutdown
        graceful_shutdown()
        return 0
        
    except Exception as e:
        log_hub.error("MAIN", f"💥 Fatal error: {e}")
        if process_manager:
            process_manager.emergency_stop_all()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)