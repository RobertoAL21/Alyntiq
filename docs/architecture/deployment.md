# Deployment Images

## Scope

Phase 24 supplies production-oriented Docker images and a documented reference topology.
It does not add a worker, model server, CI/CD pipeline, infrastructure-as-code, automatic
migrations, alert delivery, or real-money trading.

```text
browser
   |
   v
frontend image (Nginx, port 8080) ---- public load balancer
                                             |
                                             v
                                  backend image (FastAPI, port 8000)
                                             |
                      +----------------------+----------------------+
                      v                                             v
                 PostgreSQL                                    Redis
                   (RDS)                                    (ElastiCache)
```

## Images

`backend/Dockerfile` installs only the runtime package and its declared dependencies,
runs FastAPI as the unprivileged `alyntiq` user, exposes port `8000`, and probes the
existing `/health` route. The build context excludes local environment files, tests,
MLflow runs, credentials, and Python caches.

`frontend/Dockerfile` builds the Vite SPA with Node and copies only its static `dist/`
output into a small Nginx runtime image. The runtime uses the unprivileged `nginx` user
on port `8080`, has a static health endpoint, sends logs to stdout/stderr, and falls back
to `index.html` for React Router routes.

Neither image contains `.env` files, provider credentials, database passwords, model
artifacts, or MLflow run data. All runtime settings remain environment variables, as
defined by `app.core.config.Settings`.

## Compose environment

`docker-compose.yml` is a local integration environment for the backend, frontend,
PostgreSQL, and Redis. PostgreSQL requires `POSTGRES_PASSWORD` from the untracked `.env`
file; the included `.env.example` contains only a replace-before-use placeholder.
Compose derives the backend database connection from the same database settings unless
`DOCKER_DATABASE_URL` is supplied explicitly. It keeps MLflow data in a local named
volume because the current MLflow tracker is file/SQLite based.

There is intentionally no worker service: no worker contract or scheduled workload exists
yet. There is also no standalone MLflow server, since moving tracking metadata and
artifacts to shared production services requires an explicit later design.

Migrations are not run from application startup. Apply them once as an explicit release
step with `alembic upgrade head` (or an equivalent one-off container task) before serving
traffic.

## AWS reference topology

For a later managed deployment, publish the two images to a container registry and run
separate frontend and backend services on ECS/Fargate (or equivalent EC2-managed
containers). Place the public load balancer in public subnets; backend tasks, RDS
PostgreSQL, and ElastiCache Redis remain in private subnets. Give the backend a narrowly
scoped task role for only the required artifact bucket and telemetry endpoint. Store
database, Redis, Alpaca, and OTLP credentials in a secrets manager and inject them at task
runtime, never during image build.

S3 is the appropriate future location for durable model/MLflow artifacts; the current
local named volume is not a multi-replica production artifact store. CloudWatch can retain
container stdout/stderr, while the existing optional OTLP configuration remains vendor
neutral. Exact provisioning, image publishing, release automation, and CI/CD are outside
this phase.

## Manual verification

From the repository root after creating an untracked `.env` from `.env.example` and
replacing its password placeholder:

```bash
docker compose --env-file .env config
docker compose up --build
curl http://localhost:8000/health
curl http://localhost:8080/health
```

Apply database migrations separately when required:

```bash
docker compose exec backend alembic upgrade head
```
