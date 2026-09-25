"""Queries that assemble persisted research facts for the dashboard API."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from mlflow import MlflowClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models.market_bar import MarketBar
from app.db.models.model_registry import ModelRegistryRecord
from app.db.models.trading_decision import TradingDecisionRecord
from app.strategy_deployments.service import StrategyDeploymentService
from app.strategy_deployments.types import StrategyDeployment


@dataclass(frozen=True)
class MarketCandle:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


@dataclass(frozen=True)
class MarketSnapshot:
    symbol: str
    source: str
    timeframe: str
    candles: tuple[MarketCandle, ...]


@dataclass(frozen=True)
class ExperimentRun:
    id: str
    name: str
    model_version: str | None
    started_at: datetime
    accuracy: float | None
    precision: float | None
    roc_auc: float | None
    registry_state: str | None


def load_overview(session: Session, settings: Settings) -> dict[str, object]:
    latest_timestamp, bar_count, symbol_count = session.execute(
        select(
            func.max(MarketBar.timestamp),
            func.count(MarketBar.id),
            func.count(func.distinct(MarketBar.symbol)),
        )
    ).one()
    decision_count = session.scalar(select(func.count(TradingDecisionRecord.id))) or 0
    latest_market_bar_at = (
        None
        if latest_timestamp is None
        else (
            latest_timestamp.replace(tzinfo=UTC)
            if latest_timestamp.tzinfo is None
            else latest_timestamp.astimezone(UTC)
        )
    )
    return {
        "latest_market_bar_at": latest_market_bar_at,
        "market_bar_count": bar_count or 0,
        "symbol_count": symbol_count or 0,
        "experiment_count": len(load_experiment_runs(session, settings)),
        "decision_count": decision_count,
        "positions_available": False,
        "strategy_results_available": False,
    }


def load_market_snapshot(
    session: Session,
    *,
    symbol: str,
    source: str,
    timeframe: str,
    limit: int,
) -> MarketSnapshot:
    normalized_symbol = symbol.strip().upper()
    records = session.scalars(
        select(MarketBar)
        .where(
            MarketBar.symbol == normalized_symbol,
            MarketBar.source == source,
            MarketBar.timeframe == timeframe,
        )
        .order_by(MarketBar.timestamp.desc())
        .limit(limit)
    ).all()
    return MarketSnapshot(
        symbol=normalized_symbol,
        source=source,
        timeframe=timeframe,
        candles=tuple(
            MarketCandle(
                timestamp=record.timestamp.astimezone(UTC),
                open=record.open,
                high=record.high,
                low=record.low,
                close=record.close,
                volume=record.volume,
            )
            for record in reversed(records)
        ),
    )


def load_experiment_runs(session: Session, settings: Settings) -> tuple[ExperimentRun, ...]:
    client = MlflowClient(tracking_uri=settings.mlflow_tracking_uri)
    experiment = client.get_experiment_by_name(settings.mlflow_experiment_name)
    if experiment is None:
        return ()
    states = {
        record.model_version: record.state
        for record in session.scalars(select(ModelRegistryRecord)).all()
    }
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["attributes.start_time DESC"],
        max_results=100,
    )
    return tuple(
        ExperimentRun(
            id=run.info.run_id,
            name=run.data.params.get("model_name", run.info.run_name or "unnamed"),
            model_version=run.data.params.get("model_version"),
            started_at=datetime.fromtimestamp(run.info.start_time / 1000, tz=UTC),
            accuracy=_metric(run.data.metrics, "holdout_accuracy", "accuracy"),
            precision=_metric(run.data.metrics, "holdout_precision", "precision"),
            roc_auc=_metric(run.data.metrics, "holdout_roc_auc", "roc_auc"),
            registry_state=states.get(run.data.params.get("model_version", "")),
        )
        for run in runs
    )


def load_trading_decisions(session: Session, limit: int) -> tuple[TradingDecisionRecord, ...]:
    return tuple(
        session.scalars(
            select(TradingDecisionRecord)
            .order_by(TradingDecisionRecord.timestamp.desc(), TradingDecisionRecord.id)
            .limit(limit)
        ).all()
    )


def load_strategy_deployments(session: Session) -> tuple[StrategyDeployment, ...]:
    """Return persisted control-plane state without granting mutation access."""
    return StrategyDeploymentService().list(session)


def _metric(metrics: dict[str, float], *names: str) -> float | None:
    return next((metrics[name] for name in names if name in metrics), None)
