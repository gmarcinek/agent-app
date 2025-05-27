from dotenv import load_dotenv
load_dotenv()

import os
import json
import atexit
import signal
import time

# ⬇️ Upewniamy się, że katalog output istnieje
os.makedirs("output", exist_ok=True)

from agent.input import AgentInput
from agent.planner.scenario import plan_scenario
from agent.state import AgentState, Scenario
from agent.loop import agent_loop
from registry.process_registry import process_registry

def describe_step(step: dict) -> tuple[str, str]:
    step_type = step.get("type", "generate_code")
    params = step.get("params", {})

    if step_type == "generate_code":
        name = params.get("artifact", {}).get("name", "[?]")
        path = params.get("artifact", {}).get("path", "?")
    elif step_type == "write_file":
        name = os.path.basename(params.get("path", "?"))
        path = params.get("path", "?")
    elif step_type == "mkdir":
        name = "[mkdir]"
        path = params.get("path", "?")
    elif step_type == "cd":
        name = "[cd]"
        path = params.get("path", "?")
    elif step_type == "run_script":
        name = "[run]"
        path = params.get("command", "?")
    elif step_type == "delete":
        name = "[delete]"
        path = params.get("path", "?")
    else:
        name = f"[{step_type}]"
        path = "?"

    return name, path

def cleanup_background_processes():
    print("🧹 Sprzątanie... Zatrzymuję procesy w tle.")
    process_registry.kill_all()

# Rejestruj cleanup przy wyjściu
atexit.register(cleanup_background_processes)
signal.signal(signal.SIGINT, lambda sig, frame: exit(0))
signal.signal(signal.SIGTERM, lambda sig, frame: exit(0))

def process_agent_input():
    """Przetwarza jedno polecenie z agent_input.json"""
    if not os.path.exists("agent_input.json"):
        return False
    
    print("📨 Otrzymano nowe polecenie!")
    
    try:
        agent_input = AgentInput.from_file("agent_input.json")
        scenario_path = "output/scenario.json"
        state_path = "output/state.json"
        
        # 📋 Scenariusz
        print("🧠 Generuję scenariusz z LLM...")
        steps = plan_scenario(agent_input)
        os.makedirs(os.path.dirname(scenario_path), exist_ok=True)
        with open(scenario_path, "w", encoding="utf-8") as f:
            json.dump(steps, f, indent=2, ensure_ascii=False)
        print(f"💾 Zapisano scenariusz do: {scenario_path}")

        print(f"📋 Scenariusz zawiera {len(steps)} kroków:")
        for i, step in enumerate(steps, 1):
            name, path = describe_step(step)
            print(f"   {i:>2}. {name} → {path}")

        # 🧠 Utwórz scenariusz
        scenario = Scenario(goal=agent_input.goal, steps=steps)

        # 🧠 Stan agenta - zawsze nowy dla GUI
        print("🆕 Tworzę nowy stan agenta...")
        state = AgentState()

        # 🚀 Pętla agenta
        print("🔁 Start pętli agenta...")
        final_state = agent_loop(state, scenario)

        # 📊 Podsumowanie
        print(f"🏁 Agent zakończył pracę. Wykonano {final_state.current_step_index}/{len(scenario.steps)} kroków.")
        final_state.to_json(state_path)
        
        # Usuń agent_input.json żeby nie przetwarzać ponownie
        os.remove("agent_input.json")
        print("✅ Polecenie zakończone, oczekuję na kolejne...")
        return True
        
    except Exception as e:
        print(f"❌ Błąd przetwarzania polecenia: {e}")
        # Usuń wadliwy plik
        if os.path.exists("agent_input.json"):
            os.remove("agent_input.json")
        return False

def main():
    print("🖥️ Agent GUI - oczekuję na polecenia...")
    print("💡 Aby wysłać polecenie, stwórz plik agent_input.json")
    
    # Główna pętla oczekiwania na polecenia
    while True:
        try:
            # Sprawdź czy jest nowe polecenie
            if process_agent_input():
                # Jeśli są procesy w tle, poinformuj o tym
                if process_registry.has_active_processes():
                    print("🔄 W tle działa dev-server.")
            
            # Pauza żeby nie obciążać CPU
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n⏹️ Zatrzymywanie agenta GUI...")
            break
        except Exception as e:
            print(f"❌ Nieoczekiwany błąd: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()