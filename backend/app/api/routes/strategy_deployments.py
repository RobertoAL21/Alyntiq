"""Paper-deployment controls that intentionally stop before execution."""

from collections.abc import Callable
from decimal import Decimal
from secrets import compare_digest
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db_session
from app.risk.types import RiskLimits
from app.strategy_deployments.service import StrategyDeploymentError, StrategyDeploymentService
from app.strategy_deployments.types import StrategyDeployment, StrategyDeploymentSpec

router = APIRouter(prefix="/api/control/strategy-deployments", tags=["strategy deployments"])
DbSession = Annotated[Session, Depends(get_db_session)]


class RiskLimitsRequest(BaseModel):
    maximum_position_size_pct: Decimal = Field(gt=0, le=1)
    maximum_portfolio_exposure: Decimal = Field(gt=0, le=1)
    maximum_daily_loss_pct: Decimal = Field(gt=0, le=1)
    maximum_drawdown_pct: Decimal = Field(gt=0, le=1)
    stop_loss_pct: Decimal = Field(gt=0, le=1)
    take_profit_pct: Decimal = Field(gt=0, le=1)
    max_trades_per_day: int = Field(ge=1)
    minimum_cash_reserve: Decimal = Field(ge=0)

    def to_risk_limits(self) -> RiskLimits:
        return RiskLimits(**self.model_dump())


class StrategyDeploymentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=96)
    model_version: str = Field(min_length=1, max_length=64)
    strategy_version: str = Field(min_length=1, max_length=64)
    feature_version: str = Field(min_length=1, max_length=64)
    target_version: str = Field(min_length=1, max_length=64)
    source: str = Field(min_length=1, max_length=32)
    timeframe: str = Field(min_length=1, max_length=8)
    symbols: list[str] = Field(min_length=1, max_length=20)
    buy_threshold: Decimal
    sell_threshold: Decimal
    order_quantity: int = Field(ge=1)
    risk_limits: RiskLimitsRequest

    def to_spec(self) -> StrategyDeploymentSpec:
        return StrategyDeploymentSpec(
            name=self.name,
            model_version=self.model_version,
            strategy_version=self.strategy_version,
            feature_version=self.feature_version,
            target_version=self.target_version,
            source=self.source,
            timeframe=self.timeframe,
            symbols=tuple(self.symbols),
            buy_threshold=self.buy_threshold,
            sell_threshold=self.sell_threshold,
            order_quantity=self.order_quantity,
            risk_limits=self.risk_limits.to_risk_limits(),
        )


class RiskLimitsResponse(BaseModel):
    maximum_position_size_pct: Decimal
    maximum_portfolio_exposure: Decimal
    maximum_daily_loss_pct: Decimal
    maximum_drawdown_pct: Decimal
    stop_loss_pct: Decimal
    take_profit_pct: Decimal
    max_trades_per_day: int
    minimum_cash_reserve: Decimal


class StrategyDeploymentResponse(BaseModel):
    id: str
    name: str
    state: str
    model_version: str
    strategy_version: str
    feature_version: str
    target_version: str
    source: str
    timeframe: str
    symbols: list[str]
    buy_threshold: Decimal
    sell_threshold: Decimal
    order_quantity: int
    risk_limits: RiskLimitsResponse
    created_at: str
    updated_at: str


def require_dashboard_control_token(
    x_alyntiq_control_token: Annotated[str | None, Header(alias="X-Alyntiq-Control-Token")] = None,
) -> None:
    configured_token = get_settings().dashboard_control_token
    if configured_token is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Dashboard deployment controls are disabled until "
                "DASHBOARD_CONTROL_TOKEN is configured"
            ),
        )
    if x_alyntiq_control_token is None or not compare_digest(
        x_alyntiq_control_token, configured_token
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid dashboard control token is required",
        )


ControlAccess = Annotated[None, Depends(require_dashboard_control_token)]


@router.post("", response_model=StrategyDeploymentResponse, status_code=status.HTTP_201_CREATED)
def create_strategy_deployment(
    request: StrategyDeploymentCreateRequest,
    session: DbSession,
    _: ControlAccess,
) -> StrategyDeploymentResponse:
    try:
        deployment = StrategyDeploymentService().create(session, request.to_spec())
        session.commit()
    except (StrategyDeploymentError, ValueError) as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    return _response(deployment)


@router.post("/{deployment_id}/validate", response_model=StrategyDeploymentResponse)
def validate_strategy_deployment(
    deployment_id: str,
    session: DbSession,
    _: ControlAccess,
) -> StrategyDeploymentResponse:
    return _transition(
        session,
        lambda service: service.validate(
            session, deployment_id=deployment_id, settings=get_settings()
        ),
    )


@router.post("/{deployment_id}/arm", response_model=StrategyDeploymentResponse)
def arm_strategy_deployment(
    deployment_id: str,
    session: DbSession,
    _: ControlAccess,
) -> StrategyDeploymentResponse:
    return _transition(
        session,
        lambda service: service.arm(session, deployment_id=deployment_id, settings=get_settings()),
    )


@router.post("/{deployment_id}/disarm", response_model=StrategyDeploymentResponse)
def disarm_strategy_deployment(
    deployment_id: str,
    session: DbSession,
    _: ControlAccess,
) -> StrategyDeploymentResponse:
    return _transition(
        session, lambda service: service.disarm(session, deployment_id=deployment_id)
    )


def _transition(
    session: Session, operation: Callable[[StrategyDeploymentService], StrategyDeployment]
) -> StrategyDeploymentResponse:
    try:
        deployment = operation(StrategyDeploymentService())
        session.commit()
    except StrategyDeploymentError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(error)
        ) from error
    return _response(deployment)


def _response(deployment: StrategyDeployment) -> StrategyDeploymentResponse:
    spec = deployment.spec
    return StrategyDeploymentResponse(
        id=deployment.id,
        name=spec.name,
        state=deployment.state.value,
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
        risk_limits=RiskLimitsResponse.model_validate(spec.risk_limits, from_attributes=True),
        created_at=deployment.created_at.isoformat(),
        updated_at=deployment.updated_at.isoformat(),
    )
