# ADR 025 — Use Separate Unprivileged Web Runtime Images

## Status

Accepted

## Context

Alyntiq has a Python API and a standalone Vite SPA. The original backend image ran as
root and the frontend had no deployable image. A deployment unit must be small, health
checkable, and configurable at runtime without copying local secrets or research outputs
into an image.

## Options Considered

### Serve the frontend from FastAPI

This would merge SPA delivery with the backend and make independent static caching and
scaling harder, while changing the existing standalone frontend architecture.

### Run development servers in production containers

Vite's development server and a reload-oriented API command are not appropriate runtime
servers and retain unnecessary development tooling.

### Use separate backend and static-SPA runtime images

This preserves the existing architecture and lets each HTTP surface have its own health
endpoint and deployment scaling boundary.

## Decision

Build the backend from its declared Python package and run Uvicorn as an unprivileged
`alyntiq` user. Build the frontend with Node in a build stage, then serve only its static
output from Nginx as its unprivileged user. Each image has a local healthcheck and accepts
runtime configuration only through the environment.

Keep database migration execution outside application startup. Keep worker and MLflow
server deployment out of this phase because neither has an implemented runtime contract.

## Consequences

The frontend and backend can be deployed and scaled separately without relocating
financial business logic to the frontend. Release automation must explicitly build, tag,
publish, migrate, and deploy these images in a future CI/CD phase. Operators must provide
all secrets and production persistence externally; Docker image builds cannot be used as
configuration storage.
