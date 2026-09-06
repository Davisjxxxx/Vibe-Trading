# Research-Backed Stock Swing Trading Architecture

## Scope

This is the controlling architecture for the current build. The active control plane is **U.S. stock trading only**. Digital-asset execution and non-equity risk feeds are outside this feature.

The initial model portfolio is **$1,000**. The design objective is not maximum trade frequency. It is disciplined opportunity selection, capital preservation, auditable reasoning, and prospective validation.

Historical backtests are evidence, not guarantees. No strategy, author, factor, indicator, or AI agent is treated as infallible.

## Core operating principle

The system must separate five decisions:

1. **What market regime are we in?**
2. **Which validated methods fit that regime?**
3. **Which stocks deserve deeper review today?**
4. **Does technical structure support a trade now?**
5. **Does portfolio risk permit the trade?**

The system may recommend actions, but a human remains the final decision maker.

No component may place, cancel, reduce, or close a live order autonomously in the current design.

## Controlling workflow hierarchy

The primary daily workflow is `stock_daily_decision_desk`. The
`swing_trading_command_center` preset is a supporting Stock Deep-Dive Research
Committee invoked for candidates already surfaced by the daily desk.

```text
Market/Economic Regime
        ↓
Validated Strategy Suitability
        ↓
Daily Stock Research Agents
        ↓
Candidate Committee
        ↓
Ranked Stock Candidates
        ↓
Primary Technical Analysis
        +
Adversarial Technical Analysis
        ↓
Execution / Entry Quality Analysis
        ↓
Portfolio Risk / Circuit Breaker
        ↓
Human Decision Brief
        ↓
Human Executes or Rejects
```

The deep-dive committee provides evidence and a research brief; it is not a
second daily orchestrator and cannot produce an executable order.

## Daily decision workflow

The primary daily control plane is the `stock_daily_decision_desk` swarm.

### Stage 1 — Market regime diagnosis

The system evaluates:

- Broad index trend
- Breadth
- Volatility
- Rates and major macro events
- Sector leadership
- Correlation behavior
- Liquidity and execution conditions
- Whipsaw / failed-breakout behavior

The regime is classified as one of:

- `TREND_BULL`
- `TREND_BEAR`
- `RANGE_BOUND`
- `HIGH_VOLATILITY`
- `LOW_VOLATILITY`
- `MACRO_STRESS`
- `UNCERTAIN`

The regime diagnosis does not authorize trades. It informs which validated methods deserve more or less weight.

## Strategy portfolio and scorecard

The portfolio tracker must maintain a library of candidate trading methods and score them using evidence rather than recent anecdotes.

The first deterministic implementation is in `agent/src/portfolio/strategy_scorecard.py`.

### Required evidence

Each method should eventually retain:

- Trade count
- Win rate
- Expectancy in R
- Profit factor
- Sharpe or comparable risk-adjusted measure
- Maximum drawdown
- Average trade edge after realistic costs
- Walk-forward result
- Untouched holdout result
- Cost-stress result
- Overfitting warning status
- Regime-specific performance
- Last validation timestamp

### What the scorecard does

The scorecard ranks methods using:

- Expectancy
- Profit factor
- Drawdown
- Sample size
- Walk-forward robustness
- Holdout robustness
- Cost-stress robustness
- Current-regime fit

Win rate alone cannot promote a strategy.

A method can be classified as:

- `ACTIVE_CANDIDATE`
- `SHADOW_ONLY`
- `REJECTED`

A strong historical score does not permit silent live deployment. Strategy changes remain controlled changes.

### Regime-based pivoting

The system may recommend shifting emphasis between validated methods when current market conditions change. Examples include:

- Trend methods receiving more attention in healthy directional markets
- Mean-reversion methods receiving more attention in stable range-bound markets
- Reduced activity during extreme volatility or macro stress

The system must not assume that a reversal is due after a losing streak.

## Stage 2 — Daily research and candidate generation

Independent research streams produce candidate stocks from a liquid U.S. equity universe.

Initial streams include:

### Momentum / continuation

Research concepts include Gray/Vogel-style quantitative momentum and Clenow-style trend quality.

These are one correlated evidence family. Agreement improves confidence inside the family but is not counted as two independent votes.

### Relative value / mean reversion

Chan-style relative-value logic is used only when economic peer relationships and spread stability are defensible.

### Fundamental quality and catalysts

The system evaluates:

- Earnings
- Revisions
- Guidance
- SEC filings
- Balance-sheet condition
- Accounting quality
- Corporate events
- Valuation expectations
- Material changes in business outlook

Fundamental and catalyst analysis nominates candidates. It does not determine technical timing by itself.

### News and macro risk

The news layer evaluates fresh stock, sector, regulatory, exchange, geopolitical, and macro information.

It is a **notification and review system**, not an autonomous trade executor.

The parallel protection path is:

```text
Real-Time News / Risk Event
        ↓
Source Validation
        ↓
Relevance + Severity Analysis
        ↓
Portfolio / Candidate Mapping
        ↓
Risk Recommendation
        ↓
URGENT HUMAN NOTIFICATION
        ↓
Human Reviews and Decides
```

Each event must preserve its timestamp, source provenance, source quality,
corroboration status, affected symbols, transmission path, severity,
confidence, and objective de-escalation criteria. An urgent event may produce
`ENTRY_BLOCK`, `EXIT_REVIEW_REQUIRED`, or `URGENT_EXIT_REVIEW_REQUIRED`; it
must never autonomously liquidate an open position.

## Candidate committee

The candidate committee receives the independent research streams and ranks only the strongest opportunities for technical review.

It must:

- Group evidence by causal family
- Avoid double-counting correlated signals
- Require a clear edge hypothesis
- Require acceptable liquidity
- Record contradictory evidence
- Reject candidates with unresolved severe news risk
- Permit `NO_CANDIDATES` when the environment is poor

The daily queue should remain intentionally small so deeper technical review is focused on the highest-quality opportunities.

## Technical analysis sequence

The technical layer begins only after research has identified a candidate worth examining.

### Primary technical analyst

Evaluates:

- Multi-timeframe trend and structure
- Support and resistance
- Market structure
- Relative strength
- Moving-average context
- Momentum and RSI/divergence
- Volume behavior
- Relative volume and VWAP where appropriate
- Volatility
- ATR
- Gap behavior
- Breakout/retest quality
- Entry timing
- Invalidation levels
- Reward/risk

Indicators are evidence, not independent votes. The system must avoid stacking multiple indicators that measure the same underlying price behavior.

### Adversarial technical analyst

A second perspective challenges the setup and searches for:

- Failed breakout risk
- Divergence
- Exhaustion
- Poor trade location
- Nearby supply or demand
- False support or resistance
- Poor volume confirmation
- Gap-through-stop risk
- Volatility expansion
- Whipsaw regime
- Volatility instability
- Poor reward/risk
- Event risk
- Regime mismatch
- Crowded technical levels

The adversarial agent does not disagree mechanically. It must also state what evidence would invalidate its counter-thesis.

### Technical execution-quality analyst

This layer reconciles both technical perspectives and proposes:

- Entry condition
- Invalidation / stop logic
- Target zone
- Expected holding period
- Spread and slippage considerations
- Liquidity constraints
- Gap-risk considerations

It produces a proposed plan only. It never submits an order.

## Portfolio risk governor

The risk governor has precedence over alpha-seeking agents.

It evaluates:

- Current portfolio equity
- Daily and weekly P/L
- Consecutive losses
- Strategy-family health
- Market regime
- Whipsaw conditions
- Liquidity
- Slippage and spread quality
- Correlated exposure
- Open risk to stops
- News alerts

### Portfolio states

The governor classifies the account as:

- `NORMAL`
- `CAUTION`
- `DEFENSIVE`
- `LOCKOUT`
- `RECOVERY`

### Initial engineering defaults

These are starting hypotheses, not proven optimal settings:

| Control | Initial value |
|---|---:|
| Starting model equity | $1,000 |
| Target risk per trade | 0.50% of equity |
| Hard max risk per trade | 1.00% of equity |
| Max concurrent positions | 4 |
| Max correlated-cluster exposure | 35% |
| Soft daily loss stop | 2% |
| Hard weekly loss stop | 5% |

For a $1,000 account, the default target planned loss is about **$5 per trade**, with a hard ceiling of about **$10** before later validation changes those limits.

Position size must be derived from invalidation distance and expected trading cost, not confidence alone.

```text
risk_budget = equity * risk_pct
risk_per_share = abs(entry - invalidation) + estimated_cost_per_share
shares = risk_budget / risk_per_share
```

## Hyper-volatility and loss-streak circuit breaker

The system must distinguish random variance from evidence that the strategy or market environment has become hostile.

It should evaluate:

- Consecutive losing trades
- Consecutive losing days
- Whether losses are concentrated in one strategy family
- Realized volatility expansion
- Repeated breakout / stop / reversal patterns
- Spread widening
- Slippage deterioration
- Cross-stock correlation convergence
- Breadth deterioration
- Market-wide news stress

### State behavior

- `NORMAL`: standard validated risk limits
- `CAUTION`: reduce size or raise evidence threshold
- `DEFENSIVE`: materially reduce risk and trade frequency
- `LOCKOUT`: no new trade recommendations
- `RECOVERY`: limited re-entry after objective normalization

A losing streak does **not** imply that a reversal is due.

A restart from `LOCKOUT` requires evidence that volatility, whipsaw, liquidity, strategy-family performance, and relevant news risk have normalized.

## Real-time news notification model

A future continuous service may monitor fresh information while positions are open, but it must remain human-in-the-loop.

### Alert classes

- `CLEAR`
- `REVIEW`
- `HIGH_PRIORITY`
- `URGENT`

### Each alert should include

- Source
- Timestamp
- Source quality
- Affected symbols
- Direct relevance
- Transmission path
- Confidence
- Corroboration status
- Suggested human review question
- What would de-escalate the alert

### Human-in-the-loop rule

The system may recommend:

- Do nothing
- Delay entry
- Block new entries
- Reduce exposure
- Review an exit

But the human must approve the actual action.

An urgent headline by itself is not sufficient for an automatic sale. Source quality, confirmation, relevance, market reaction, current exposure, and liquidity all matter.

## Final human decision brief

Every actionable recommendation must end in a concise brief containing at least:

- Symbol
- Proposed action
- Dominant thesis
- Why today
- Current market regime
- Strategy method
- Technical entry condition
- Invalidation
- Target zone
- Proposed position risk
- Evidence for
- Evidence against
- News alert status
- Portfolio risk state
- Risk-governor action
- Key unknowns
- Human review checklist

Every actionable brief must include:

```text
HUMAN_APPROVAL_REQUIRED: true
DO_NOT_EXECUTE_AUTONOMOUSLY: true
```

Supported recommendation actions include `CLEAR`, `WATCH`, `CAUTION`,
`NO_TRADE`, `ENTRY_BLOCK`, `SIZE_REDUCE_RECOMMENDED`,
`EXIT_REVIEW_REQUIRED`, `URGENT_REVIEW_REQUIRED`, and
`URGENT_EXIT_REVIEW_REQUIRED`. If the risk governor blocks new entries or
returns no-trade, the final brief must preserve that block. Open-position risk
events require human review; they do not authorize automatic liquidation.

## Portfolio tracker requirements

The portfolio tracker should become the system of record for simulated, paper, and eventually live stock positions.

Required portfolio state includes:

- Starting equity
- Cash
- Net liquidation value
- Realized P/L
- Unrealized P/L
- Fees and slippage
- Gross and net exposure
- Sector exposure
- Strategy-family exposure
- Correlated-cluster exposure
- Daily drawdown
- Weekly drawdown
- Peak-to-trough drawdown
- Open risk to stops
- Available risk budget
- Current circuit-breaker state

Required position state includes:

- Symbol
- Direction
- Quantity
- Average entry
- Current price
- Market value
- Stop / invalidation
- Target
- Initial thesis
- Current thesis status
- Strategy method
- Signal family
- Entry timestamp
- Planned horizon
- Realized and unrealized P/L
- Fees and slippage
- Maximum favorable excursion
- Maximum adverse excursion
- News alert status
- Risk state
- Last re-evaluation time

## Trade and decision journal

Every proposed or executed action must retain:

- Research outputs
- Data timestamps
- News sources and timestamps
- Strategy-scorecard state
- Candidate ranking
- TA primary view
- TA counter-thesis
- Final technical plan
- Risk-governor ruling
- Human approval or rejection
- Execution result when applicable
- Post-trade outcome
- Postmortem tags

This evidence is necessary to learn which agents, strategy families, and vetoes add real incremental value.

## Backtesting and validation

Each codifiable strategy family should be tested separately before the combined system is judged.

Required controls include:

- Point-in-time data
- Historical universe membership
- Delisted stocks where appropriate
- Corporate actions
- Actual filing timestamps
- Historical estimates if used
- Bid/ask spread
- Slippage
- Commissions
- Partial fills
- Overnight gaps
- Liquidity ceilings
- Walk-forward validation
- Untouched holdout periods
- Parameter-sensitivity testing
- Regime segmentation
- Bootstrap confidence intervals
- Multiple-testing log
- Overfitting diagnostics where feasible

Track every material experiment. Do not optimize many variants and report only the winner.

## Prospective validation sequence

Before live capital:

1. Freeze the strategy rules and risk policy.
2. Run the daily desk prospectively with live data and no execution.
3. Record every candidate, recommendation, veto, and alert.
4. Compare expected vs realized behavior.
5. Evaluate performance across different regimes.
6. Run constrained paper trading.
7. Only after acceptance gates pass should live execution be considered.

## Future read-only account integration

The only near-term account integration under consideration is **Moomoo API
where supported**, beginning with read-only account and position
synchronization. This sprint does not authorize broker order operations.

The read-only integration may support:

- Account and balance fetch
- Position fetch
- Quote fetch
- Market-hours awareness

Any later paper or live adapter requires separate validation gates and human
approval. No current agent may submit, cancel, reduce, close, or flatten a
live position.

## Deferred technical enhancements

The following can be added after the core stock system is stable and independently tested:

- Pivot high/low event learner
- VWAP stretch/reclaim logic
- Relative-volume and liquidity filters
- ATR stop/target modeling
- Signal-quality / no-trade gate
- Sector and industry relative strength
- Breadth and market internals
- Options-implied volatility and skew where relevant
- Sentiment and attention anomaly discovery

Each enhancement must demonstrate incremental value beyond the existing stack before receiving decision weight.

## Non-negotiable rules

1. Stock trading only for the current build.
2. No invented market, fundamental, or news data.
3. No silent parameter changes after seeing outcomes.
4. No double-counting correlated evidence.
5. No averaging down outside a predefined risk budget.
6. No strategy promotion based on win rate alone.
7. No treating a losing streak as proof a reversal is due.
8. No bypass of the portfolio risk governor.
9. No autonomous trade action from a news alert.
10. Every actionable recommendation requires explicit human approval.
11. Every decision must be reconstructable from stored evidence.
12. `NO_TRADE` and `NO_CANDIDATES` are valid successful outcomes.

## Recommended next implementation sprints

### Sprint 002 — Persistent Portfolio Ledger
- Cash, positions, fills, realized/unrealized P/L, fees, and slippage
- Maximum favorable/adverse excursion, drawdown, and strategy attribution
- Risk-to-stop and exposure accounting

### Sprint 003 — Strategy Experiment Registry + Backtest Integration
- Connect the existing backtest engine to the strategy scorecard
- Persist every material experiment and parameter set
- Regime segmentation, walk-forward, untouched holdout, and cost stress
- Overfitting diagnostics and controlled method promotion/demotion

### Sprint 004 — Daily Stock Universe / Scanner Runtime
- U.S. stock universe, liquidity, price, and relative-volume filters
- Catalyst discovery, broad screening, and candidate queue

### Sprint 005 — Continuous news notification service
- Source adapters
- Provenance and deduplication
- Symbol relevance mapping
- Alert delivery
- Human acknowledgement workflow

### Sprint 006 — Deterministic portfolio risk engine
- Daily/weekly limits
- Loss-streak logic
- Regime stress logic
- Exposure clustering
- NORMAL / CAUTION / DEFENSIVE / LOCKOUT / RECOVERY transitions

### Sprint 007 — Moomoo Read-Only Account / Position Sync Where Supported
- Account and position synchronization only
- No order placement, cancellation, or autonomous execution

### Sprint 008 — Prospective shadow portfolio
- Full daily workflow on live data without capital
- Strategy and agent calibration
- Risk-veto evaluation

### Sprint 009 — Human-Approved Paper Trading
- Paper actions require explicit human approval
- Complete decision and execution audit trail

### Sprint 010 — Constrained Live Pilot Consideration
- Consider only after all validation gates pass
- Retain explicit human approval and bounded controls
