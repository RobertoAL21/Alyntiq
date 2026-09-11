import numpy as np
import pandas as pd

from app.features.constants import FEATURE_COLUMNS

REQUIRED_BAR_COLUMNS = frozenset(
    {"symbol", "timestamp", "open", "high", "low", "close", "volume", "source", "timeframe"}
)


class FeatureCalculationError(ValueError):
    """Raised when bars cannot be transformed into point-in-time features."""


def calculate_features(bars: pd.DataFrame) -> pd.DataFrame:
    """Calculate per-bar features using only values available at each timestamp.

    Rolling windows and exponential windows are trailing windows that include the current
    bar. The result retains rows with warm-up nulls so downstream consumers can apply
    their own explicit completeness policy.
    """
    missing_columns = REQUIRED_BAR_COLUMNS.difference(bars.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise FeatureCalculationError(f"bars are missing required columns: {missing}")

    normalized = bars.copy()
    normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], utc=True)
    for column in ("open", "high", "low", "close", "volume"):
        normalized[column] = pd.to_numeric(normalized[column])
    normalized = normalized.sort_values(["symbol", "timestamp"]).reset_index(drop=True)

    feature_frames = [
        _calculate_symbol_features(group) for _, group in normalized.groupby("symbol")
    ]
    features = pd.concat(feature_frames, ignore_index=True)
    features = _add_market_context(features)

    return features.sort_values(["symbol", "timestamp"]).reset_index(drop=True)


def _calculate_symbol_features(bars: pd.DataFrame) -> pd.DataFrame:
    frame = bars.copy()
    close = frame["close"]
    high = frame["high"]
    low = frame["low"]
    volume = frame["volume"]
    previous_close = close.shift(1)

    frame["returns_1d"] = close.pct_change(fill_method=None)
    for period in (5, 10, 20):
        frame[f"returns_{period}d"] = close.pct_change(periods=period, fill_method=None)
        frame[f"momentum_{period}"] = close.divide(close.shift(period)).subtract(1)

    for period in (10, 20, 50):
        frame[f"sma_{period}"] = close.rolling(window=period, min_periods=period).mean()
    for period in (10, 20):
        frame[f"ema_{period}"] = close.ewm(span=period, adjust=False, min_periods=period).mean()

    for period in (10, 20):
        frame[f"volatility_{period}"] = frame["returns_1d"].rolling(
            window=period, min_periods=period
        ).std(ddof=0) * np.sqrt(252)

    true_range = pd.concat(
        [
            high.subtract(low),
            high.subtract(previous_close).abs(),
            low.subtract(previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    frame["atr_14"] = true_range.rolling(window=14, min_periods=14).mean()

    price_delta = close.diff()
    average_gain = price_delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    average_loss = (
        (-price_delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    )
    relative_strength = average_gain.divide(average_loss.replace(0, np.nan))
    rsi = 100 - (100 / (1 + relative_strength))
    frame["rsi_14"] = rsi.mask((average_loss == 0) & (average_gain > 0), 100).mask(
        (average_gain == 0) & (average_loss > 0), 0
    )

    ema_12 = close.ewm(span=12, adjust=False, min_periods=12).mean()
    ema_26 = close.ewm(span=26, adjust=False, min_periods=26).mean()
    frame["macd"] = ema_12.subtract(ema_26)
    frame["macd_signal"] = frame["macd"].ewm(span=9, adjust=False, min_periods=9).mean()

    rolling_std_20 = close.rolling(window=20, min_periods=20).std(ddof=0)
    frame["bollinger_upper"] = frame["sma_20"].add(rolling_std_20.mul(2))
    frame["bollinger_lower"] = frame["sma_20"].subtract(rolling_std_20.mul(2))

    frame["volume_change"] = volume.pct_change(fill_method=None)
    frame["volume_ma_20"] = volume.rolling(window=20, min_periods=20).mean()
    frame["volume_ratio"] = volume.divide(frame["volume_ma_20"])

    return frame


def _add_market_context(features: pd.DataFrame) -> pd.DataFrame:
    context = features.loc[
        features["symbol"].isin({"SPY", "QQQ"}),
        ["symbol", "timestamp", "returns_1d", "volatility_20"],
    ]
    spy_context = (
        context.loc[context["symbol"] == "SPY", ["timestamp", "returns_1d", "volatility_20"]]
        .rename(
            columns={
                "returns_1d": "spy_returns_1d",
                "volatility_20": "spy_volatility_20",
            }
        )
        .drop_duplicates("timestamp")
    )
    qqq_context = (
        context.loc[context["symbol"] == "QQQ", ["timestamp", "returns_1d"]]
        .rename(columns={"returns_1d": "qqq_returns_1d"})
        .drop_duplicates("timestamp")
    )

    return features.merge(spy_context, on="timestamp", how="left").merge(
        qqq_context, on="timestamp", how="left"
    )


def feature_columns_present(features: pd.DataFrame) -> bool:
    """Return whether every versioned feature column is present in a result frame."""
    return set(FEATURE_COLUMNS).issubset(features.columns)
