import os
import json
from agent.state import AgentState, Scenario
from agent.llm.use_llm import LLMClient
from agent.input import AgentInput
from agent.prompt.scenario_prompt_builder import build_scenario_prompt
from agent.loop import agent_loop

def should_enter_interactive_mode(agent_input: AgentInput | None, state_path: str) -> bool:
    if not agent_input:
        return True

    if os.path.exists(state_path):
        try:
            state = AgentState.from_json(state_path)
            return getattr(state, "done", False)
        except Exception as e:
            print(f"⚠️ Błąd przy wczytywaniu state.json: {e}")
            return False

    return False

def interactive_loop():
    state_path = "output/state.json"
    scenario_path = "output/scenario.json"
    log_path = "output/logs/interactive_raw.txt"

    # Wczytaj constraints z agent_input.json (jeśli istnieje)
    agent_input = AgentInput.from_file("agent_input.json") if os.path.exists("agent_input.json") else None
    constraints = agent_input.constraints if agent_input else []

    # Wczytaj stan
    state = AgentState.from_json(state_path) if os.path.exists(state_path) else AgentState()

    # Wczytaj istniejący scenariusz
    steps = []
    if os.path.exists(scenario_path):
        with open(scenario_path, encoding="utf-8") as f:
            steps = json.load(f)

    llm = LLMClient(model="gpt-4o")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    while True:
        user_input = input("🟢 Podaj nowy cel działania agenta:\n> ").strip()
        if not user_input:
            print("⚠️ Pusty input – spróbuj jeszcze raz.")
            continue

        # 🧠 Fix prompt
        fixed_input = fix_user_prompt(user_input)
        print(f"🧪 Poprawiony prompt:\n→ {fixed_input}")

        prompt = build_scenario_prompt(fixed_input, constraints, mode="interactive")

        try:
            response = llm.chat(prompt).strip()

            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n--- Prompt ---\n{prompt}\n\n--- Response ---\n{response}\n")

            if response.startswith("```json"):
                response = response.removeprefix("```json").removesuffix("```").strip()

            steps_batch = json.loads(response)
            if not isinstance(steps_batch, list):
                raise ValueError("LLM powinien zwrócić listę kroków")

            print(f"📥 Dodano {len(steps_batch)} kroków.")
            steps.extend(steps_batch)

            with open(scenario_path, "w", encoding="utf-8") as f:
                json.dump(steps, f, indent=2, ensure_ascii=False)

            scenario = Scenario(goal="interactive", steps=steps)
            state = agent_loop(state, scenario)
            state.to_json(state_path)

        except Exception as e:
            print(f"❌ Błąd LLM lub scenariusza:\n{e}")

def fix_user_prompt(raw_input: str, model="gpt-4o") -> str:
    fixer_prompt = f"""Popraw lub uzupełnij polecenie użytkownika, zachowując jego intencję.
Usuń błędy językowe i spraw, by polecenie było możliwie jasne dla agenta AI.
Zwróć tylko jedną poprawioną wersję bez dodatkowych komentarzy.

Polecenie:
{raw_input}

Poprawione:
"""
    llm = LLMClient(model=model)
    return llm.chat(fixer_prompt).strip()
