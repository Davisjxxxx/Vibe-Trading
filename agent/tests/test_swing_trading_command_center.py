"""Acceptance contract for the research-backed swing-trading swarm preset."""

from __future__ import annotations

from pathlib import Path

from src.swarm.presets import build_run_from_preset, load_preset
from src.swarm.task_store import validate_dag


PRESET_NAME = "swing_trading_command_center"
EXPECTED_AGENTS = {
    "data_quality_guard",
    "momentum_specialist",
    "trend_regime_specialist",
    "relative_value_specialist",
    "fundamental_quality_specialist",
    "valuation_expectations_specialist",
    "earnings_catalyst_specialist",
    "macro_news_sentinel",
    "portfolio_risk_governor",
    "chief_orchestrator",
}


def _run():
    return build_run_from_preset(
        PRESET_NAME,
        {
            "target": "AAPL",
            "market": "US equities",
            "account_size": "1000",
            "holding_horizon": "3-15 trading days",
        },
    )


def test_swing_command_center_loads_and_has_valid_dag() -> None:
    run = _run()
    validate_dag(run.tasks)

    assert run.preset_name == PRESET_NAME
    assert {agent.id for agent in run.agents} == EXPECTED_AGENTS
    assert len(run.agents) == 10


def test_risk_governor_receives_all_independent_evidence_families() -> None:
    run = _run()
    tasks = {task.id: task for task in run.tasks}

    risk_task = tasks["task-risk-governor"]
    expected_dependencies = {
        "task-momentum",
        "task-trend-regime",
        "task-relative-value",
        "task-fundamentals",
        "task-valuation",
        "task-catalyst",
        "task-macro-news",
    }
    assert set(risk_task.depends_on) == expected_dependencies
    assert risk_task.input_from["data_quality"] == "task-data-quality"
    assert set(risk_task.input_from.values()) == expected_dependencies | {"task-data-quality"}


def test_final_orchestrator_retains_specialist_evidence_and_hard_risk_gate() -> None:
    run = _run()
    tasks = {task.id: task for task in run.tasks}
    agents = {agent.id: agent for agent in run.agents}

    final_task = tasks["task-final-decision"]
    assert final_task.depends_on == ["task-risk-governor"]
    assert final_task.input_from["risk_governor"] == "task-risk-governor"
    assert final_task.input_from["macro_news"] == "task-macro-news"
    assert final_task.input_from["momentum"] == "task-momentum"
    assert final_task.input_from["trend_regime"] == "task-trend-regime"

    governor_prompt = agents["portfolio_risk_governor"].system_prompt
    orchestrator_prompt = agents["chief_orchestrator"].system_prompt

    assert "ENTRY_BLOCK" in governor_prompt
    assert "EMERGENCY_EXIT" in governor_prompt
    assert "0.5%" in governor_prompt
    assert "1.0%" in governor_prompt
    assert "may not override ENTRY_BLOCK or EMERGENCY_EXIT" in orchestrator_prompt


def test_momentum_agents_are_explicitly_correlated_not_independent_votes() -> None:
    run = _run()
    agents = {agent.id: agent for agent in run.agents}

    momentum_prompt = agents["momentum_specialist"].system_prompt
    trend_prompt = agents["trend_regime_specialist"].system_prompt
    orchestrator_prompt = agents["chief_orchestrator"].system_prompt

    assert "correlation_cluster: momentum" in momentum_prompt
    assert "correlation_cluster: momentum" in trend_prompt
    assert "does not count as two independent votes" in orchestrator_prompt


def test_preset_uses_only_existing_native_skill_directories() -> None:
    preset = load_preset(PRESET_NAME)
    skills_dir = Path(__file__).resolve().parent.parent / "src" / "skills"

    referenced_skills = {
        skill
        for agent in preset["agents"]
        for skill in agent.get("skills", [])
    }
    missing = sorted(skill for skill in referenced_skills if not (skills_dir / skill).is_dir())

    assert "event-study" not in referenced_skills
    assert "event-driven" in referenced_skills
    assert "pair-trading" in referenced_skills
    assert "geopolitical-risk" in referenced_skills
    assert missing == []
