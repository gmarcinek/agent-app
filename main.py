import subprocess
import os
import time
import atexit
from registry.process_registry import process_registry

def start_process(cmd, cwd=".", capture_output=True):
    print(f"🔧 Uruchamiam komendę: {' '.join(cmd)}")
    print(f"🔧 W katalogu: {os.path.abspath(cwd)}")
    
    if capture_output:
        proc = subprocess.Popen(
            cmd,
            cwd=os.path.abspath(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy(),
        )
    else:
        # Przekazanie stdin/stdout/stderr do terminala - tryb interaktywny
        proc = subprocess.Popen(
            cmd,
            cwd=os.path.abspath(cwd),
            stdin=None,
            stdout=None,
            stderr=None,
            text=True,
            env=os.environ.copy(),
        )
    process_registry.register(proc)
    print(f"🚀 Uruchomiono proces `{' '.join(cmd)}` (PID {proc.pid})")
    return proc

def cleanup():
    print("\n🧹 Sprzątanie procesów...")
    process_registry.kill_all()

atexit.register(cleanup)

def main():
    print("🚀 Uruchamiam główną aplikację...")
    
    # Sprawdź czy poetry działa
    try:
        result = subprocess.run(["poetry", "--version"], capture_output=True, text=True)
        print(f"🔧 Poetry: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ Błąd poetry: {e}")
        return

    # Komendy dla wszystkich procesów
    analyser_cmd = ["poetry", "run", "analyser-watch", "--mode", "watch"]
    synthetiser_cmd = ["poetry", "run", "synthetiser", "--mode", "watch"]
    agent_cmd = ["poetry", "run", "agent"]

    print("🔧 Uruchamiam agent...")
    # agent uruchamiamy w trybie interaktywnym - dziedziczy terminal (stdin/out/err)
    agent_process = start_process(agent_cmd, capture_output=False)
    
    print("🔧 Czekam 2 sekundy przed uruchomieniem analysera...")
    time.sleep(2)
    
    print("🔧 Uruchamiam analyser...")
    # analyser uruchamiamy bez przekierowania - będzie logował do konsoli
    analyser_process = start_process(analyser_cmd, capture_output=False)
    
    print("🔧 Czekam 3 sekundy przed uruchomieniem synthetiser...")
    time.sleep(3)
    
    print("🔧 Uruchamiam synthetiser...")
    # synthetiser uruchamiamy bez przekierowania - będzie logował do konsoli
    synthetiser_process = start_process(synthetiser_cmd, capture_output=False)

    # Sprawdź natychmiast czy procesy żyją
    print("🔧 Sprawdzanie statusu procesów po uruchomieniu...")
    time.sleep(1)
    
    processes = {
        "Agent": agent_process,
        "Analyser": analyser_process,
        "Synthetiser": synthetiser_process
    }
    
    for name, proc in processes.items():
        if proc.poll() is not None:
            print(f"❌ {name} już nie żyje! Kod wyjścia: {proc.returncode}")
        else:
            print(f"✅ {name} działa")

    # Flagi dla jednorazowego wyświetlania statusu
    process_done_flags = {name: False for name in processes.keys()}
    
    try:
        while True:
            # Sprawdź status wszystkich procesów
            all_done = True
            for name, proc in processes.items():
                is_done = proc.poll() is not None
                
                if is_done and not process_done_flags[name]:
                    print(f"🛑 {name} zakończył działanie z kodem: {proc.returncode}")
                    process_done_flags[name] = True
                
                if not is_done:
                    all_done = False
            
            # Jeśli wszystkie procesy zakończone
            if all_done:
                print("🛑 Wszystkie procesy zakończyły działanie.")
                break

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n⏹️ Przerwano działanie aplikacji przez użytkownika.")

    finally:
        cleanup()

if __name__ == "__main__":
    main()