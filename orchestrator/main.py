#!/usr/bin/env python3
"""
start.py - Simplified Python Orchestrator using ProcessManager
Uruchamia analyser/synthetiser w tle, następnie agent interactive w tym samym terminalu
"""

import os
import sys
import signal
import subprocess
import time
import atexit
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
    
    print("🎯 Agent App Orchestrator")
    print("=" * 50)
    
    log_hub.info("ORCHESTRATOR", "Starting Agent App Orchestrator")
    
    # Setup signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_processes)
    
    # Initialize ProcessManager
    print("📦 Initializing ProcessManager...")
    manager = ProcessManager()
    
    print("🚀 Starting background processes...")
    log_hub.info("ORCHESTRATOR", "Starting background processes...")
    
    # Start background processes (analyser + synthetiser)
    manager.start_all()
    
    print("⏳ Waiting for processes to initialize...")
    # Give processes time to start with progress indicator
    for i in range(3):
        time.sleep(1)
        print(f"   {i+1}/3 seconds...")
    
    # Check what actually started
    running_processes = manager.get_running_processes()
    if not running_processes:
        print("❌ No background processes started - exiting")
        log_hub.error("ORCHESTRATOR", "No background processes started - exiting")
        return 1
    
    print(f"✅ Started {len(running_processes)} background processes:")
    for process in running_processes:
        print(f"   • {process}")
    
    log_hub.info("ORCHESTRATOR", f"Started {len(running_processes)} background processes: {', '.join(running_processes)}")
    
    # Show status
    print("🤖 Starting interactive agent...")
    print("   Use Ctrl+C to stop all processes")
    print("=" * 50)
    
    log_hub.info("ORCHESTRATOR", "Starting agent in foreground...")
    log_hub.info("ORCHESTRATOR", "Background processes running. Use Ctrl+C to stop all.")
    
    try:
        # Start agent in foreground
        result = subprocess.run(
            ["poetry", "run", "agent"],
            cwd=".",
            stdout=None,  # Direct output to console
            stderr=None   # Direct output to console
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