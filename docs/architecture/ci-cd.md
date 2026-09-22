# CI Validation and Release Boundary

## Scope

Phase 25 validates every pull request and `main` branch change. It does not publish an
image, deploy infrastructure, run migrations automatically, or introduce a live-trading
path.

```text
pull request / main push / manual run
                |
    +-----------+------------+-------------------+
    v                        v                   v
backend quality       frontend quality    financial safety
    |                        |                   |
    +------------------------+-------------------+
                             v
                    Docker image builds
```

## Validation jobs

The GitHub Actions workflow uses read-only repository permissions and cancels superseded
runs for the same branch. It runs four independent jobs:

- backend quality: install declared development dependencies, run Ruff, and execute the
  complete pytest suite;
- frontend quality: run `npm ci`, ESLint, Vitest, and the production Vite build;
- financial safety: verify tracked-file and paper-trading contracts, then run the leakage,
  model-lineage, paper-broker, and backtesting sanity tests explicitly; and
- Docker image builds: build the backend and frontend images without pushing either image.

The financial-safety verifier uses only the Python standard library and the Git index. It
rejects tracked environment or credential files, non-placeholder sensitive values in
`.env.example`, a non-paper default, a live Alpaca endpoint in the paper broker, and the
absence of the model-version guard. It complements behavioural tests; it is not a secret
scanner for external systems or a substitute for platform-level secret protection.

## Release boundary

`main` runs the same validation and image builds as pull requests. Image publication and
deployment remain intentionally disabled: this repository has no authorized registry,
cloud account, environment protections, or deployment credentials configured.

When those authorities exist, a separate protected release workflow should: tag immutable
images with the reviewed commit SHA; push only after all validation jobs succeed; apply
Alembic migrations as a one-off task; deploy the backend and frontend independently; and
verify their health endpoints. It must obtain runtime secrets from the platform secret
manager, keep `TRADING_ENVIRONMENT=paper`, and never pass credentials through build args
or image layers.

## Local verification

From the repository root:

```bash
python scripts/verify_ci_safety.py
cd backend && ruff check . && ruff format --check . && pytest
cd ../frontend && npm ci && npm run lint && npm test && npm run build
cd .. && docker build --tag alyntiq-backend:ci backend
docker build --tag alyntiq-frontend:ci frontend
```
