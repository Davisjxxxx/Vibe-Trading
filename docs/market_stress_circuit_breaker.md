# Market Stress and Loss-Streak Circuit Breaker

## Purpose

Prevent the trading system from continuing to deploy capital when market conditions become hostile to the system's tested edge or when realized losses indicate that the current regime, execution environment, or strategy calibration may be unreliable.

This control is deliberately conservative for a small starting account. It is a deterministic risk policy, not a discretionary LLM opinion.

## Core Principle

A sequence of losses does **not** imply that a reversal is due. Loss streaks are evidence to investigate, not a reason to increase risk.

The system must distinguish among:

1. Normal statistical variance.
2. A hostile market regime.
3. Strategy-specific degradation.
4. Execution/liquidity degradation.
5. Data or infrastructure problems.
6. A genuine external shock or black-swan event.

## Risk-State Machine

The portfolio operates in one of five states:

- `NORMAL`
- `CAUTION`
- `DEFENSIVE`
- `LOCKOUT`
- `RECOVERY`

The Portfolio Risk Governor has final authority over transitions. Alpha agents cannot override `LOCKOUT`.

### NORMAL

Normal validated risk budgets and position limits apply.

### CAUTION

Triggered by elevated but not extreme stress. New positions remain possible, but size and trade frequency are reduced.

Recommended initial behavior:

- Reduce per-trade risk by approximately 25-50%.
- Require stronger signal quality and cleaner execution conditions.
- Avoid marginal setups and crowded correlated exposure.
- Avoid opening immediately before known binary macro events unless the strategy was specifically validated for that condition.

### DEFENSIVE

Triggered when market structure or recent portfolio behavior suggests materially elevated uncertainty.

Recommended initial behavior:

- Reduce normal per-trade risk by at least 50%.
- Limit simultaneous positions.
- Block low-liquidity and high-slippage candidates.
- Require independent evidence families rather than several correlated technical confirmations.
- Prefer preservation of capital over opportunity capture.

### LOCKOUT

No new discretionary directional positions may be opened.

Existing positions are surfaced for human review according to their stops,
event risk, and risk policy. The system may recommend reducing or closing
exposure, but it may not execute that action autonomously.

LOCKOUT may be triggered by any of the following classes of evidence:

- Daily hard-loss threshold reached.
- Rolling multi-day drawdown threshold reached.
- Loss streak combined with abnormal market stress.
- Severe execution degradation.
- Extreme volatility or volatility-of-volatility.
- Abrupt correlation convergence across risk assets.
- Severe breadth deterioration or disorderly price action.
- Exchange/broker/data-feed instability.
- Confirmed systemic, geopolitical, regulatory, cyber, liquidity, or issuer-specific shock.
- Data-integrity failure.

### RECOVERY

A probationary state after LOCKOUT. Trading does not return immediately to full risk.

Recommended initial behavior:

- Resume at 25-50% of normal risk.
- Permit only the highest-quality setups.
- Require objective normalization of stress metrics and execution quality.
- Require no unresolved infrastructure/data incidents.
- Escalate immediately back to LOCKOUT if losses continue under stressed conditions.

Only after predefined recovery evidence is satisfied should the system return to `NORMAL`.

## Market-Stress Inputs

The stress engine should evaluate multiple independent dimensions rather than rely on one volatility index or one price move.

### Volatility

Examples:

- Realized volatility percentile versus recent history.
- Intraday range expansion.
- ATR expansion.
- Gap frequency and gap magnitude.
- Implied volatility where available.
- Volatility-of-volatility.

### Market Structure

Examples:

- Bid/ask spread expansion.
- Slippage versus expected slippage.
- Abnormal order-book thinning where data are available.
- Rapid failed breakouts and failed breakdowns.
- Increased stop-out/reversal frequency.
- Excessive intraday whipsaw.

### Breadth and Correlation

Examples:

- Advance/decline breadth deterioration.
- Sector participation collapse.
- Dispersion changes.
- Cross-asset correlation spikes.
- Normally diversifying assets suddenly moving together.

### Macro/Event Stress

Examples:

- Surprise central-bank decisions.
- CPI/jobs/major macro releases with abnormal market reaction.
- Geopolitical escalation.
- Banking or sovereign stress.
- Major regulatory intervention.
- Trading halts or exchange outages.

## Loss-Streak Logic

Loss streaks should modify risk only in combination with statistical expectations and regime evidence.

### Single Loss

A single planned stop-out under normal conditions does not automatically change the global risk state.

However, if the market is already classified as `EXTREME_STRESS`, one full planned loss may be sufficient to stop new trading for the rest of that session. This is an intentionally conservative small-account rule and must be backtested before live deployment.

### Consecutive Losing Days

Initial hypothesis for validation:

- Two consecutive losing sessions: at minimum enter `CAUTION`; next eligible trades use reduced risk.
- Three consecutive losing sessions, or a materially abnormal rolling loss measured in R-multiples: enter `LOCKOUT` pending diagnosis and recovery criteria.

The system must **not** assume the next day is more likely to reverse simply because prior days lost.

### Strategy-Level Loss Streaks

Losses should be attributed by strategy family and regime.

For example, if momentum trades are failing while mean-reversion trades are behaving normally, the system should be able to disable or downweight the momentum family without necessarily shutting down the entire portfolio.

The reverse also applies.

## R-Multiple Accounting

Loss controls should be expressed in both dollars and normalized `R` units.

For a $1,000 model account, current draft hypotheses include:

- Normal risk per trade: approximately 0.50% of equity.
- Absolute maximum planned risk per trade: approximately 1.00%.
- Daily soft-loss threshold: approximately 2%.
- Weekly hard-loss threshold: approximately 5%.

These are **initial hypotheses only** and must be validated using realistic fees, slippage, gap risk, and historical/prospective testing before live use.

R-based controls allow the system to recognize deterioration independently of account size.

Examples of metrics to track:

- Consecutive losing trades.
- Consecutive losing sessions.
- Rolling 5-day R.
- Rolling 20-trade R.
- Expectancy by strategy family.
- Hit rate versus expected hit-rate confidence interval.
- Average adverse excursion.
- Stop-out frequency followed by immediate reversal.
- Realized versus expected slippage.

## Whipsaw Detection

The system should explicitly measure the pattern often described subjectively as "the market is hunting stops."

The system should not assume malicious targeting of an individual trader. Instead it should detect measurable conditions such as:

- Price repeatedly crossing entry/stop zones and reversing.
- Elevated intraday noise relative to directional movement.
- Failed breakout frequency.
- Stop-outs followed quickly by movement toward the original target.
- Spread/slippage expansion.
- High realized volatility with low directional efficiency.

A persistent increase in these metrics is evidence that the strategy may be operating in an unfavorable microstructure regime.

## Recovery Gate

A LOCKOUT cannot end merely because a fixed amount of time passed or because several losing days make a reversal feel likely.

Recovery should require objective evidence such as:

1. Market-stress score falls below the relevant threshold for a defined observation window.
2. Liquidity/spreads/slippage normalize.
3. Data and broker/exchange infrastructure are healthy.
4. No unresolved CRITICAL macro/news alert exists.
5. Strategy-family diagnostics show no obvious structural failure.
6. Paper/shadow signals demonstrate acceptable behavior during the observation period where practical.

The system then enters `RECOVERY`, not `NORMAL`.

## Deterministic Enforcement

The following precedence must be enforced in code:

```text
DATA_INVALID / INFRASTRUCTURE_FAILURE
        ↓
LOCKOUT
        ↓
CRITICAL NEWS / SYSTEMIC RISK
        ↓
URGENT HUMAN EXIT REVIEW
        ↓
MARKET-STRESS STATE
        ↓
PORTFOLIO LOSS / DRAWDOWN STATE
        ↓
STRATEGY-FAMILY HEALTH
        ↓
ALPHA SIGNALS
```

Alpha confidence cannot override a higher-order risk state.

## Anti-Overfitting Requirement

Thresholds must not be optimized solely to maximize historical return.

Validation should favor broad, stable parameter regions and robustness across:

- bull markets,
- bear markets,
- high-volatility regimes,
- low-volatility regimes,
- event shocks,
- U.S. equities,
- different liquidity environments.

If the circuit breaker only works under one narrow threshold combination, it should be treated as overfit.

## Required Telemetry

Every state change must record:

- timestamp,
- prior state,
- new state,
- triggering metrics,
- loss history,
- market-stress readings,
- strategy-family health,
- relevant news/events,
- positions affected,
- action taken,
- recovery requirements,
- later counterfactual outcome where measurable.

This allows the system to evaluate whether a risk shutdown saved capital or unnecessarily blocked profitable trades.

## Implementation Boundary

This document defines the acceptance requirements for the future deterministic Portfolio Risk Engine and LiveRiskSentinel integration.

It does **not** claim that the current swarm preset continuously enforces these controls yet. Live execution must remain disabled until the portfolio ledger, deterministic risk engine, market-stress telemetry, read-only account integration, backtests, shadow mode, and recovery-state tests are implemented and accepted. News and risk events produce recommendations and urgent human notifications; they do not execute liquidation.
