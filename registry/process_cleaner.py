"""
Process Cleaner - Dedykowany moduł do zamykania i czyszczenia procesów
"""
import subprocess
import threading
import time
from typing import Dict, List, Optional, NamedTuple


class CleanupReport(NamedTuple):
    """Raport z procesu czyszczenia"""
    total_processes: int
    active_before: int
    zombie_before: int
    remaining_alive: int
    zombie_after: int
    zombie_pids: List[int]
    cleanup_time: float
    threads_cleaned: int
    errors: List[str]


class ProcessCleaner:
    """Dedykowany cleaner do zamykania procesów i threadów"""
    
    def __init__(self, log_hub=None):
        self.log_hub = log_hub
    
    def cleanup_all(self, 
                   processes: Dict[str, subprocess.Popen], 
                   process_threads: Dict[str, threading.Thread],
                   timeout: int = 2,  # Skrócone z 5s na 2s
                   thread_timeout: int = 1) -> CleanupReport:  # Skrócone z 3s na 1s
        """
        Kompletne czyszczenie wszystkich procesów i threadów
        
        Args:
            processes: Dict procesów do zamknięcia
            process_threads: Dict threadów do zamknięcia
            timeout: Timeout dla graceful shutdown procesów
            thread_timeout: Timeout dla join threadów
            
        Returns:
            CleanupReport z detalami procesu czyszczenia
        """
        print("🔄 Starting complete cleanup sequence...")
        start_time = time.time()
        errors = []
        
        if self.log_hub:
            self.log_hub.group_start("CLEANER", "Complete system cleanup")
        
        # Analiza stanu przed cleanup
        pre_cleanup = self._analyze_processes(processes)
        self._print_pre_cleanup_status(processes)
        
        try:
            # 1. Zamknij wszystkie procesy
            print("🧹 Phase 1: Shutting down processes...")
            self._shutdown_all_processes(processes, timeout, errors)
            
            # 2. Cleanup threadów
            print("🧵 Phase 2: Cleaning up threads...")
            threads_cleaned = self._cleanup_all_threads(process_threads, thread_timeout, errors)
            
            # 3. Final analysis
            post_cleanup = self._analyze_processes(processes)
            cleanup_time = time.time() - start_time
            
            # Stwórz raport
            report = CleanupReport(
                total_processes=pre_cleanup['total'],
                active_before=pre_cleanup['active'],
                zombie_before=pre_cleanup['zombie'],
                remaining_alive=post_cleanup['active'],
                zombie_after=post_cleanup['zombie'],
                zombie_pids=post_cleanup['zombie_pids'],
                cleanup_time=cleanup_time,
                threads_cleaned=threads_cleaned,
                errors=errors
            )
            
            self._print_cleanup_summary(report)
            
            if self.log_hub:
                status = "with errors" if errors else "successfully"
                self.log_hub.group_end("CLEANER", f"Cleanup completed {status} in {cleanup_time:.2f}s")
            
            return report
            
        except Exception as e:
            error_msg = f"Critical cleanup error: {e}"
            print(f"❌ {error_msg}")
            errors.append(error_msg)
            
            # Return partial report
            return CleanupReport(
                total_processes=pre_cleanup['total'],
                active_before=pre_cleanup['active'],
                zombie_before=pre_cleanup['zombie'],
                remaining_alive=len([p for p in processes.values() if p.poll() is None]),
                zombie_after=len([p for p in processes.values() if p.poll() is not None]),
                zombie_pids=[p.pid for p in processes.values() if p.poll() is not None],
                cleanup_time=time.time() - start_time,
                threads_cleaned=0,
                errors=errors
            )
    
    def cleanup_single_process(self, name: str, process: subprocess.Popen, timeout: int = 2) -> bool:  # Skrócone z 5s na 2s
        """
        Zamyka pojedynczy proces gracefully
        
        Returns:
            True jeśli proces został zamknięty, False w przypadku błędu
        """
        if process.poll() is not None:
            print(f"💀 Process {name} already dead (exit code: {process.poll()})")
            return True
        
        try:
            print(f"🤝 Graceful shutdown: {name} (PID {process.pid})")
            
            # Zamknij stdin przed terminacją
            if process.stdin and not process.stdin.closed:
                try:
                    process.stdin.close()
                except:
                    pass  # Ignore stdin close errors
            
            # Wyślij SIGTERM
            process.terminate()
            
            # Czekaj na graceful shutdown
            try:
                process.wait(timeout=timeout)
                print(f"✅ {name} terminated gracefully")
                return True
            except subprocess.TimeoutExpired:
                print(f"⚡ Timeout! Force killing {name} (PID {process.pid})")
                process.kill()
                process.wait()  # Clean up zombie
                print(f"💥 {name} force killed")
                return True
                
        except ProcessLookupError:
            print(f"👻 Process {name} disappeared during shutdown")
            return True  # Consider this success
        except Exception as e:
            print(f"❌ Error stopping {name}: {e}")
            try:
                process.kill()  # Last resort
                process.wait()
                return True
            except:
                return False
    
    def _analyze_processes(self, processes: Dict[str, subprocess.Popen]) -> Dict:
        """Analizuje stan procesów"""
        active = [p for p in processes.values() if p.poll() is None]
        zombie = [p for p in processes.values() if p.poll() is not None]
        
        return {
            'total': len(processes),
            'active': len(active),
            'zombie': len(zombie),
            'zombie_pids': [p.pid for p in zombie]
        }
    
    def _print_pre_cleanup_status(self, processes: Dict[str, subprocess.Popen]) -> None:
        """Wyświetla status przed cleanup"""
        analysis = self._analyze_processes(processes)
        
        print(f"📊 Pre-cleanup status:")
        print(f"   🟢 Active processes: {analysis['active']}")
        print(f"   🧟 Zombie processes: {analysis['zombie']}")
        print(f"   📈 Total processes: {analysis['total']}")
        
        for name, process in processes.items():
            status = "ALIVE" if process.poll() is None else f"DEAD ({process.poll()})"
            print(f"   📊 {name}: PID {process.pid} - {status}")
    
    def _shutdown_all_processes(self, processes: Dict[str, subprocess.Popen], 
                              timeout: int, errors: List[str]) -> None:
        """Zamyka wszystkie procesy równocześnie (parallel approach)"""
        if not processes:
            print("💀 No processes to shutdown")
            return
        
        process_list = list(processes.items())
        print(f"💀 Starting parallel shutdown of {len(process_list)} processes...")
        
        # FAZA 1: Wyślij SIGTERM do wszystkich równocześnie
        print("🤝 Phase 1: Sending SIGTERM to all processes...")
        alive_processes = []
        
        for name, process in process_list:
            if process.poll() is not None:
                print(f"💀 {name} already dead (exit code: {process.poll()})")
                continue
                
            try:
                print(f"🤝 Sending SIGTERM to {name} (PID {process.pid})")
                
                # Zamknij stdin przed terminacją
                if process.stdin and not process.stdin.closed:
                    try:
                        process.stdin.close()
                    except:
                        pass
                
                process.terminate()
                alive_processes.append((name, process))
                
            except ProcessLookupError:
                print(f"👻 Process {name} disappeared before terminate")
            except Exception as e:
                error_msg = f"Error terminating {name}: {e}"
                print(f"❌ {error_msg}")
                errors.append(error_msg)
        
        if not alive_processes:
            print("✅ All processes were already dead")
            return
        
        # FAZA 2: Czekaj na graceful shutdown wszystkich (parallel wait)
        print(f"⏳ Phase 2: Waiting up to {timeout}s for graceful shutdown...")
        start_time = time.time()
        check_interval = 0.1  # Sprawdzaj co 100ms
        
        while alive_processes and (time.time() - start_time) < timeout:
            # Sprawdź które procesy się zakończyły
            still_alive = []
            for name, process in alive_processes:
                if process.poll() is None:
                    still_alive.append((name, process))
                else:
                    print(f"✅ {name} terminated gracefully")
            
            alive_processes = still_alive
            
            if alive_processes:
                time.sleep(check_interval)
        
        # FAZA 3: Force kill survivors równocześnie
        if alive_processes:
            print(f"⚡ Phase 3: Force killing {len(alive_processes)} survivors...")
            
            for name, process in alive_processes:
                try:
                    print(f"💥 Force killing {name} (PID {process.pid})")
                    process.kill()
                except ProcessLookupError:
                    print(f"👻 Process {name} disappeared before kill")
                except Exception as e:
                    error_msg = f"Error force killing {name}: {e}"
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
            
            # Czekaj na cleanup zombie processes
            print("🧟 Cleaning up killed processes...")
            for name, process in alive_processes:
                try:
                    process.wait(timeout=1)  # Krótki timeout na cleanup
                    print(f"💥 {name} force killed successfully")
                except subprocess.TimeoutExpired:
                    error_msg = f"Process {name} didn't die after force kill"
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
                except Exception as e:
                    error_msg = f"Error waiting for {name} cleanup: {e}"
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
        else:
            print("🎉 All processes terminated gracefully - no force kill needed!")
        
        total_time = time.time() - start_time
        print(f"✅ Parallel shutdown complete in {total_time:.2f}s")
    
    def _cleanup_all_threads(self, process_threads: Dict[str, threading.Thread], 
                           timeout: int, errors: List[str]) -> int:
        """Cleanup wszystkich threadów"""
        if not process_threads:
            print("🧵 No threads to cleanup")
            return 0
        
        print(f"🧵 Cleaning up {len(process_threads)} threads...")
        
        alive_threads = [(name, thread) for name, thread in process_threads.items() 
                        if thread.is_alive()]
        
        if not alive_threads:
            print("🧵 All threads already dead")
            return len(process_threads)
        
        print(f"⏳ Waiting for {len(alive_threads)} threads to finish...")
        cleaned_count = 0
        
        for name, thread in alive_threads:
            print(f"   ⏳ Joining thread {name}...")
            thread.join(timeout=timeout)
            
            if thread.is_alive():
                # Daemon threads mogą się nie zakończyć - to OK
                if thread.daemon:
                    print(f"   🔄 Thread {name} is daemon - will exit with main process")
                    cleaned_count += 1  # Count as cleaned since it's daemon
                else:
                    error_msg = f"Thread {name} didn't stop cleanly (still alive)"
                    print(f"   ⚠️  {error_msg}")
                    errors.append(error_msg)
            else:
                print(f"   ✅ Thread {name} joined successfully")
                cleaned_count += 1
        
        # Check for non-daemon zombie threads
        still_alive = [name for name, thread in process_threads.items() 
                      if thread.is_alive() and not thread.daemon]
        
        if still_alive:
            print(f"⚠️  Non-daemon zombie threads: {still_alive}")
            print("   💡 These threads may need manual intervention")
        else:
            print("🧵 All critical threads cleaned up!")
        
        return cleaned_count
        
    def _print_cleanup_summary(self, report: CleanupReport) -> None:
        """Wyświetla podsumowanie cleanup z auto-killing zombie PIDs"""
        print("\n" + "="*50)
        print("✨ CLEANUP SUMMARY 🎉")
        print("="*50)
        
        print(f"⏱️  Total cleanup time: {report.cleanup_time:.2f}s")
        print(f"📊 Processes handled: {report.total_processes}")
        print(f"🧵 Threads cleaned: {report.threads_cleaned}")
        print(f"📈 Active threads remaining: {threading.active_count()}")
        
        if report.remaining_alive > 0:
            print(f"⚠️  Processes still alive: {report.remaining_alive}")
        
        if report.zombie_pids:
            print(f"🧟 Found {len(report.zombie_pids)} zombie PIDs")
            for pid in report.zombie_pids:
                print(f"   💀 PID {pid}")
            
            # Auto-kill zombies
            self._auto_kill_zombies(report.zombie_pids)
        else:
            print("🧟 No zombie processes - squeaky clean!")
        
        if report.errors:
            print(f"❌ Errors encountered: {len(report.errors)}")
            for error in report.errors:
                print(f"   ⚠️  {error}")
        else:
            print("✅ No errors - perfect cleanup!")
        
        print("="*50)
        print("🎯 All systems shutdown complete! Papa would be proud! 🎉")
        print("="*50)

    def _auto_kill_zombies(self, zombie_pids: List[int]) -> None:
        """Auto-kill zombie PIDs - Windows compatible"""
        import os
        import signal
        import sys
        
        print(f"🔪 Auto-killing {len(zombie_pids)} zombies...")
        
        for pid in zombie_pids:
            try:
                # Cross-platform process killing
                if sys.platform == "win32":
                    # Windows: użyj os.kill z SIGTERM lub subprocess
                    import subprocess
                    subprocess.run(["taskkill", "/F", "/PID", str(pid)], 
                                capture_output=True, check=False)
                    print(f"   ✅ Killed PID {pid} (Windows)")
                else:
                    # Unix: użyj SIGKILL
                    os.kill(pid, 0)  # Check existence
                    os.kill(pid, signal.SIGKILL)  # Kill
                    print(f"   ✅ Killed PID {pid} (Unix)")
                    
            except ProcessLookupError:
                print(f"   👻 PID {pid} already gone")
            except Exception as e:
                print(f"   ❌ Failed PID {pid}: {e}")
        
        print("🧽 Auto-cleanup complete!")


# Utility functions dla prostszego użycia
def quick_cleanup(processes: Dict[str, subprocess.Popen], 
                 process_threads: Dict[str, threading.Thread] = None,
                 log_hub=None) -> CleanupReport:
    """Quick cleanup function dla prostego użycia"""
    cleaner = ProcessCleaner(log_hub)
    return cleaner.cleanup_all(processes, process_threads or {})


def emergency_kill_all(processes: Dict[str, subprocess.Popen]) -> List[int]:
    """Emergency kill wszystkich procesów - bez graceful shutdown"""
    print("🚨 EMERGENCY KILL MODE - NO MERCY! 💀")
    killed_pids = []
    
    for name, process in processes.items():
        if process.poll() is None:  # Still alive
            try:
                print(f"💀 Emergency killing {name} (PID {process.pid})")
                process.kill()
                process.wait()
                killed_pids.append(process.pid)
                print(f"💥 {name} emergency killed")
            except Exception as e:
                print(f"❌ Failed to emergency kill {name}: {e}")
    
    print(f"🚨 Emergency kill complete - killed {len(killed_pids)} processes")
    return killed_pids
