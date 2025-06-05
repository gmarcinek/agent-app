import os
import json
from agent.state import AgentState, Scenario
from llm import LLMClient, Models
from agent.input import AgentInput
from agent.prompt.scenario_prompt_builder import build_scenario_prompt
from agent.loop import agent_loop
from logger import get_log_hub

def should_enter_interactive_mode(agent_input: AgentInput | None, state_path: str) -> bool:
    log_hub = get_log_hub()
    
    if not agent_input:
        return True

    if os.path.exists(state_path):
        try:
            state = AgentState.from_json(state_path)
            return getattr(state, "done", False)
        except Exception as e:
            log_hub.error("AGENT", f"⚠️ Błąd przy wczytywaniu state.json: {e}")
            return False

    return False

def interactive_loop():
    from registry.process_manager import ProcessManager
    log_hub = get_log_hub()
    manager = ProcessManager()

    state_path = "output/state.json"
    scenario_path = "output/scenario.json"
    log_path = "output/logs/interactive_raw.txt"

    agent_input = AgentInput.from_file("agent_input.json") if os.path.exists("agent_input.json") else None
    constraints = agent_input.constraints if agent_input else []

    state = AgentState.from_json(state_path) if os.path.exists(state_path) else AgentState()
    steps = []
    if os.path.exists(scenario_path):
        with open(scenario_path, encoding="utf-8") as f:
            steps = json.load(f)

    llm = LLMClient(Models.CLAUDE_4_SONNET)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    try:
        while True:
            user_input = input("🟢 Podaj nowy cel działania agenta:\n> ").strip()
            if not user_input:
                log_hub.warn("AGENT", "⚠️ Pusty input – spróbuj jeszcze raz")
                continue

            fixed_input, intention = fix_and_classify_prompt(user_input)
            log_hub.info("AGENT", f"🧪 Poprawiony prompt: {fixed_input} [{intention}]")

            prompt = build_scenario_prompt(fixed_input, constraints, mode="interactive", intention=intention)

            try:
                response = llm.chat(prompt).strip()
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"\n\n--- Intention: {intention} ---\n--- Prompt ---\n{prompt}\n\n--- Response ---\n{response}\n")

                if response.startswith("```json"):
                    response = response.removeprefix("```json").removesuffix("```").strip()

                steps_batch = json.loads(response)
                if not isinstance(steps_batch, list):
                    raise ValueError("LLM powinien zwrócić listę kroków")

                log_hub.info("AGENT", f"📥 Dodano {len(steps_batch)} kroków [{intention}]")
                steps.extend(steps_batch)

                with open(scenario_path, "w", encoding="utf-8") as f:
                    json.dump(steps, f, indent=2, ensure_ascii=False)

                scenario = Scenario(goal="interactive", steps=steps)
                state = agent_loop(state, scenario)
                state.to_json(state_path)

            except Exception as e:
                log_hub.error("AGENT", f"❌ Błąd LLM lub scenariusza: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Przerwano ręcznie.")
    finally:
        log_hub.warn("AGENT", "🧹 Zatrzymuję wszystkie procesy...")
        manager.stop_all()
        log_hub.info("AGENT", "✅ Zakończono interaktywną sesję.")


def fix_and_classify_prompt(raw_input: str) -> tuple[str, str]:
    """Poprawia prompt i klasyfikuje intencję w jednym wywołaniu LLM"""
    log_hub = get_log_hub()
    
    fixer_prompt = f"""Popraw polecenie użytkownika i sklasyfikuj jego intencję.

Zwróć odpowiedź w formacie JSON:
{{
  "fixed_prompt": "poprawione i uzupełnione polecenie",
  "intention": "infrastructure lub mixed"
}}

Kategorie:
- infrastructure: jeśli tekst zawiera tylko pure setup/ops - instalacja, git clone, mkdir, npm install, npm create, npx, i tym podobne
- mixed: wszystko inne - development, features, komponenty (DEFAULT)

Polecenie użytkownika:
{raw_input}
"""
    
    try:
        llm = LLMClient(Models.GPT_4O_MINI)
        response = llm.chat(fixer_prompt).strip()
        
        # Parse JSON response
        if response.startswith("```json"):
            response = response.removeprefix("```json").removesuffix("```").strip()
        
        result = json.loads(response)
        fixed_prompt = result.get("fixed_prompt", raw_input)
        intention = result.get("intention", "code_generation")
        
        log_hub.debug("AGENT", f"🔧 '{raw_input}' → '{fixed_prompt}' [{intention}]")
        return fixed_prompt, intention
        
    except Exception as e:
        log_hub.error("AGENT", f"❌ Błąd fix+classify: {e}")
        return raw_input, "code_generation"  # Safe fallback