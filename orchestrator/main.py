#!/usr/bin/env python3
"""
start.py - Python Orchestrator using ProcessManager with tmux terminal split
Uruchamia analyser/synthetiser w tle, logi w górnym panelu, agent interactive w dolnym
"""

import os
import sys
import signal
import subprocess
import time
import atexit
import shutil
from pathlib import Path

# Setup encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

# Create output directory
Path("output/logs").mkdir(parents=True, exist_ok=True)

# Import ProcessManager and logging
from registry.process_manager import ProcessManager
from logger import get_log_hub

# Global manager instance
manager = None
log_hub = get_log_hub()

# Register orchestrator module
log_hub.register_module("ORCHESTRATOR", "🎯", "blue")

def check_tmux_available():
    """Sprawdź czy tmux jest dostępny"""
    return shutil.which("tmux") is not None

def start_with_tmux():
    """Uruchom aplikację w tmux z podziałem terminala"""
    session_name = "agent-session"
    
    # Zabij istniejącą sesję jeśli istnieje
    subprocess.run(["tmux", "kill-session", "-t", session_name], 
                  capture_output=True, check=False)
    
    try:
        # Utwórz nową sesję w tle
        log_hub.info("ORCHESTRATOR", "Creating tmux session...")
        subprocess.run(["tmux", "new-session", "-d", "-s", session_name], check=True)
        
        # Podziel okno: 70% góra (logi), 30% dół (interactive)
        log_hub.info("ORCHESTRATOR", "Splitting terminal...")
        subprocess.run(["tmux", "split-window", "-v", "-p", "30", "-t", session_name], check=True)
        
        # Górny panel - logi (background processes)
        log_hub.info("ORCHESTRATOR", "Starting background processes in upper panel...")
        subprocess.run(["tmux", "select-pane", "-t", f"{session_name}:0.0"], check=True)
        
        # Uruchom orchestrator w górnym panelu (bez interactive agenta)
        cmd_upper = f"cd '{os.getcwd()}' && python -c \"" \
                   f"from orchestrator.start import start_background_only; " \
                   f"start_background_only()\""
        subprocess.run(["tmux", "send-keys", "-t", f"{session_name}:0.0", cmd_upper, "Enter"], check=True)
        
        # Dolny panel - interactive agent
        log_hub.info("ORCHESTRATOR", "Starting interactive agent in lower panel...")
        subprocess.run(["tmux", "select-pane", "-t", f"{session_name}:0.1"], check=True)
        
        # Krótka pauza żeby background procesy się uruchomiły
        time.sleep(3)
        
        cmd_lower = f"cd '{os.getcwd()}' && poetry run agent"
        subprocess.run(["tmux", "send-keys", "-t", f"{session_name}:0.1", cmd_lower, "Enter"], check=True)
        
        # Ustaw focus na dolny panel (interactive)
        subprocess.run(["tmux", "select-pane", "-t", f"{session_name}:0.1"], check=True)
        
        log_hub.info("ORCHESTRATOR", "Attaching to tmux session...")
        log_hub.info("ORCHESTRATOR", "Use Ctrl+B then D to detach, Ctrl+C to stop")
        
        # Attach do sesji
        subprocess.run(["tmux", "attach-session", "-t", session_name])
        
        return 0
        
    except subprocess.CalledProcessError as e:
        log_hub.error("ORCHESTRATOR", f"Failed to setup tmux session: {e}")
        return 1
    except KeyboardInterrupt:
        log_hub.info("ORCHESTRATOR", "Interrupted - cleaning up tmux session...")
        subprocess.run(["tmux", "kill-session", "-t", session_name], 
                      capture_output=True, check=False)
        return 0

def start_background_only():
    """Uruchom tylko background procesy (dla górnego panelu tmux)"""
    global manager
    
    # Setup signal handling dla background procesów
    signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ignoruj Ctrl+C w background
    signal.signal(signal.SIGTERM, lambda s, f: cleanup_processes())
    
    # Initialize ProcessManager
    manager = ProcessManager()
    
    log_hub.info("ORCHESTRATOR", "Starting background processes (analyser + synthetiser)...")
    
    # Start background processes
    manager.start_all()
    
    # Check status
    running_processes = manager.get_running_processes()
    if running_processes:
        log_hub.info("ORCHESTRATOR", f"Background processes running: {', '.join(running_processes)}")
        log_hub.info("ORCHESTRATOR", "Background logs will appear here...")
        
        # Trzymaj proces żywy i wyświetlaj logi
        try:
            while True:
                time.sleep(1)
                # Sprawdź czy procesy nadal działają
                if not manager.get_running_processes():
                    log_hub.warn("ORCHESTRATOR", "All background processes stopped")
                    break
        except:
            pass
    else:
        log_hub.error("ORCHESTRATOR", "No background processes started")
    
    cleanup_processes()

def cleanup_processes():
    """Clean up all processes using ProcessManager"""
    global manager
    if manager:
        log_hub.warn("ORCHESTRATOR", "Shutting down all processes...")
        manager.stop_all()
        log_hub.info("ORCHESTRATOR", "All processes stopped")

def signal_handler(signum, frame):
    """Handle Ctrl+C"""
    log_hub.warn("ORCHESTRATOR", "Interrupt received - cleaning up...")
    cleanup_processes()
    sys.exit(0)

def main():
    """Main orchestrator function"""
    global manager
    
    log_hub.info("ORCHESTRATOR", "Starting Agent App Orchestrator")
    
    # Sprawdź czy tmux jest dostępny
    if check_tmux_available():
        log_hub.info("ORCHESTRATOR", "tmux detected - using split terminal mode")
        return start_with_tmux()
    else:
        log_hub.warn("ORCHESTRATOR", "tmux not available - falling back to single terminal mode")
        return start_single_terminal()

def start_single_terminal():
    """Fallback - uruchom w pojedynczym terminalu (stara logika)"""
    global manager
    
    # Setup signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_processes)
    
    # Initialize ProcessManager
    manager = ProcessManager()
    
    log_hub.info("ORCHESTRATOR", "Starting background processes...")
    
    # Start background processes (analyser + synthetiser)
    manager.start_all()
    
    # Give processes time to start
    time.sleep(3)
    
    # Check what actually started
    running_processes = manager.get_running_processes()
    if not running_processes:
        log_hub.error("ORCHESTRATOR", "No background processes started - exiting")
        return 1
    
    log_hub.info("ORCHESTRATOR", f"Started {len(running_processes)} background processes: {', '.join(running_processes)}")
    
    # Show status
    log_hub.info("ORCHESTRATOR", "Starting agent in foreground...")
    log_hub.info("ORCHESTRATOR", "Background processes running. Use Ctrl+C to stop all.")
    log_hub.info("ORCHESTRATOR", "Background processes managed by ProcessManager")
    
    try:
        # Start agent in foreground - bez przechwytywania output
        result = subprocess.run(
            ["poetry", "run", "agent"],
            cwd=".",
            stdout=None,  # Pozwól na bezpośredni output do konsoli
            stderr=None   # Pozwól na bezpośredni output do konsoli
        )
        
        log_hub.info("ORCHESTRATOR", "Agent finished")
        return result.returncode
        
    except KeyboardInterrupt:
        # Handled by signal_handler
        return 0
    except Exception as e:
        log_hub.error("ORCHESTRATOR", f"Error running agent: {e}")
        return 1
    finally:
        cleanup_processes()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)