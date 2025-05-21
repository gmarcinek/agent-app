from agent.state import AgentState, Scenario
from agent.commands.factory import get_command

def agent_loop(state: AgentState, scenario: Scenario) -> AgentState:
    print("🔁 Start pętli agenta...")

    for i, step in enumerate(scenario.steps, 1):
        print(f"\n➡️  Krok {i}: generuję artefakt '{step['artifact']['name']}'")

        command = get_command("generate_code", step)
        state = command.run(state)

        last_result = state.history[-1]
        report = last_result.output.get("validation_report")

        if report and not report["ok"]:
            print(f"❌ Walidacja nie powiodła się dla {step['artifact']['name']}.")
            print(report["details"])
            state.done = True
            break

        print(f"✅ Artefakt {step['artifact']['name']} wygenerowany i przeszedł walidację.")

    state.done = True
    print("\n🏁 Agent zakończył pracę.")
    return state
