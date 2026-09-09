Alyntiq — Development Roadmap

Alyntiq is built in sequential phases.

Do not skip foundational phases unless explicitly documented.

⸻

Phase 0 — Project Foundation

Create:

* backend foundation
* FastAPI
* configuration
* PostgreSQL
* Redis
* Docker
* testing
* linting
* CI

Detailed file:

docs/phases/PHASE_00_FOUNDATION.md

⸻

Phase 1 — Historical Market Data

Create a historical market data ingestion pipeline.

Provider:

Alpaca.

Initial assets:

AAPL
MSFT
NVDA
SPY
QQQ

Initial timeframe:

1D

Later:

1H
15m
5m

Core concepts:

* provider abstraction
* OHLCV storage
* idempotent ingestion
* data validation
* historical queries

Detailed file:

docs/phases/PHASE_01_MARKET_DATA.md

⸻

Phase 2 — Exploratory Data Analysis

Analyze historical data.

Study:

* returns
* volatility
* volume
* drawdowns
* correlations
* autocorrelation
* market behavior

Produce research documentation.

⸻

Phase 3 — Feature Engineering

Create reproducible financial features.

Groups:

* returns
* momentum
* moving averages
* volatility
* technical indicators
* volume
* market context

Introduce feature versioning.

⸻

Phase 4 — Prediction Problem

Define ML targets.

Initial task:

binary classification.

Example:

close(t+1) > close(t)

Later:

multi-period targets.

⸻

Phase 5 — Baseline Models

Implement:

* random baseline
* majority-class baseline
* logistic regression
* decision tree

Use walk-forward validation.

Introduce MLflow.

⸻

Phase 6 — Advanced Models

Implement:

* Random Forest
* XGBoost
* LightGBM

Introduce:

* Optuna
* feature importance
* model leaderboard

⸻

Phase 7 — Backtesting Engine

Build a custom backtesting engine.

Core entities:

* Strategy
* Signal
* Order
* Fill
* Trade
* Position
* Portfolio

Simulate:

* commissions
* slippage

⸻

Phase 8 — Baseline Trading Strategies

Implement:

* Buy & Hold
* Moving Average Crossover
* RSI Mean Reversion
* Momentum
* Random Strategy

Compare all strategies consistently.

⸻

Phase 9 — ML Trading Strategy

Convert model probabilities into trading signals.

Example:

P(up) > threshold → BUY

P(up) < threshold → SELL

Thresholds must be selected using validation data only.

⸻

Phase 10 — Risk Engine

Introduce independent risk management.

Possible rules:

* max position size
* max exposure
* max daily loss
* max drawdown
* stop loss
* take profit
* max trades per day
* minimum cash reserve

⸻

Phase 11 — Portfolio Engine

Support:

* multiple assets
* cash
* positions
* realized PnL
* unrealized PnL
* equity
* exposure
* position sizing

⸻

Phase 12 — Paper Trading

Connect strategies to Alpaca Paper Trading.

Introduce:

BrokerInterface

AlpacaPaperBroker

Research and paper trading logic should share the same strategy layer.

⸻

Phase 13 — Real-Time Market Data

Connect to live market feeds using WebSockets.

Handle:

* reconnects
* duplicates
* out-of-order events
* API failures
* rate limits

⸻

Phase 14 — Trading Audit Trail

Persist every trading decision.

Track:

* timestamp
* symbol
* prediction
* confidence
* model version
* strategy version
* feature version
* risk decision
* order
* execution

Every trade must be explainable.

⸻

Phase 15 — Frontend Dashboard

Create a Next.js dashboard.

Main pages:

* overview
* portfolio
* positions
* trades
* strategies
* models
* market

⸻

Phase 16 — Strategy Competition

Give multiple strategies identical starting capital.

Compare:

* Buy & Hold
* Momentum
* Mean Reversion
* ML
* Hybrid strategies

⸻

Phase 17 — Market Regime Detection

Detect market environments.

Possible techniques:

* KMeans
* Gaussian Mixture Models
* HDBSCAN

Potential regimes:

* bull
* bear
* sideways
* high volatility
* low volatility

⸻

Phase 18 — News and NLP

Introduce news analysis.

Pipeline:

News
→ Deduplication
→ Entity Extraction
→ Ticker Mapping
→ NLP / LLM Analysis
→ Structured Signal

LLMs must not directly execute trades.

⸻

Phase 19 — Hybrid Strategy

Combine:

* quantitative features
* ML predictions
* market regime
* news sentiment

Compare against pure strategies.

⸻

Phase 20 — Deep Learning

Research advanced time-series models.

Potential models:

* LSTM
* GRU
* Temporal CNN
* Temporal Fusion Transformer
* time-series Transformers

Deep learning must be compared against simpler baselines.

⸻

Phase 21 — Model Registry

Introduce model lifecycle.

States:

* candidate
* staging
* production
* retired

Only production models may operate in paper trading.

⸻

Phase 22 — Observability

Track:

* prediction volume
* trade volume
* rejected trades
* API latency
* model latency
* ingestion failures
* WebSocket reconnects
* portfolio drawdown
* PnL

Introduce OpenTelemetry.

⸻

Phase 23 — Data and Model Drift

Compare live distributions against training distributions.

Track:

* feature drift
* prediction drift
* volatility changes
* regime changes

⸻

Phase 24 — Deployment

Create production-ready deployment.

Potential AWS architecture:

* ECS or EC2
* RDS PostgreSQL
* ElastiCache
* S3
* CloudWatch

⸻

Phase 25 — CI/CD

Expand GitHub Actions.

Pull Request checks:

* lint
* tests
* integration tests
* feature tests
* leakage tests
* backtesting sanity tests
* Docker build

Main:

* build
* push
* deploy

⸻

Phase 26 — Final Research Report

Produce a professional research report.

Document:

* hypotheses
* models
* strategies
* results
* rejected ideas
* limitations
* backtesting performance
* paper trading performance
* lessons learned
* future research

Do not claim that Alyntiq “beats the market” without extraordinary evidence.

Use language such as:

* historical result
* experimental result
* paper trading result
* observed performance