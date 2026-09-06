"""Tests for evidence-weighted stock-strategy ranking."""

from __future__ import annotations

from src.portfolio.strategy_scorecard import (
    MarketRegime,
    StrategyBacktestMetrics,
    StrategyEvidenceRecord,
    StrategyRegimeMetrics,
    rank_strategies,
    score_strategy,
)


def _record(
    strategy_id: str,
    *,
    expectancy_r: float,
    profit_factor: float,
    drawdown: float,
    trades: int = 220,
    win_rate: float = 0.52,
    regime: MarketRegime = MarketRegime.trend_bull,
    regime_expectancy: float = 0.25,
    regime_profit_factor: float = 1.35,
    walk_forward: bool = True,
    holdout: bool = True,
    cost_stress: bool = True,
    pbo_warning: bool = False,
) -> StrategyEvidenceRecord:
    return StrategyEvidenceRecord(
        metrics=StrategyBacktestMetrics(
            strategy_id=strategy_id,
            strategy_name=strategy_id.replace("_", " ").title(),
            trades=trades,
            win_rate=win_rate,
            expectancy_r=expectancy_r,
            profit_factor=profit_factor,
            sharpe=1.1,
            max_drawdown_pct=drawdown,
            avg_trade_bps=18.0,
        ),
        regime_metrics=[
            StrategyRegimeMetrics(
                regime=regime,
                trades=max(40, trades // 3),
                win_rate=win_rate,
                expectancy_r=regime_expectancy,
                profit_factor=regime_profit_factor,
                max_drawdown_pct=min(drawdown, 18.0),
            )
        ],
        walk_forward_pass=walk_forward,
        holdout_pass=holdout,
        cost_stress_pass=cost_stress,
        pbo_warning=pbo_warning,
    )


def test_high_win_rate_does_not_rescue_negative_expectancy() -> None:
    bad = _record(
        "high_win_rate_bad_expectancy",
        expectancy_r=-0.06,
        profit_factor=0.88,
        drawdown=12.0,
        win_rate=0.74,
    )

    score = score_strategy(bad, MarketRegime.trend_bull)

    assert score.recommendation == "REJECTED"
    assert "non_positive_expectancy" in score.gate_failures
    assert "profit_factor_not_above_one" in score.gate_failures


def test_unvalidated_strategy_remains_shadow_only_even_with_good_backtest() -> None:
    record = _record(
        "good_but_unvalidated",
        expectancy_r=0.30,
        profit_factor=1.55,
        drawdown=14.0,
        holdout=False,
    )

    score = score_strategy(record, MarketRegime.trend_bull)

    assert score.total_score > 50
    assert score.recommendation == "SHADOW_ONLY"
    assert "holdout_not_passed" in score.gate_failures


def test_missing_walk_forward_validation_prevents_full_activation() -> None:
    record = _record(
        "missing_walk_forward",
        expectancy_r=0.30,
        profit_factor=1.55,
        drawdown=14.0,
        walk_forward=False,
    )

    score = score_strategy(record, MarketRegime.trend_bull)

    assert score.recommendation == "SHADOW_ONLY"
    assert "walk_forward_not_passed" in score.gate_failures


def test_high_win_rate_alone_cannot_activate_an_unvalidated_method() -> None:
    record = _record(
        "high_hit_rate_unvalidated",
        expectancy_r=0.03,
        profit_factor=1.08,
        drawdown=12.0,
        trades=400,
        win_rate=0.92,
        walk_forward=False,
        holdout=False,
        cost_stress=False,
    )

    score = score_strategy(record, MarketRegime.trend_bull)

    assert score.recommendation == "SHADOW_ONLY"
    assert score.total_score < 80
    assert "walk_forward_not_passed" in score.gate_failures
    assert "holdout_not_passed" in score.gate_failures


def test_current_regime_can_change_strategy_ranking() -> None:
    trend = _record(
        "trend_strategy",
        expectancy_r=0.24,
        profit_factor=1.40,
        drawdown=14.0,
        regime=MarketRegime.trend_bull,
        regime_expectancy=0.40,
        regime_profit_factor=1.75,
    )
    range_method = _record(
        "range_strategy",
        expectancy_r=0.22,
        profit_factor=1.38,
        drawdown=13.0,
        regime=MarketRegime.range_bound,
        regime_expectancy=0.42,
        regime_profit_factor=1.80,
    )

    trend_rank = rank_strategies([trend, range_method], MarketRegime.trend_bull)
    range_rank = rank_strategies([trend, range_method], MarketRegime.range_bound)

    assert trend_rank[0].strategy_id == "trend_strategy"
    assert range_rank[0].strategy_id == "range_strategy"


def test_backtest_overfitting_warning_blocks_active_use() -> None:
    record = _record(
        "overfit_candidate",
        expectancy_r=0.44,
        profit_factor=1.90,
        drawdown=10.0,
        pbo_warning=True,
    )

    score = score_strategy(record, MarketRegime.trend_bull)

    assert score.recommendation == "REJECTED"
    assert "backtest_overfitting_warning" in score.gate_failures
