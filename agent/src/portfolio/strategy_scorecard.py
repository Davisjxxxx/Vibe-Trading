"""Evidence-weighted strategy scorecard for stock-trading portfolio selection.

The scorecard intentionally does not optimize for win rate alone. It ranks strategies
using expectancy, drawdown, robustness, sample size, and current-regime fit, then
applies hard validation gates before a method can become an active candidate.
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable

from pydantic import BaseModel, Field


class MarketRegime(str, Enum):
    trend_bull = "trend_bull"
    trend_bear = "trend_bear"
    high_volatility = "high_volatility"
    low_volatility = "low_volatility"
    range_bound = "range_bound"
    macro_stress = "macro_stress"
    unknown = "unknown"


class StrategyBacktestMetrics(BaseModel):
    strategy_id: str
    strategy_name: str
    trades: int = Field(ge=0)
    win_rate: float = Field(ge=0.0, le=1.0)
    expectancy_r: float
    profit_factor: float = Field(ge=0.0)
    sharpe: float = 0.0
    max_drawdown_pct: float = Field(ge=0.0)
    avg_trade_bps: float = 0.0
    sample_start: str | None = None
    sample_end: str | None = None


class StrategyRegimeMetrics(BaseModel):
    regime: MarketRegime
    trades: int = Field(ge=0)
    win_rate: float = Field(ge=0.0, le=1.0)
    expectancy_r: float
    profit_factor: float = Field(ge=0.0)
    max_drawdown_pct: float = Field(ge=0.0)


class StrategyEvidenceRecord(BaseModel):
    metrics: StrategyBacktestMetrics
    regime_metrics: list[StrategyRegimeMetrics] = Field(default_factory=list)
    walk_forward_pass: bool = False
    holdout_pass: bool = False
    cost_stress_pass: bool = False
    pbo_warning: bool = False
    last_validated_at: str | None = None
    notes: list[str] = Field(default_factory=list)


class StrategyScore(BaseModel):
    strategy_id: str
    strategy_name: str
    total_score: float = Field(ge=0.0, le=100.0)
    grade: str
    recommendation: str
    current_regime: MarketRegime
    expectancy_score: float
    risk_score: float
    robustness_score: float
    regime_fit_score: float
    sample_score: float
    gate_failures: list[str] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _linear(value: float, bad: float, good: float) -> float:
    if good <= bad:
        raise ValueError("good must be greater than bad")
    return _clip((value - bad) / (good - bad), 0.0, 1.0)


def _regime_metrics(record: StrategyEvidenceRecord, regime: MarketRegime) -> StrategyRegimeMetrics | None:
    for item in record.regime_metrics:
        if item.regime == regime:
            return item
    return None


def score_strategy(
    record: StrategyEvidenceRecord,
    current_regime: MarketRegime = MarketRegime.unknown,
    risk_appetite: float = 0.5,
) -> StrategyScore:
    """Score one strategy without allowing a strong narrative to bypass validation gates.

    Args:
        record: Backtest and validation evidence for the strategy.
        current_regime: Current diagnosed stock-market regime.
        risk_appetite: 0.0 is most conservative; 1.0 is most risk tolerant.

    Returns:
        StrategyScore with a recommendation of ACTIVE_CANDIDATE, SHADOW_ONLY, or REJECTED.
    """

    m = record.metrics
    risk_appetite = _clip(risk_appetite, 0.0, 1.0)

    expectancy_quality = (
        0.65 * _linear(m.expectancy_r, -0.10, 0.50)
        + 0.35 * _linear(m.profit_factor, 0.80, 1.80)
    )
    expectancy_score = 25.0 * expectancy_quality

    drawdown_tolerance = 12.0 + (18.0 * risk_appetite)
    risk_quality = 1.0 - _linear(m.max_drawdown_pct, drawdown_tolerance, 45.0)
    risk_score = 20.0 * risk_quality

    robustness_score = 0.0
    robustness_score += 8.0 if record.walk_forward_pass else 0.0
    robustness_score += 8.0 if record.holdout_pass else 0.0
    robustness_score += 5.0 if record.cost_stress_pass else 0.0
    robustness_score += 4.0 if not record.pbo_warning else 0.0

    regime = _regime_metrics(record, current_regime)
    if regime is None or current_regime == MarketRegime.unknown:
        regime_fit_score = 8.0
    else:
        regime_quality = (
            0.55 * _linear(regime.expectancy_r, -0.10, 0.45)
            + 0.30 * _linear(regime.profit_factor, 0.80, 1.70)
            + 0.15 * (1.0 - _linear(regime.max_drawdown_pct, 15.0, 40.0))
        )
        regime_fit_score = 20.0 * regime_quality

    sample_score = 10.0 * _linear(float(m.trades), 20.0, 300.0)

    total = _clip(
        expectancy_score
        + risk_score
        + robustness_score
        + regime_fit_score
        + sample_score,
        0.0,
        100.0,
    )

    gate_failures: list[str] = []
    if m.trades < 30:
        gate_failures.append("insufficient_trade_sample")
    if m.expectancy_r <= 0:
        gate_failures.append("non_positive_expectancy")
    if m.profit_factor <= 1.0:
        gate_failures.append("profit_factor_not_above_one")
    if m.max_drawdown_pct > 35.0:
        gate_failures.append("drawdown_above_active_limit")
    if not record.walk_forward_pass:
        gate_failures.append("walk_forward_not_passed")
    if not record.holdout_pass:
        gate_failures.append("holdout_not_passed")
    if not record.cost_stress_pass:
        gate_failures.append("cost_stress_not_passed")
    if record.pbo_warning:
        gate_failures.append("backtest_overfitting_warning")

    severe_failures = {
        "non_positive_expectancy",
        "profit_factor_not_above_one",
        "drawdown_above_active_limit",
        "backtest_overfitting_warning",
    }
    if severe_failures.intersection(gate_failures):
        recommendation = "REJECTED"
    elif gate_failures:
        recommendation = "SHADOW_ONLY"
    else:
        recommendation = "ACTIVE_CANDIDATE"

    if total >= 80:
        grade = "A"
    elif total >= 65:
        grade = "B"
    elif total >= 50:
        grade = "C"
    else:
        grade = "D"

    rationale = [
        f"expectancy_r={m.expectancy_r:.3f}",
        f"profit_factor={m.profit_factor:.2f}",
        f"max_drawdown_pct={m.max_drawdown_pct:.2f}",
        f"trades={m.trades}",
        f"regime={current_regime.value}",
    ]
    if regime is not None:
        rationale.append(
            f"regime_expectancy_r={regime.expectancy_r:.3f}; regime_profit_factor={regime.profit_factor:.2f}"
        )
    else:
        rationale.append("no_regime_specific_sample; neutral regime-fit prior applied")

    return StrategyScore(
        strategy_id=m.strategy_id,
        strategy_name=m.strategy_name,
        total_score=round(total, 2),
        grade=grade,
        recommendation=recommendation,
        current_regime=current_regime,
        expectancy_score=round(expectancy_score, 2),
        risk_score=round(risk_score, 2),
        robustness_score=round(robustness_score, 2),
        regime_fit_score=round(regime_fit_score, 2),
        sample_score=round(sample_score, 2),
        gate_failures=gate_failures,
        rationale=rationale,
    )


def rank_strategies(
    records: Iterable[StrategyEvidenceRecord],
    current_regime: MarketRegime = MarketRegime.unknown,
    risk_appetite: float = 0.5,
) -> list[StrategyScore]:
    """Rank validated methods while keeping active, shadow, and rejected states distinct."""

    priority = {"ACTIVE_CANDIDATE": 2, "SHADOW_ONLY": 1, "REJECTED": 0}
    scores = [score_strategy(record, current_regime, risk_appetite) for record in records]
    return sorted(
        scores,
        key=lambda item: (priority[item.recommendation], item.total_score),
        reverse=True,
    )


class StrategyScorecard:
    """In-memory strategy registry used by the portfolio intelligence layer.

    Persistence and automatic backtest ingestion are intentionally separate concerns so
    the ranking rules remain deterministic and independently testable.
    """

    def __init__(self) -> None:
        self._records: dict[str, StrategyEvidenceRecord] = {}

    def register(self, record: StrategyEvidenceRecord) -> None:
        self._records[record.metrics.strategy_id] = record

    def get(self, strategy_id: str) -> StrategyEvidenceRecord | None:
        return self._records.get(strategy_id)

    def rank(
        self,
        current_regime: MarketRegime = MarketRegime.unknown,
        risk_appetite: float = 0.5,
    ) -> list[StrategyScore]:
        return rank_strategies(self._records.values(), current_regime, risk_appetite)

    def active_candidates(
        self,
        current_regime: MarketRegime = MarketRegime.unknown,
        risk_appetite: float = 0.5,
    ) -> list[StrategyScore]:
        return [
            score
            for score in self.rank(current_regime, risk_appetite)
            if score.recommendation == "ACTIVE_CANDIDATE"
        ]
