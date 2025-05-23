from dotenv import load_dotenv
load_dotenv()

import os
import json
import atexit
import signal

# ⬇️ Upewniamy się, że katalog output istnieje
os.makedirs("output", exist_ok=True)

from agent.input import AgentInput
from agent.planner.scenario import plan_scenario
from agent.state import AgentState, Scenario
from agent.loop import agent_loop
from agent.interactive_loop import interactive_loop
from agent.process_registry import process_registry

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
    print("\n🧹 Sprzątanie... Zatrzymuję procesy w tle.")
    process_registry.kill_all()

# Rejestruj cleanup przy wyjściu
atexit.register(cleanup_background_processes)
signal.signal(signal.SIGINT, lambda sig, frame: exit(0))
signal.signal(signal.SIGTERM, lambda sig, frame: exit(0))

def main():
    print("🔄 Wczytuję dane wejściowe agenta...")

    scenario_path = "output/scenario.json"
    state_path = "output/state.json"

    if os.path.exists("agent_input.json"):
        agent_input = AgentInput.from_file("agent_input.json")
    else:
        agent_input = None

    # Tryb interaktywny jeśli brak inputu lub stan zakończony
    if not agent_input or (os.path.exists(state_path) and AgentState.from_json(state_path).done):
        interactive_loop()
    else:
        # 📋 Scenariusz
        if os.path.exists(scenario_path):
            print(f"📂 Wczytuję istniejący scenariusz z: {scenario_path}")
            with open(scenario_path, encoding="utf-8") as f:
                steps = json.load(f)
        else:
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

        # 🧠 Stan agenta
        if os.path.exists(state_path):
            print("📦 Wczytuję poprzedni stan agenta...")
            state = AgentState.from_json(state_path)
        else:
            print("🆕 Tworzę nowy stan agenta...")
            state = AgentState()

        # 🚀 Pętla agenta
        print("🚀 Uruchamiam agenta...")
        final_state = agent_loop(state, scenario)

        # 📊 Podsumowanie
        print(f"\n📊 Wykonano {final_state.current_step_index}/{len(scenario.steps)} kroków.")
        final_state.to_json(state_path)
        print("💾 Zapisano stan agenta.")

        # 🔁 Jeśli działają procesy w tle – przejdź w tryb interaktywny
        if process_registry.has_active_processes():
            print("🔁 W tle działa dev-server. Przechodzę do trybu interaktywnego...")
            while True:
                user_input = input("🟢 Tryb interaktywny. Wpisz komendę ('exit' aby wyjść):\n> ")
                if user_input.strip().lower() == "exit":
                    print("👋 Kończę. Zatrzymuję wszystkie procesy...")
                    break
                else:
                    print("ℹ️ Nieznana komenda. Dostępne: exit")

if __name__ == "__main__":
    main()