from dotenv import load_dotenv
load_dotenv()

import os
import json
from agent.input import AgentInput
from agent.planner.scenario import plan_scenario
from agent.state import AgentState, Scenario
from agent.loop import agent_loop

if __name__ == "__main__":
    print("🔄 Wczytuję dane wejściowe agenta...")
    agent_input = AgentInput.from_file("agent_input.json")

    print("🧠 Generuję scenariusz z LLM...")
    steps = plan_scenario(agent_input)

    print(f"📋 Scenariusz zawiera {len(steps)} kroków:")
    for i, step in enumerate(steps, 1):
        artifact = step["artifact"]
        print(f"   {i:>2}. {artifact['name']} → {artifact['path']}")

    # 💾 Zapis scenariusza
    output_path = "output/scenario.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(steps, f, indent=2, ensure_ascii=False)

    print(f"💾 Zapisano scenariusz do: {output_path}")

    # 🚀 Start agenta
    print("🚀 Uruchamiam agenta...")
    scenario = Scenario(
        goal=agent_input.goal,
        steps=steps
    )

    state = AgentState(current_step_index=0)
    final_state = agent_loop(state, scenario)

    print(f"\n✅ Wykonano {len(final_state.history)} kroków.")
