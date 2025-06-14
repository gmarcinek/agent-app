import os
import json
import re
from agent.input import AgentInput
from llm import LLMClient, Models
from agent.prompt.scenario_prompt_builder import build_scenario_prompt
from agent.prompt.initial_scenario_prompt import build_initial_scenario_prompt

def plan_scenario(agent_input: AgentInput) -> list[dict]:
    llm = LLMClient(Models.CLAUDE_4_SONNET)

    # Sprawdź czy istnieje scenario.json w output
    scenario_path = "output/scenario.json"
    
    if os.path.exists(scenario_path):
        # Użyj nowego złożonego prompta
        prompt = build_scenario_prompt(agent_input.goal, agent_input.constraints, mode="initial")
    else:
        # Użyj prostego prompta do inicjalizacji
        prompt = build_initial_scenario_prompt(agent_input.goal, agent_input.constraints)

    raw = llm.chat(prompt)

    # Logi i sanity-check
    os.makedirs("output/logs", exist_ok=True)
    with open("output/logs/plan_raw.txt", "w", encoding="utf-8") as f:
        f.write(raw)

    match = re.search(r'\[[\s\S]+\]', raw)
    if not match:
        raise ValueError("LLM nie zwrócił poprawnego JSON-a (brak listy kroków)")

    json_content = match.group(0)
    with open("output/logs/plan_json.txt", "w", encoding="utf-8") as f:
        f.write(json_content)

    try:
        steps = json.loads(json_content)
        if not isinstance(steps, list):
            raise ValueError("Zdekodowany JSON nie jest listą")
    except Exception as e:
        raise RuntimeError(f"Błąd parsowania JSON: {e}\n{json_content[:200]}...")

    return steps