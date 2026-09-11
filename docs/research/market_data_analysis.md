# Exploratory Data Analysis — Historical Market Data

## Scope and reproducibility

This Phase 2 analysis queries the PostgreSQL `market_bars` dataset on 2026-09-10.

| Property | Value |
| --- | --- |
| Symbols | AAPL, MSFT, NVDA, SPY, QQQ |
| Source | `alpaca:iex:raw` |
| Timeframe | 1D |
| Coverage | 2020-07-27 through 2026-09-10 |
| Observations | 1,539 bars per symbol; 7,695 total |

The requested range began on 2020-01-01, but IEX returned coverage beginning on
2020-07-27. This is a dataset limitation, not an assumption about every provider.

Run the notebook after starting Compose services:

```bash
docker run --rm --network alyntiq_default \
  -e DATABASE_URL=postgresql+psycopg://alyntiq:alyntiq@postgres:5432/alyntiq \
  -e MPLBACKEND=Agg -v "$PWD:/workspace" -w /workspace/backend python:3.12-slim \
  sh -c "pip install '.[research]' && jupyter nbconvert --to notebook --execute \
  --output /tmp/market_data_analysis_executed.ipynb \
  /workspace/notebooks/exploration/market_data_analysis.ipynb"
```

The notebook is descriptive only. It reads bars but creates no features, models,
signals, or trading rules.

## Methods

The analysis covers close-price and volume distributions, simple/log returns,
21-session annualized rolling volatility, drawdowns, return correlations, 60-session
SPY correlations, lag-one autocorrelation, and 20/50-session moving averages.

The regime view is descriptive: SPY is classified by its position relative to the
50-session moving average and whether its 21-session volatility exceeds the sample
median. It is not a predictive model or a strategy.

## Findings

### Price, returns, and drawdowns

| Symbol | Mean close | Median close | Annualized volatility | Maximum drawdown |
| --- | ---: | ---: | ---: | ---: |
| AAPL | 194.15 | 178.20 | 41.66% | -78.88% |
| MSFT | 347.24 | 335.30 | 27.50% | -37.54% |
| NVDA | 316.95 | 214.74 | 69.24% | -92.30% |
| SPY | 501.07 | 454.26 | 16.54% | -25.38% |
| QQQ | 425.44 | 380.33 | 22.58% | -35.63% |

NVDA has the widest daily-return dispersion, highest annualized volatility, and deepest
sample drawdown. SPY has the lowest volatility and shallowest maximum drawdown in this
universe. These are historical descriptions of the raw-price sample, not future-risk
estimates.

Lag-one return autocorrelation is close to zero for all symbols, from -0.0410 (NVDA) to
0.0031 (MSFT). This does not establish market efficiency or rule out nonlinear effects;
it only gives little descriptive support to one-day linear return persistence.

### Volume and correlations

Mean daily volume ranges from 0.62 million shares for QQQ to 1.74 million for NVDA.
The distributions are right-skewed: NVDA's maximum was 16.79 million shares compared
with a 0.99 million median. Future volume measures should use trailing normalization
only, to avoid future information.

Daily-return correlation between QQQ and SPY is 0.9346, the highest non-identical pair.
MSFT correlates 0.7391 with QQQ and 0.6959 with SPY. NVDA has lower sample correlation
with QQQ (0.5559) and SPY (0.4821).

Rolling 60-session correlation with SPY changes materially:

| Symbol | Minimum | Median | Maximum |
| --- | ---: | ---: | ---: |
| AAPL | 0.0216 | 0.6566 | 0.9233 |
| MSFT | 0.0909 | 0.7104 | 0.9341 |
| NVDA | -0.2630 | 0.6388 | 0.8994 |
| QQQ | 0.7298 | 0.9390 | 0.9920 |

A static correlation therefore does not fully describe this sample. QQQ and SPY should
not be treated as independent diversification exposures.

### Moving averages and descriptive regimes

SPY was above its 50-session moving average in 69.72% of eligible observations and in
the above-median 21-session-volatility state for 49.32%. The descriptive states were:

| SPY above 50-session MA | High volatility | Sessions | Share |
| --- | --- | ---: | ---: |
| Yes | No | 639 | 41.52% |
| Yes | Yes | 434 | 28.20% |
| No | Yes | 325 | 21.12% |
| No | No | 141 | 9.16% |

This classification describes changing conditions; it is not a validated regime model
or a trading rule.

## Limitations and hypotheses

- The data is daily and limited to five US instruments on IEX; it is not a broad-market
  or intraday study.
- Bars are `raw`, so corporate actions can affect returns and drawdowns. Later research
  must choose and document an adjustment policy before long-horizon comparisons.
- This EDA uses the full sample only for description. Predictive work must use
  chronological or walk-forward validation, never random splits.
- Phase 3 can evaluate trailing, point-in-time returns, volatility, relative volume,
  moving-average distance, and rolling correlation. Their value must be compared with
  simple baselines without leakage.
