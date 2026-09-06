# Research-Backed Swing Trading Architecture

## Purpose

This document defines the target architecture for evolving Vibe-Trading into an evidence-first, multi-agent swing-trading decision and portfolio-management system for U.S. equities and crypto. The initial model portfolio is **$1,000** and the system must prioritize survival, auditability, and falsifiable decision logic over trade frequency.

Historical backtests are evidence, not guarantees. No strategy, book, author, factor, indicator, or AI agent is treated as infallible.

## Core design principle

The system must combine **independent causal signal families**, not simply collect many agents and count votes.

The initial families are:

1. **Cross-sectional momentum / continuation** — Gray/Vogel-style quantitative momentum.
2. **Trend quality / regime / volatility** — Clenow-style regression momentum, regime filters, and ATR-informed risk.
3. **Relative value / mean reversion** — Chan-style statistical-arbitrage and convergence logic.
4. **Accounting quality / business strength** — Penman/Pope-style financial-statement analysis with Piotroski-style health diagnostics and Buffett-style business-quality discipline.
5. **Valuation / expectations** — Damodaran-style valuation and reverse-implied expectations, with Greenblatt-style quality/value ranking where structurally appropriate.
6. **Earnings / revisions / catalysts** — post-earnings drift, guidance, revisions, estimate changes, event timing, and reaction quality.
7. **Macro / news / tail risk** — real-time market, geopolitical, regulatory, cyber, liquidity, exchange, and issuer-level risk.
8. **Portfolio risk** — deterministic limits, correlation awareness, exposure constraints, cost awareness, and risk-of-ruin controls.

Gray/Vogel momentum and Clenow trend are deliberately tagged as the same **momentum/continuation correlation cluster**. They may confirm one another but may not be counted as independent bullish votes.

## Phase 1: Decision swarm

The new `swing_trading_command_center` preset establishes the research/control plane.

### Agents

- Point-in-Time Data Quality Guard
- Quantitative Momentum Specialist
- Trend/Regime/Volatility Specialist
- Relative-Value Specialist
- Fundamental Accounting Quality Specialist
- Valuation/Expectations Specialist
- Earnings/Catalyst Specialist
- Macro/News/Black-Swan Sentinel
- Portfolio Risk Governor
- Chief Investment Orchestrator

### Decision contract

Every specialist should converge toward a standardized output containing at least:

```json
{
  "target": "AAPL",
  "as_of": "ISO-8601 timestamp",
  "signal_family": "momentum|mean_reversion|fundamental|valuation|catalyst|macro_news|risk",
  "signal": "BULLISH|BEARISH|NEUTRAL|NO_EDGE",
  "confidence": 0,
  "horizon_trading_days": [3, 20],
  "thesis": "...",
  "evidence_for": [],
  "evidence_against": [],
  "entry_condition": "...",
  "invalidation_condition": "...",
  "data_quality": "HIGH|MEDIUM|LOW",
  "correlation_cluster": "...",
  "risk_factors": [],
  "missing_data": []
}
```

The final orchestrator must not increase confidence merely because multiple agents agree when they depend on the same factor or data transformation.

## Phase 2: $1,000 portfolio ledger and tracker

The portfolio tracker should become the system of record for all simulated, paper, and live positions.

### Required portfolio state

- Starting equity
- Current cash
- Net liquidation value
- Realized P/L
- Unrealized P/L
- Fees and slippage paid
- Gross exposure
- Net exposure
- Long exposure
- Short exposure
- Equity exposure
- Crypto exposure
- Per-sector exposure
- Per-signal-family exposure
- Correlated-cluster exposure
- Daily drawdown
- Weekly drawdown
- Peak-to-trough drawdown
- Open-risk dollars to all stops/invalidation levels
- Available risk budget

### Required position state

- Instrument and market
- Direction
- Quantity / fractional quantity
- Average entry price
- Current price
- Market value
- Stop / invalidation level
- Target zone
- Initial thesis
- Current thesis status
- Dominant signal family
- Entry timestamp
- Planned holding horizon
- Realized/unrealized P/L
- Fees/slippage
- Maximum favorable excursion
- Maximum adverse excursion
- Risk governor status
- Latest macro/news status
- Last full re-evaluation timestamp

### Trade journal / audit record

Every proposed or executed action must retain:

- Agent outputs used
- Data timestamps
- News sources and timestamps
- Final decision
- Rejected alternatives
- Position-sizing math
- Expected transaction cost
- Risk-governor ruling
- User/broker execution result
- Post-trade outcome
- Post-mortem tags

This record is required for later calibration and agent-performance attribution.

## Initial small-account risk policy

These are **conservative engineering defaults**, not proven optimal trading parameters. They should be treated as hypotheses and adjusted only through controlled validation.

| Control | Initial value |
|---|---:|
| Starting model equity | $1,000 |
| Target risk per trade | 0.50% of equity |
| Hard max risk per trade | 1.00% of equity |
| Max single-position market value | 25% of equity |
| Max gross exposure | 80% of equity |
| Max correlated-cluster exposure | 35% of equity |
| Max simultaneous positions | 4 |
| Daily soft loss stop | 2% |
| Weekly hard loss stop | 5% |
| Initial minimum planned reward/risk | ~1.8:1 |

For a $1,000 account, 0.50% target risk is $5 and 1.00% maximum risk is $10. The position size must be calculated from stop/invalidation distance and realistic execution cost, not from confidence alone.

Example:

```text
risk_budget = equity * risk_pct
risk_per_share = abs(entry - invalidation) + estimated_cost_per_share
shares = risk_budget / risk_per_share
```

If the broker does not support a viable fractional size or if fees/spread consume the edge, the correct output is **NO_TRADE**.

## Phase 3: Continuous real-time macro/news risk governor

The one-shot swarm can evaluate fresh news at decision time, but it is not a continuous protection system. A separate event-driven service must be built for open positions.

### Service responsibility

`LiveRiskSentinel` should run independently of the alpha swarm and continuously ingest/re-evaluate events while positions are open.

### Event sources

The implementation should support multiple source classes with provenance and deduplication:

- Exchange status / trading halts
- Company filings and investor-relations releases
- SEC/regulator announcements
- Central-bank and government releases
- High-quality financial news wires/APIs
- Earnings / guidance releases
- Economic-calendar events
- Crypto exchange status feeds
- Crypto protocol/security incident feeds
- Stablecoin and major on-chain stress alerts where relevant
- Broker/execution status

Do not make one social-media source or one news vendor a single point of failure.

### Event schema

```json
{
  "event_id": "...",
  "observed_at": "...",
  "published_at": "...",
  "source": "...",
  "source_quality": "PRIMARY|HIGH|MEDIUM|LOW",
  "scope": "SYSTEMIC|MARKET|SECTOR|ISSUER|ASSET|EXCHANGE",
  "severity": 0,
  "confidence": 0,
  "affected_symbols": [],
  "transmission_paths": [],
  "summary": "...",
  "corroborating_sources": [],
  "status": "UNCONFIRMED|CONFIRMED|RESOLVED"
}
```

### Risk actions

The deterministic policy engine should translate evaluated events into:

- `NO_ACTION`
- `WATCH`
- `BLOCK_NEW_ENTRIES`
- `REDUCE_POSITION`
- `HEDGE`
- `EXIT_POSITION`
- `EMERGENCY_EXIT`

The LLM/news agent can classify and explain events, but the actual broker action must pass a deterministic policy layer.

### Example hard triggers

Potential high-severity examples include:

- Confirmed issuer fraud/bankruptcy filing
- Regulatory trading halt
- Confirmed critical protocol exploit affecting the held crypto asset
- Exchange outage that prevents normal risk management
- Major stablecoin depeg affecting the trade's liquidity path
- Systemic banking/liquidity event
- Surprise geopolitical escalation with direct market transmission
- Unexpected central-bank action producing disorderly cross-asset repricing
- Broker/API failure combined with an unbounded open-risk condition

A severe headline alone should not force an exit. Source quality, direct relevance, confirmation, market transmission, liquidity, and current exposure all matter.

## Phase 4: Portfolio-level orchestration

The final system should separate three decisions:

1. **Is there an edge?** — research swarm.
2. **Is the risk acceptable?** — deterministic + agent risk governor.
3. **Can the trade be executed economically right now?** — execution layer.

### Candidate ranking

When multiple opportunities exist, the system should rank on expected net value rather than raw confidence:

```text
expected_net_edge
= expected_gross_edge
- fees
- spread
- slippage
- borrow/financing cost
- uncertainty_buffer
- concentration_penalty
```

### Correlation-aware portfolio logic

The portfolio layer must recognize that five different technology stocks or several momentum names may represent one underlying exposure. Risk should be budgeted by both instrument and factor/cluster.

## Phase 5: Execution adapters

Initial intended broker/exchange adapters:

- **Coinbase API** for crypto
- **Moomoo API** for equities where supported

Execution must remain disabled until shadow/paper acceptance tests pass.

### Execution adapter contract

Each adapter should expose a common interface for:

- Account/balance fetch
- Position fetch
- Quote/order-book fetch
- Place order
- Cancel order
- Get order status
- Trade/fill history
- Market-hours / exchange-status awareness
- Estimated fee
- Emergency flatten/reduce action

No agent should directly construct arbitrary broker calls. All orders must flow through an execution policy service with limits.

## Phase 6: Backtesting and validation

The system should be tested in layers rather than backtesting one giant LLM stack as a black box.

### Strategy-family validation

Validate each codifiable family independently:

- Momentum ranking
- Trend/regime filter
- Relative-value model
- Earnings/revision/catalyst rules
- Fundamental-quality filters
- Valuation priors

### Data requirements

- Point-in-time fundamentals
- Actual filing timestamps
- Historical index/universe membership
- Delisted securities
- Corporate actions
- Historical analyst estimates if used
- Realistic market-hours behavior

### Execution assumptions

- Bid/ask spread
- Slippage
- Commissions/fees
- Crypto taker/maker fees
- Borrow cost / locate availability for shorts
- Partial fills
- Overnight gaps
- Liquidity ceilings

### Statistical controls

- Walk-forward validation
- Completely untouched holdout period
- Parameter-sensitivity surfaces
- Regime segmentation
- Monte Carlo/permutation tests where appropriate
- Bootstrap confidence intervals
- Multiple-testing log
- Probability-of-backtest-overfitting / deflated-performance diagnostics where feasible

Track every material experiment. Do not optimize thousands of variants and report only the winner.

## Phase 7: Prospective shadow mode

Before live money:

1. Freeze decision rules and risk policy.
2. Run prospectively on live data with no execution.
3. Record every proposed trade and risk intervention.
4. Compare expected vs realized slippage, timing, signal decay, and correlation.
5. Require a minimum observation sample across different market regimes.
6. Only then enable constrained paper trading.
7. Only after paper acceptance should live trading be considered.

## Additional alpha/risk layers to add after core acceptance

The following can improve short-horizon context but should not be allowed to overwhelm the evidence-backed core until independently validated:

- Pivot high/low event learner
- VWAP stretch/reclaim logic
- Relative-volume and liquidity filters
- ATR stop/target modeling
- Signal-quality/no-trade gate
- Sector/industry relative strength
- Breadth and market-internals regime layer
- Options-implied volatility / skew where economically relevant
- Crypto funding/basis, liquidation heatmap, stablecoin flow, and on-chain stress
- Sentiment anomaly detector for under-the-radar names and event-driven attention spikes

Each should enter as a separate evidence family or modifier only after testing for incremental value beyond the existing stack.

## Agent-performance learning layer

The system should eventually score agents by **calibration and incremental value**, not whether their narrative sounded convincing.

Track:

- Brier/log-loss style calibration for probabilistic calls where possible
- Directional accuracy
- Expected vs realized move
- Signal decay by horizon
- Performance by regime
- False-positive and false-negative rates
- Incremental lift over baseline
- Correlation with other agents
- Veto quality: losses avoided vs good trades incorrectly blocked

Agent weights must be learned only from out-of-sample/prospective evidence and must remain bounded so that short hot streaks do not cause runaway reweighting.

## Non-negotiable safety and integrity rules

1. No invented market or fundamental data.
2. No silent parameter changes after seeing outcomes.
3. No double-counting correlated agents.
4. No averaging down outside a pre-defined risk budget.
5. No live execution without explicit adapter-level limits.
6. No treating historical win rate as a guarantee.
7. No bypass of the risk governor by the final orchestrator.
8. No fully autonomous emergency action based solely on an unverified single-source headline.
9. Every live/paper decision must be reconstructable from stored evidence.
10. `NO_TRADE` is a successful system outcome when uncertainty dominates edge.

## Recommended implementation sequence

### Sprint 001 — Strategy control plane
- Add research-backed swarm preset.
- Establish methodology boundaries and risk-governor precedence.
- Add architecture specification.

### Sprint 002 — Portfolio ledger
- Implement portfolio/position/order/trade Pydantic models.
- Persistent ledger and P/L accounting.
- $1,000 risk-budget calculator.
- Tests for fills, partial exits, fees, and drawdown.

### Sprint 003 — Deterministic risk policy engine
- Encode account/position/cluster/drawdown limits.
- Machine-readable risk decisions.
- Hard block/size-reduction/exit states.
- Unit and property tests.

### Sprint 004 — Live news/event ingestion
- Source adapters.
- Deduplication and provenance.
- Event severity model.
- Position-to-event relevance graph.

### Sprint 005 — Continuous LiveRiskSentinel
- Event loop and re-evaluation scheduler.
- Risk state transitions.
- Alerting.
- Shadow-only emergency-action recommendations.

### Sprint 006 — Coinbase/Moomoo execution abstraction
- Read-only account sync first.
- Paper execution.
- Idempotent order lifecycle.
- Kill switch.

### Sprint 007 — Strategy backtest harness
- Implement codifiable research-backed families.
- Walk-forward and cost-aware testing.
- Experiment registry and overfitting controls.

### Sprint 008 — Portfolio candidate engine
- Broad-stock/crypto scanner.
- Sentiment/catalyst discovery layer.
- Candidate prioritization by expected net edge.

### Sprint 009 — Prospective shadow portfolio
- Run the full stack live without money.
- Score agent calibration and risk interventions.

### Sprint 010 — Constrained live pilot
- Only after acceptance gates pass.
- Minimal capital and conservative limits.
- Human-observable kill switch and complete audit trail.
