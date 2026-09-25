from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.strategy_deployment import StrategyDeploymentRecord
from app.risk.types import RiskLimits
from app.strategy_deployments.types import (
    StrategyDeployment,
    StrategyDeploymentSpec,
    StrategyDeploymentState,
)


class StrategyDeploymentRepositoryError(ValueError):
    """Raised for missing or invalid persisted strategy deployment data."""


def list_deployments(session: Session) -> tuple[StrategyDeployment, ...]:
    records = session.scalars(
        select(StrategyDeploymentRecord).order_by(
            StrategyDeploymentRecord.created_at.desc(), StrategyDeploymentRecord.id.desc()
        )
    )
    return tuple(_to_deployment(record) for record in records)


def find_deployment(session: Session, deployment_id: str) -> StrategyDeployment | None:
    record = session.get(StrategyDeploymentRecord, deployment_id)
    return None if record is None else _to_deployment(record)


def store_deployment(session: Session, spec: StrategyDeploymentSpec) -> StrategyDeployment:
    record = StrategyDeploymentRecord(
        id=str(uuid4()),
        name=spec.name,
        state=StrategyDeploymentState.DRAFT.value,
        model_version=spec.model_version,
        strategy_version=spec.strategy_version,
        feature_version=spec.feature_version,
        target_version=spec.target_version,
        source=spec.source,
        timeframe=spec.timeframe,
        symbols=list(spec.symbols),
        buy_threshold=spec.buy_threshold,
        sell_threshold=spec.sell_threshold,
        order_quantity=spec.order_quantity,
        risk_limits=_risk_limits_to_json(spec.risk_limits),
    )
    session.add(record)
    session.flush()
    return _to_deployment(record)


def update_deployment_state(
    session: Session,
    *,
    deployment_id: str,
    state: StrategyDeploymentState,
    updated_at: datetime,
) -> StrategyDeployment:
    record = _require_record(session, deployment_id)
    record.state = state.value
    record.updated_at = updated_at.astimezone(UTC)
    session.flush()
    return _to_deployment(record)


def _require_record(session: Session, deployment_id: str) -> StrategyDeploymentRecord:
    record = session.get(StrategyDeploymentRecord, deployment_id)
    if record is None:
        raise StrategyDeploymentRepositoryError(
            f"strategy deployment was not found: {deployment_id}"
        )
    return record


def _to_deployment(record: StrategyDeploymentRecord) -> StrategyDeployment:
    try:
        risk = record.risk_limits
        spec = StrategyDeploymentSpec(
            name=record.name,
            model_version=record.model_version,
            strategy_version=record.strategy_version,
            feature_version=record.feature_version,
            target_version=record.target_version,
            source=record.source,
            timeframe=record.timeframe,
            symbols=tuple(record.symbols),
            buy_threshold=Decimal(str(record.buy_threshold)),
            sell_threshold=Decimal(str(record.sell_threshold)),
            order_quantity=record.order_quantity,
            risk_limits=RiskLimits(
                maximum_position_size_pct=Decimal(str(risk["maximum_position_size_pct"])),
                maximum_portfolio_exposure=Decimal(str(risk["maximum_portfolio_exposure"])),
                maximum_daily_loss_pct=Decimal(str(risk["maximum_daily_loss_pct"])),
                maximum_drawdown_pct=Decimal(str(risk["maximum_drawdown_pct"])),
                stop_loss_pct=Decimal(str(risk["stop_loss_pct"])),
                take_profit_pct=Decimal(str(risk["take_profit_pct"])),
                max_trades_per_day=int(risk["max_trades_per_day"]),
                minimum_cash_reserve=Decimal(str(risk["minimum_cash_reserve"])),
            ),
        )
        return StrategyDeployment(
            id=record.id,
            state=StrategyDeploymentState(record.state),
            spec=spec,
            created_at=_as_utc(record.created_at),
            updated_at=_as_utc(record.updated_at),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise StrategyDeploymentRepositoryError(
            "strategy deployment persistence is invalid"
        ) from error


def _risk_limits_to_json(limits: RiskLimits) -> dict[str, str | int]:
    return {
        "maximum_position_size_pct": str(limits.maximum_position_size_pct),
        "maximum_portfolio_exposure": str(limits.maximum_portfolio_exposure),
        "maximum_daily_loss_pct": str(limits.maximum_daily_loss_pct),
        "maximum_drawdown_pct": str(limits.maximum_drawdown_pct),
        "stop_loss_pct": str(limits.stop_loss_pct),
        "take_profit_pct": str(limits.take_profit_pct),
        "max_trades_per_day": limits.max_trades_per_day,
        "minimum_cash_reserve": str(limits.minimum_cash_reserve),
    }


def _as_utc(timestamp: datetime) -> datetime:
    return timestamp.replace(tzinfo=UTC) if timestamp.tzinfo is None else timestamp.astimezone(UTC)
