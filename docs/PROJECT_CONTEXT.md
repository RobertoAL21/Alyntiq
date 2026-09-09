Alyntiq — Project Context

Overview

Alyntiq is an AI-powered quantitative research and paper trading platform.

The goal is not to create a system that claims to predict the stock market perfectly.

The goal is to build a professional research platform capable of designing, testing, deploying and evaluating intelligent trading strategies under controlled and measurable conditions.

Main Capabilities

Alyntiq will eventually support:

* historical market data ingestion
* real-time market data
* financial feature engineering
* Machine Learning experiments
* model versioning
* walk-forward validation
* backtesting
* quantitative trading strategies
* risk management
* portfolio simulation
* paper trading
* strategy comparison
* market regime detection
* news and sentiment analysis
* model registry
* observability
* drift detection
* frontend analytics
* cloud deployment
* CI/CD
* reproducible research

Long-Term Flow

Market Data
↓
Data Validation
↓
Feature Engineering
↓
ML Models
↓
Predictions
↓
Trading Strategy
↓
Risk Engine
↓
Execution Engine
↓
Paper Broker
↓
Portfolio
↓
Analytics

Research Philosophy

Alyntiq must prioritize evidence over assumptions.

Complex models must not automatically be considered better than simple models.

Every advanced model should be compared against simple baselines.

Examples:

* random baseline
* majority-class baseline
* logistic regression
* buy and hold
* moving average strategies
* random trading strategy

If a complex model cannot outperform a reasonable baseline under controlled evaluation, that result should be documented rather than hidden.

Core Evaluation Principle

Prediction accuracy is not the same as trading profitability.

Model metrics and trading metrics must be evaluated independently.

Scope

Initial supported markets:

US equities and ETFs.

Initial symbols may include:

* AAPL
* MSFT
* NVDA
* SPY
* QQQ

Initial environment:

paper trading only.

Safety

The application must not claim guaranteed returns.

Historical performance does not imply future performance.

Paper trading results are experimental results, not financial advice.

## Frontend Architecture

Alyntiq uses a standalone frontend built with:

- React

- TypeScript

- Vite

- React Router

- Tailwind CSS

The frontend communicates with the FastAPI backend through REST APIs and WebSockets.

Next.js is not part of the current architecture.