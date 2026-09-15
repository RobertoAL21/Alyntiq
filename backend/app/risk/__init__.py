"""Independent pre-trade risk evaluation for proposed strategy orders."""

from app.risk.types import ProposedOrder, RiskContext, RiskDecision, RiskLimits, RiskRule

__all__ = ["ProposedOrder", "RiskContext", "RiskDecision", "RiskEngine", "RiskLimits", "RiskRule"]


def __getattr__(name: str) -> object:
    """Load the engine only when requested to avoid a risk/backtesting import cycle."""
    if name == "RiskEngine":
        from app.risk.engine import RiskEngine

        return RiskEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
