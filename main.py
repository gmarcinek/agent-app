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

    analyser_cmd = ["poetry", "run", "analyser-watch", "--mode", "watch"]
    agent_cmd = ["poetry", "run", "agent"]

    print("🔧 Uruchamiam agent...")
    # agent uruchamiamy w trybie interaktywnym - dziedziczy terminal (stdin/out/err)
    agent_process = start_process(agent_cmd, capture_output=False)
    
    print("🔧 Czekam 2 sekundy przed uruchomieniem analysera...")
    time.sleep(2)
    
    print("🔧 Uruchamiam analyser...")
    # analyser uruchamiamy tak samo jak agent - bez przekierowania do pliku
    analyser_process = start_process(analyser_cmd, capture_output=False)
    print(f"🚀 Uruchomiono proces `{' '.join(analyser_cmd)}` (PID {analyser_process.pid})")

    analyser_done_printed = False
    agent_done_printed = False
    
    # Sprawdź natychmiast czy procesy żyją
    print("🔧 Sprawdzanie statusu procesów po uruchomieniu...")
    time.sleep(1)
    
    if agent_process.poll() is not None:
        print(f"❌ Agent już nie żyje! Kod wyjścia: {agent_process.returncode}")
    else:
        print("✅ Agent działa")
        
    if analyser_process.poll() is not None:
        print(f"❌ Analyser już nie żyje! Kod wyjścia: {analyser_process.returncode}")
    else:
        print("✅ Analyser działa")

    try:
        while True:
            agent_done = agent_process.poll() is not None
            analyser_done = analyser_process.poll() is not None

            if agent_done and analyser_done:
                if not agent_done_printed:
                    print(f"🛑 Agent zakończył działanie z kodem: {agent_process.returncode}")
                    agent_done_printed = True
                if not analyser_done_printed:
                    print(f"🛑 Analyser zakończył działanie z kodem: {analyser_process.returncode}")
                    analyser_done_printed = True
                print("🛑 Oba procesy zakończyły działanie.")
                break

            if agent_done and not agent_done_printed:
                print(f"🛑 Agent zakończył działanie z kodem: {agent_process.returncode}")
                agent_done_printed = True

            if analyser_done and not analyser_done_printed:
                print(f"🛑 Analyser zakończył działanie z kodem: {analyser_process.returncode}")
                analyser_done_printed = True

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n⏹️ Przerwano działanie aplikacji przez użytkownika.")

    finally:
        cleanup()

if __name__ == "__main__":
    main()