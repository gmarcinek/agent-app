import os
import json
from agent.state import AgentState, Scenario
from agent.llm.use_llm import LLMClient
from agent.prompt.scenario_prompt_builder import build_scenario_prompt, build_summary_prompt
from agent.loop import agent_loop

def interactive_loop():
    state_path = "output/state.json"
    scenario_path = "output/scenario.json"

    # Wczytaj stan
    state = AgentState.from_json(state_path) if os.path.exists(state_path) else AgentState()

    # Wczytaj scenariusz
    steps = []
    if os.path.exists(scenario_path):
        with open(scenario_path, encoding="utf-8") as f:
            steps = json.load(f)

    llm = LLMClient(model="gpt-4o")

    while True:
        print("\n🔄 Tryb interaktywny")

        if not state.history:
            user_input = input("Od czego zaczynamy, co chcesz zbudować? (lub wpisz 'exit')\n> ")
        elif state.done:
            summary_prompt = build_summary_prompt(state.model_dump_json(indent=2))
            summary = llm.chat(summary_prompt)
            print(summary)
            user_input = input("Co dalej? (lub wpisz 'exit')\n> ")
        else:
            print("🔁 Agent wciąż działa. Poczekaj na zakończenie scenariusza.")
            return

        if user_input.strip().lower() == "exit":
            print("👋 Kończę tryb interaktywny.")
            break

        scenario_prompt = build_scenario_prompt(user_input, [], mode="interactive")
        try:
            new_steps_raw = llm.chat(scenario_prompt).strip()
            # Usuwanie ewentualnych code fences
            if new_steps_raw.startswith("```json"):
                new_steps_raw = new_steps_raw.removeprefix("```json").removesuffix("```").strip()

            try:
                new_steps = json.loads(new_steps_raw)
            except json.JSONDecodeError as e:
                print("❌ LLM zwrócił nieparsowalną odpowiedź:")
                print(new_steps_raw)
                raise e

            if not isinstance(new_steps, list):
                raise ValueError("LLM powinien zwrócić listę kroków")

            print(f"📥 Dodano {len(new_steps)} nowych kroków do scenariusza.")
            steps.extend(new_steps)

            # Nadpisz scenariusz
            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(steps, f, indent=2, ensure_ascii=False)

            state.done = False
            scenario = Scenario(goal="interactive", steps=steps)
            state = agent_loop(state, scenario)
            state.to_json(state_path)

        except Exception as e:
            print(f"❌ Błąd interakcji LLM: {e}")
