from agent.state import AgentState, Scenario
from agent.commands.factory import get_command
from logger import get_log_hub

def agent_loop(state: AgentState, scenario: Scenario) -> AgentState:
    log_hub = get_log_hub()
    log_hub.info("AGENT", "Start pętli agenta...")

    while state.current_step_index < len(scenario.steps):
        step = scenario.steps[state.current_step_index]
        step_type = step.get("type") or step.get("command") or "generate_code"

        log_hub.info("AGENT", f"Krok {state.current_step_index + 1}: {step_type}")

        try:
            command = get_command(step_type, step)
            log_hub.debug("AGENT", f"Komenda: {command.__class__.__name__}")
            log_hub.debug("AGENT", f"Params: {step}")

            state = command.run(state)

            last_result = state.history[-1]
            report = last_result.output.get("validation_report")

            if report and not report.get("ok", True):
                log_hub.error("AGENT", f"Walidacja nie powiodła się dla kroku {step_type}")
                log_hub.error("AGENT", f"Szczegóły: {report.get('details', 'Brak szczegółów')}")
                state.done = True
                break

        except Exception as e:
            log_hub.error("AGENT", f"Błąd podczas wykonywania kroku {step_type}: {e}")
            state.done = True
            break

        state.current_step_index += 1

    state.done = True
    log_hub.info("AGENT", f"Agent zakończył pracę. Wykonano {state.current_step_index}/{len(scenario.steps)} kroków")
    return state