Phase 24 — Deployment

Status: COMPLETE

Create production-ready Docker images.

Potential services:

* frontend
* backend
* worker
* postgres
* redis
* MLflow

Potential AWS architecture:

* ECS or EC2
* RDS
* ElastiCache
* S3
* CloudWatch

Never store secrets in code.

Delivered:

* unprivileged, health-checkable backend and frontend production images;
* local Compose integration for the API, SPA, PostgreSQL, and Redis with externally
  supplied database credentials; and
* deployment architecture documentation with an AWS reference topology and an explicit
  migration release step.

Workers, a standalone MLflow service, infrastructure-as-code, image publishing, and CI/CD
remain out of scope.
