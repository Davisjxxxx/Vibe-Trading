"""Acceptance contract for the stock-only daily decision desk."""

from __future__ import annotations

from pathlib import Path

from src.swarm.presets import build_run_from_preset, load_preset
from src.swarm.task_store import validate_dag


PRESET_NAME = "stock_daily_decision_desk"
EXPECTED_AGENTS = {
    "market_regime_researcher",
    "strategy_selector",
    "fundamental_catalyst_screener",
    "momentum_screener",
    "relative_value_screener",
    "news_risk_notifier",
    "candidate_committee",
    "ta_structure_analyst",
    "ta_counter_thesis_analyst",
    "ta_execution_analyst",
    "portfolio_risk_governor",
    "human_decision_editor",
}


def _run():
    return build_run_from_preset(
        PRESET_NAME,
        {
            "universe": "liquid U.S. common stocks",
            "candidate_limit": "5",
            "holding_horizon": "2-15 trading days",
            "risk_appetite": "moderate",
            "account_size": "1000",
        },
    )


def test_daily_desk_loads_and_has_valid_dag() -> None:
    run = _run()
    validate_dag(run.tasks)

    assert run.preset_name == PRESET_NAME
    assert {agent.id for agent in run.agents} == EXPECTED_AGENTS
    assert len(run.agents) == 12


def test_research_flows_into_multi_perspective_ta_before_risk_review() -> None:
    run = _run()
    tasks = {task.id: task for task in run.tasks}

    committee = tasks["task-candidate-committee"]
    assert set(committee.depends_on) == {
        "task-strategy-selector",
        "task-fundamental-catalyst",
        "task-momentum-screen",
        "task-relative-value-screen",
        "task-news-risk",
    }

    ta_execution = tasks["task-ta-execution"]
    assert set(ta_execution.depends_on) == {"task-ta-structure", "task-ta-counter"}
    assert ta_execution.input_from["ta_primary"] == "task-ta-structure"
    assert ta_execution.input_from["ta_counter"] == "task-ta-counter"

    risk = tasks["task-portfolio-risk"]
    assert "task-ta-execution" in risk.depends_on
    assert "task-news-risk" in risk.depends_on


def test_final_output_requires_human_approval_and_forbids_autonomous_execution() -> None:
    run = _run()
    agents = {agent.id: agent for agent in run.agents}

    editor_prompt = agents["human_decision_editor"].system_prompt
    news_prompt = agents["news_risk_notifier"].system_prompt
    risk_prompt = agents["portfolio_risk_governor"].system_prompt

    assert "HUMAN_APPROVAL_REQUIRED: true" in editor_prompt
    assert "DO_NOT_EXECUTE_AUTONOMOUSLY: true" in editor_prompt
    assert "Never execute" in editor_prompt
    assert "notification system only" in news_prompt
    assert "do not place, cancel, reduce, or close orders" in news_prompt
    assert "No autonomous order action is permitted" in risk_prompt


def test_stock_only_scope_has_no_crypto_or_coinbase_language() -> None:
    preset = load_preset(PRESET_NAME)
    text = str(preset).lower()

    assert "crypto" not in text
    assert "coinbase" not in text
    assert "stablecoin" not in text


def test_preset_uses_existing_native_skill_directories() -> None:
    preset = load_preset(PRESET_NAME)
    skills_dir = Path(__file__).resolve().parent.parent / "src" / "skills"

    referenced_skills = {
        skill
        for agent in preset["agents"]
        for skill in agent.get("skills", [])
    }
    missing = sorted(skill for skill in referenced_skills if not (skills_dir / skill).is_dir())

    assert missing == []


def test_circuit_breaker_does_not_assume_reversal_after_losses() -> None:
    run = _run()
    agents = {agent.id: agent for agent in run.agents}
    prompt = agents["portfolio_risk_governor"].system_prompt

    assert "NORMAL, CAUTION, DEFENSIVE, LOCKOUT, or RECOVERY" in prompt
    assert "Do not assume a reversal is due after consecutive losses" in prompt
    assert "In LOCKOUT, block all new trade recommendations" in prompt
