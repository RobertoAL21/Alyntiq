from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.observability.telemetry import configure_observability, get_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    configure_observability(settings, app)
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)


@app.middleware("http")
async def record_api_latency(request, call_next):
    started_at = perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        get_telemetry().record_api_latency(
            method=request.method,
            route=request.url.path,
            status_code=status_code,
            duration_seconds=perf_counter() - started_at,
        )


app.include_router(api_router)
