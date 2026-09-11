import pandas as pd

from app.targets.constants import TARGET_COLUMNS, TARGET_IDENTITY_COLUMNS

REQUIRED_BAR_COLUMNS = frozenset({*TARGET_IDENTITY_COLUMNS, "close"})


class TargetCalculationError(ValueError):
    """Raised when market bars cannot be transformed into supervised-learning targets."""


class TargetGenerator:
    """Generate labels while keeping future values out of the feature pipeline."""

    def generate(self, bars: pd.DataFrame) -> pd.DataFrame:
        """Generate the next-day direction target for each source-qualified bar.

        The label for timestamp t uses close(t + 1), so it is intentionally not an
        inference feature. The final bar in each symbol dataset has no known label.
        """
        missing_columns = REQUIRED_BAR_COLUMNS.difference(bars.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise TargetCalculationError(f"bars are missing required columns: {missing}")

        normalized = bars.loc[:, [*TARGET_IDENTITY_COLUMNS, "close"]].copy()
        normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], utc=True)
        normalized["close"] = pd.to_numeric(normalized["close"])
        normalized = normalized.sort_values(
            ["symbol", "source", "timeframe", "timestamp"]
        ).reset_index(drop=True)

        grouping_columns = ["symbol", "source", "timeframe"]
        next_close = normalized.groupby(grouping_columns, sort=False)["close"].shift(-1)
        normalized["direction_1d"] = next_close.gt(normalized["close"]).where(next_close.notna())

        return normalized.loc[:, [*TARGET_IDENTITY_COLUMNS, *TARGET_COLUMNS]]
