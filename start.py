#!/usr/bin/env python3
"""
start.py - Python Orchestrator
Uruchamia analyser/synthetiser w tle, agent w foreground
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

# Global process tracking
background_processes = []

def print_colored(message, color='white'):
    """Print colored messages"""
    colors = {
        'red': '\033[0;31m',
        'green': '\033[0;32m',
        'yellow': '\033[1;33m',
        'blue': '\033[0;34m',
        'white': '\033[0m'
    }
    print(f"{colors.get(color, colors['white'])}{message}\033[0m")

def cleanup_processes():
    """Clean up all background processes"""
    if not background_processes:
        return
        
    print_colored("🛑 Shutting down background processes...", 'yellow')
    
    for proc in background_processes:
        if proc.poll() is None:  # Still running
            print_colored(f"  Stopping PID {proc.pid}...", 'yellow')
            try:
                proc.terminate()
            except:
                pass
    
    # Wait for graceful shutdown
    time.sleep(2)
    
    # Force kill if needed
    for proc in background_processes:
        if proc.poll() is None:
            print_colored(f"  Force killing PID {proc.pid}...", 'red')
            try:
                proc.kill()
            except:
                pass
    
    print_colored("✅ Background processes stopped", 'green')

def signal_handler(signum, frame):
    """Handle Ctrl+C"""
    print_colored("\n🛑 Interrupt received - cleaning up...", 'yellow')
    cleanup_processes()
    sys.exit(0)

def start_background_process(name, cmd, log_file):
    """Start a process in background with logging"""
    print_colored(f"🔧 Starting {name}...", 'blue')
    
    try:
        with open(log_file, 'w') as f:
            proc = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                shell=False,
                cwd="."
            )
        
        background_processes.append(proc)
        print_colored(f"✅ {name} started (PID: {proc.pid}) - logs: {log_file}", 'green')
        return True
        
    except Exception as e:
        print_colored(f"❌ Failed to start {name}: {e}", 'red')
        return False

def main():
    """Main orchestrator function"""
    print_colored("🎯 Starting Agent App Orchestrator", 'blue')
    print_colored("=" * 35, 'blue')
    
    # Setup signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    atexit.register(cleanup_processes)
    
    # Start background processes
    success_count = 0
    
    # Start analyser
    if start_background_process(
        "analyser", 
        ["poetry", "run", "analyser-watch", "--mode", "watch"],
        "output/logs/analyser.log"
    ):
        success_count += 1
        time.sleep(1)
    
    # Start synthetiser  
    if start_background_process(
        "synthetiser",
        ["poetry", "run", "synthetiser", "--mode", "watch"], 
        "output/logs/synthetiser.log"
    ):
        success_count += 1
        time.sleep(1)
    
    if success_count == 0:
        print_colored("❌ No background processes started - exiting", 'red')
        return 1
    
    # Show status
    print_colored("🚀 Starting agent in foreground...", 'blue')
    print_colored("💡 Background processes running. Use Ctrl+C to stop all.", 'yellow')
    print_colored("📝 Check logs: tail -f output/logs/analyser.log", 'yellow')
    print_colored("📝 Check logs: tail -f output/logs/synthetiser.log", 'yellow')
    print_colored("=" * 35, 'blue')
    
    try:
        # Start agent in foreground
        result = subprocess.run(
            ["poetry", "run", "agent"],
            cwd="."
        )
        
        print_colored("Agent finished", 'blue')
        return result.returncode
        
    except KeyboardInterrupt:
        # Handled by signal_handler
        return 0
    except Exception as e:
        print_colored(f"❌ Error running agent: {e}", 'red')
        return 1
    finally:
        cleanup_processes()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)