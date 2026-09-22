# Alyntiq — Final Research Report

## Conclusion

Alyntiq is a reproducible research, historical-backtesting, and paper-trading foundation. It is **not** evidence that an AI model beats the market, and this repository does not contain enough persisted experimental output to support a profitability claim. The committed numerical evidence is descriptive historical market-data analysis. Models, strategies, risk, and execution components are controlled ways to produce later experiments, not experiment results by themselves.

The project remains paper-only. No live-trading path is implemented or authorized.

## Research questions

1. Can versioned, point-in-time daily inputs support reproducible next-day direction experiments without future-information leakage?
2. How do simple, tree-based, and temporal classifiers compare under chronological validation and an untouched final holdout?
3. Do technical, model-driven, and hybrid strategies perform acceptably under identical next-open execution and explicit cost assumptions?
4. Can paper orders retain model, strategy, risk, and audit lineage while remaining isolated from real-money execution?

Questions 1 and 4 have implementation and automated-test evidence. Questions 2 and 3 require recorded experiment runs before they can be answered empirically.

## Evidence inventory

| Evidence | Status in the repository | Interpretation |
| --- | --- | --- |
| Historical EDA | Recorded in [market_data_analysis.md](market_data_analysis.md) | Descriptive evidence only |
| Feature and target definitions | Implemented as `features-v1` and `targets-v1` | Reproducible input and label contracts |
| Model evaluators | Implemented with MLflow tracking | No committed MLflow runs or leaderboard artifacts |
| Backtest and strategy comparison | Implemented and tested | No committed strategy-comparison output |
| Paper broker, registry, risk, audit | Implemented and tested | No paper orders, fills, or performance history |
| Drift and OpenTelemetry | Implemented and tested | No persisted operational or drift observations |

There is no versioned market-data dump, model artifact, MLflow run directory, backtest report, strategy leaderboard, or paper-trading execution record in this repository. This report therefore does not infer predictive quality, risk-adjusted return, or paper performance from the presence of the implementation.

## Dataset and lineage

The recorded EDA queried PostgreSQL on 2026-09-10. It used daily raw IEX data from `alpaca:iex:raw` for AAPL, MSFT, NVDA, SPY, and QQQ: 1,539 bars per symbol (7,695 total) from 2020-07-27 through 2026-09-10. Although the requested start was 2020-01-01, the available IEX coverage began later. The data is unadjusted (`raw`), so corporate actions can affect long-horizon returns and drawdowns.

`features-v1` contains trailing returns, momentum, moving-average, volatility, technical, volume, and SPY/QQQ market-context inputs. Its immutable identity includes symbol, timestamp, source, timeframe, and feature version. Warm-up rows remain null, and tests verify that later bars cannot alter an earlier feature row.

`targets-v1` is the separately stored label `direction_1d(t) = close(t + 1) > close(t)`. The final observation has a null target. An experiment must explicitly retain its source, timeframe, feature version, target version, and dataset version.

## Observed descriptive data results

These values reproduce the committed EDA, not a model or strategy evaluation.

| Symbol | Mean close | Annualized volatility | Maximum drawdown |
| --- | ---: | ---: | ---: |
| AAPL | 194.15 | 41.66% | -78.88% |
| MSFT | 347.24 | 27.50% | -37.54% |
| NVDA | 316.95 | 69.24% | -92.30% |
| SPY | 501.07 | 16.54% | -25.38% |
| QQQ | 425.44 | 22.58% | -35.63% |

NVDA had the highest sample volatility and deepest drawdown; SPY had the lowest sample volatility and shallowest drawdown in this five-instrument sample. Lag-one return autocorrelation was near zero for every symbol (from -0.0410 for NVDA to 0.0031 for MSFT). QQQ and SPY had daily-return correlation of 0.9346, so they should not be treated as independent diversification exposures in this sample. These findings describe raw, daily historical data; they do not estimate future risk or return.

SPY was above its 50-session moving average in 69.72% of eligible sessions and in the high 21-session-volatility state in 49.32%. This is a historical descriptive regime view, not a validated predictive signal.

## Experimental methods available

### Predictive models

The pipeline evaluates random and majority-class controls, logistic regression, decision trees, Random Forest, XGBoost, LightGBM, LSTM, GRU, temporal CNN, and a small Transformer. It uses timestamp-aligned expanding walk-forward splits with a mandatory one-timestamp gap for the next-day label. Advanced-model optimization uses earlier folds only; the final chronological fold is reserved for one holdout evaluation. Temporal windows remain within a symbol and each fold's scaler is fitted only on its training data.

No predictive metrics or MLflow artifacts from a run are committed here. The available evaluation controls cannot establish that a complex model outperforms a baseline.

### Strategies, benchmarks, and backtesting

Historical benchmarks are Buy & Hold, moving-average crossover, RSI mean reversion, momentum, and a seeded random strategy. The model-threshold strategy consumes versioned, point-in-time probabilities; thresholds are selected from labeled validation predictions before holdout use. The hybrid strategy combines this proposal with quantitative context, descriptive regimes, and prior news signals.

Competitors receive the same completed bars, cash, whole-share quantity, commission, slippage, and trading-days assumptions in isolated fresh backtests. A completed-bar signal fills at the next available open. The engine reports return, volatility, Sharpe, Sortino, maximum drawdown, trade count, win rate, profit factor, and closed-trade statistics when defined.

No benchmark, ML, or hybrid-comparison output is committed. There are no backtesting results to rank, no verified winning strategy, and no basis to claim positive expected or realized performance.

### Paper-trading controls

An independent pre-trade risk engine evaluates proposals before an order can progress. Model-driven paper orders also require a registry record in `production` state. The Alpaca adapter is permanently bound to the paper endpoint and rejects every environment other than `paper`; the execution, audit, and broker boundaries do not expose a live endpoint.

No paper orders, account snapshots, fills, or PnL observations are stored in the repository. Paper-trading performance is therefore **not available**. Simulated fills, when collected, would be observations rather than evidence of live-market performance.

## What worked

- Versioned feature, target, model, strategy, and audit lineage makes experimental inputs and decisions traceable.
- Chronological evaluation, target gaps, next-open fills, and validation-only threshold selection explicitly address common look-ahead paths.
- Shared assumptions and fresh state per competitor support fairer historical comparisons.
- Model, strategy, risk, portfolio, and execution responsibilities remain separated.
- The paper-only endpoint, registry gate, CI safety checks, and unprivileged runtime images provide safety controls around the research system.

## Rejected hypotheses and evidence gaps

- **"AI beats the market." Rejected as unsupported.** No persisted predictive, backtest, or paper-trading result supports the claim.
- **"A complex model beats a simple baseline." Unanswered.** Comparative MLflow leaderboards and untouched-holdout values are absent.
- **"A hybrid strategy improves risk-adjusted performance." Unanswered.** No recorded like-for-like strategy-competition result exists.
- **"Paper trading validates live deployment." Rejected.** No paper history is recorded, and paper fills would not validate live execution conditions.
- **"A drift alert proves model degradation." Rejected.** PSI, volatility, prediction, and regime comparisons identify distributional change, not predictive degradation.

## Limitations

- The recorded data analysis covers five US instruments, daily bars, a single IEX feed, and 2020-07-27 to 2026-09-10; it is not a broad-market or intraday study.
- Raw prices require a documented corporate-action adjustment policy before long-horizon comparisons.
- The historical simulator is single-symbol and long-only; it does not model liquidity, partial fills, shorting, leverage, intraday execution, or order-book effects.
- Commission and slippage are explicit assumptions, not calibrated market-cost estimates.
- There are no committed artifacts from model training, optimization, backtests, paper execution, telemetry export, or drift monitoring.
- The dashboard is presentation-only; Prometheus/Grafana dashboards, alert delivery, model serving, a worker, and deployment automation are not implemented.

## Recommended next research cycle

1. Create a versioned dataset snapshot with explicit adjustment and survivorship policy.
2. Run every model family on fixed walk-forward folds, retain MLflow artifacts, and publish a holdout-only predictive leaderboard including simple controls.
3. Pre-register strategy parameters, dates, costs, quantity, and benchmarks; then retain like-for-like backtest reports with drawdown and trade-count context.
4. Promote a model only after evidence review, then collect bounded paper-trading history with audit records, drift reports, and operational telemetry.
5. Compare paper observations with backtest assumptions before considering new scope. Live-money execution remains outside this roadmap and requires a separate decision.

## Verification status

The automated tests verify leakage controls, chronological validation, backtest timing, risk decisions, paper-endpoint enforcement, model lifecycle gating, telemetry interfaces, drift calculations, CI safety, and image builds. They validate implementation behavior, not market performance.
