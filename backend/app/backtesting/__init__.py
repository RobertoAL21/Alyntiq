"""Deterministic, historical backtesting primitives."""

from app.backtesting.types import BacktestBar, BacktestConfig, SignalLineage, Strategy

__all__ = [
    "BacktestBar",
    "BacktestConfig",
    "BacktestEngine",
    "BacktestInputError",
    "SignalLineage",
    "Strategy",
]


def __getattr__(name: str) -> object:
    """Load the engine only when requested to avoid a risk/backtesting import cycle."""
    if name in {"BacktestEngine", "BacktestInputError"}:
        from app.backtesting.engine import BacktestEngine, BacktestInputError

        return {"BacktestEngine": BacktestEngine, "BacktestInputError": BacktestInputError}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
