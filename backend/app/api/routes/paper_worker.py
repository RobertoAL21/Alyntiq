"""Token-gated operational control for one non-executing worker preflight cycle."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.routes.strategy_deployments import require_dashboard_control_token
from app.core.config import get_settings
from app.db.session import get_db_session
from app.paper_worker.service import PaperWorkerService

router = APIRouter(prefix="/api/control/paper-worker", tags=["paper worker"])
DbSession = Annotated[Session, Depends(get_db_session)]
ControlAccess = Annotated[None, Depends(require_dashboard_control_token)]


class PreflightResultResponse(BaseModel):
    deployment_id: str
    outcome: str
    reason: str
    checked_at: datetime


class PreflightRunResponse(BaseModel):
    checked: int
    ready: int
    blocked: int
    results: list[PreflightResultResponse]


@router.post("/preflight", response_model=PreflightRunResponse)
def run_paper_worker_preflight(session: DbSession, _: ControlAccess) -> PreflightRunResponse:
    results = PaperWorkerService().run_once(session, settings=get_settings())
    session.commit()
    return PreflightRunResponse(
        checked=len(results),
        ready=sum(result.outcome.value == "ready" for result in results),
        blocked=sum(result.outcome.value == "blocked" for result in results),
        results=[
            PreflightResultResponse(
                deployment_id=result.deployment_id,
                outcome=result.outcome.value,
                reason=result.reason,
                checked_at=result.checked_at,
            )
            for result in results
        ],
    )
