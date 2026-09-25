"""Read-only API views for persisted research data."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.dashboard.service import (
    ExperimentRun,
    MarketCandle,
    load_experiment_runs,
    load_market_snapshot,
    load_overview,
    load_strategy_deployments,
    load_trading_decisions,
)
from app.db.session import get_db_session

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
DbSession = Annotated[Session, Depends(get_db_session)]


class OverviewResponse(BaseModel):
    latest_market_bar_at: datetime | None
    market_bar_count: int
    symbol_count: int
    experiment_count: int
    decision_count: int
    positions_available: bool
    strategy_results_available: bool


class CandleResponse(BaseModel):
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


class MarketResponse(BaseModel):
    symbol: str
    source: str
    timeframe: str
    candles: list[CandleResponse]


class ExperimentResponse(BaseModel):
    id: str
    name: str
    model_version: str | None
    started_at: datetime
    accuracy: float | None
    precision: float | None
    roc_auc: float | None
    registry_state: str | None


class ModelsResponse(BaseModel):
    runs: list[ExperimentResponse]


class TradingDecisionResponse(BaseModel):
    id: str
    timestamp: datetime
    symbol: str
    signal: str
    risk_decision: str
    executed: bool
    price: Decimal | None
    quantity: int | None
    model_version: str | None
    confidence: Decimal | None
    reason: str


class TradesResponse(BaseModel):
    decisions: list[TradingDecisionResponse]


class StrategyDeploymentSummaryResponse(BaseModel):
    id: str
    name: str
    state: str
    model_version: str
    strategy_version: str
    symbols: list[str]
    created_at: datetime
    updated_at: datetime
    latest_preflight_outcome: str | None
    latest_preflight_reason: str | None
    latest_preflight_at: datetime | None


class StrategyDeploymentsResponse(BaseModel):
    deployments: list[StrategyDeploymentSummaryResponse]


@router.get("/overview", response_model=OverviewResponse)
def dashboard_overview(session: DbSession) -> OverviewResponse:
    return OverviewResponse.model_validate(load_overview(session, get_settings()))


@router.get("/market", response_model=MarketResponse)
def dashboard_market(
    session: DbSession,
    symbol: str = Query(default="AAPL", min_length=1, max_length=16),
    source: str = Query(default="alpaca:iex:raw", min_length=1, max_length=32),
    timeframe: str = Query(default="1D", min_length=1, max_length=8),
    limit: int = Query(default=180, ge=1, le=500),
) -> MarketResponse:
    snapshot = load_market_snapshot(
        session, symbol=symbol, source=source, timeframe=timeframe, limit=limit
    )
    return MarketResponse(
        symbol=snapshot.symbol,
        source=snapshot.source,
        timeframe=snapshot.timeframe,
        candles=[_candle_response(candle) for candle in snapshot.candles],
    )


@router.get("/models", response_model=ModelsResponse)
def dashboard_models(session: DbSession) -> ModelsResponse:
    return ModelsResponse(
        runs=[_experiment_response(run) for run in load_experiment_runs(session, get_settings())]
    )


@router.get("/deployments", response_model=StrategyDeploymentsResponse)
def dashboard_strategy_deployments(session: DbSession) -> StrategyDeploymentsResponse:
    return StrategyDeploymentsResponse(
        deployments=[
            StrategyDeploymentSummaryResponse(
                id=status.deployment.id,
                name=status.deployment.spec.name,
                state=status.deployment.state.value,
                model_version=status.deployment.spec.model_version,
                strategy_version=status.deployment.spec.strategy_version,
                symbols=list(status.deployment.spec.symbols),
                created_at=status.deployment.created_at,
                updated_at=status.deployment.updated_at,
                latest_preflight_outcome=(
                    None
                    if status.latest_preflight is None
                    else status.latest_preflight.outcome.value
                ),
                latest_preflight_reason=(
                    None if status.latest_preflight is None else status.latest_preflight.reason
                ),
                latest_preflight_at=(
                    None if status.latest_preflight is None else status.latest_preflight.checked_at
                ),
            )
            for status in load_strategy_deployments(session)
        ]
    )


@router.get("/trades", response_model=TradesResponse)
def dashboard_trades(
    session: DbSession, limit: int = Query(default=100, ge=1, le=500)
) -> TradesResponse:
    return TradesResponse(
        decisions=[
            TradingDecisionResponse(
                id=record.id,
                timestamp=record.timestamp,
                symbol=record.symbol,
                signal=record.signal,
                risk_decision=record.risk_decision,
                executed=record.executed,
                price=record.price,
                quantity=record.quantity,
                model_version=record.model_version,
                confidence=record.confidence,
                reason=record.reason,
            )
            for record in load_trading_decisions(session, limit)
        ]
    )


def _candle_response(candle: MarketCandle) -> CandleResponse:
    return CandleResponse(
        timestamp=candle.timestamp,
        open=candle.open,
        high=candle.high,
        low=candle.low,
        close=candle.close,
        volume=candle.volume,
    )


def _experiment_response(run: ExperimentRun) -> ExperimentResponse:
    return ExperimentResponse(
        id=run.id,
        name=run.name,
        model_version=run.model_version,
        started_at=run.started_at,
        accuracy=run.accuracy,
        precision=run.precision,
        roc_auc=run.roc_auc,
        registry_state=run.registry_state,
    )
