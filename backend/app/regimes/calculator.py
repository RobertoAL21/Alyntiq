from collections.abc import Sequence
from math import sqrt

import pandas as pd

from app.regimes.types import RegimeBar, RegimeFeatureConfig, RegimeFeatures


class RegimeFeatureCalculationError(ValueError):
    """Raised when completed bars cannot produce complete trailing regime features."""


def calculate_regime_features(
    bars: Sequence[RegimeBar],
    config: RegimeFeatureConfig | None = None,
) -> tuple[RegimeFeatures, ...]:
    """Calculate trailing SPY/QQQ regime inputs without reading a later completed bar."""
    config = config or RegimeFeatureConfig()
    frame = _bars_frame(bars, config)
    market = _market_features(frame, config)
    correlation = _correlations(frame, config)
    complete = market.merge(correlation, on="timestamp", how="inner").dropna()
    return tuple(
        RegimeFeatures(
            timestamp=row.timestamp.to_pydatetime(),
            return_value=float(row.return_value),
            trend=float(row.trend),
            volatility=float(row.volatility),
            volume_ratio=float(row.volume_ratio),
            correlation=float(row.correlation),
        )
        for row in complete.itertuples(index=False)
    )


def _bars_frame(bars: Sequence[RegimeBar], config: RegimeFeatureConfig) -> pd.DataFrame:
    relevant = [
        {"timestamp": bar.timestamp, "symbol": bar.symbol, "close": bar.close, "volume": bar.volume}
        for bar in bars
        if bar.symbol in {config.market_symbol, config.correlation_symbol}
    ]
    if not relevant:
        raise RegimeFeatureCalculationError(
            "no bars were supplied for the configured regime symbols"
        )
    frame = pd.DataFrame(relevant)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame = frame.sort_values(["symbol", "timestamp"]).reset_index(drop=True)
    if frame.duplicated(["symbol", "timestamp"]).any():
        raise RegimeFeatureCalculationError("regime bars must be unique per symbol and timestamp")
    symbols = set(frame["symbol"])
    missing = {config.market_symbol, config.correlation_symbol}.difference(symbols)
    if missing:
        raise RegimeFeatureCalculationError(
            f"regime bars are missing configured symbols: {', '.join(sorted(missing))}"
        )
    return frame


def _market_features(frame: pd.DataFrame, config: RegimeFeatureConfig) -> pd.DataFrame:
    market = frame.loc[frame["symbol"] == config.market_symbol].copy()
    returns = market["close"].pct_change(fill_method=None)
    market["return_value"] = market["close"].pct_change(periods=config.window, fill_method=None)
    market["trend"] = (
        market["close"]
        .divide(market["close"].rolling(config.window, min_periods=config.window).mean())
        .subtract(1)
    )
    market["volatility"] = (
        returns.rolling(config.window, min_periods=config.window)
        .std(ddof=0)
        .mul(sqrt(config.trading_days_per_year))
    )
    market["volume_ratio"] = market["volume"].divide(
        market["volume"].rolling(config.window, min_periods=config.window).mean()
    )
    return market[["timestamp", "return_value", "trend", "volatility", "volume_ratio"]]


def _correlations(frame: pd.DataFrame, config: RegimeFeatureConfig) -> pd.DataFrame:
    prices = frame.pivot(index="timestamp", columns="symbol", values="close").sort_index()
    returns = prices.pct_change(fill_method=None)
    correlation = (
        returns[config.market_symbol]
        .rolling(config.window, min_periods=config.window)
        .corr(returns[config.correlation_symbol])
    )
    return correlation.rename("correlation").reset_index()
