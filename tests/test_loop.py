import pytest
from agent.state import AgentState
from agent.scenario import Scenario
from agent.loop import agent_loop
import os
import json

def test_happy_path(tmp_path):
    # Skopiuj scenariusz do katalogu testowego
    scenario_path = os.path.join(tmp_path, "test_scenario.json")
    with open("scenarios/happy_path.json") as src, open(scenario_path, "w") as dst:
        dst.write(src.read())

    scenario = Scenario.from_file(scenario_path)
    state = AgentState()

    final_state = agent_loop(state, scenario)

    # Porównujemy kroków
    assert len(final_state.history) == len(scenario.steps)

    # Każdy krok powinien mieć expected keys
    for step in final_state.history:
        assert "step_name" in step.model_dump()
        assert "input" in step.model_dump()
        assert "output" in step.model_dump()

    # Artefakty powinny być zgodne z krokami write_file
    written = [
        s.output["component_name"]
        for s in final_state.history
        if s.step_name == "write_file"
    ]

    for name in written:
        assert name in final_state.artifacts
        assert os.path.exists(final_state.artifacts[name])
