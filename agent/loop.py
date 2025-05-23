from agent.state import AgentState, Scenario
from agent.commands.factory import get_command

def agent_loop(state: AgentState, scenario: Scenario) -> AgentState:
    print("🔁 Start pętli agenta...")

    while state.current_step_index < len(scenario.steps):
        step = scenario.steps[state.current_step_index]
        step_type = step.get("type") or step.get("command") or "generate_code"

        print(f"\n➡️  Krok {state.current_step_index + 1}: {step_type}")

        try:
            command = get_command(step_type, step)
            print(f"🔧 Komenda: {command.__class__.__name__}")
            print(f"📦 Params: {step}")

            state = command.run(state)

            last_result = state.history[-1]
            report = last_result.output.get("validation_report")

            if report and not report.get("ok", True):
                print(f"❌ Walidacja nie powiodła się dla kroku {step_type}.")
                print(report.get("details", "Brak szczegółów."))
                state.done = True
                break

        except Exception as e:
            print(f"❌ Błąd podczas wykonywania kroku {step_type}: {e}")
            state.done = True
            break

        state.current_step_index += 1

    state.done = True
    print(f"\n🏁 Agent zakończył pracę. Wykonano {state.current_step_index}/{len(scenario.steps)} kroków.")
    return state
