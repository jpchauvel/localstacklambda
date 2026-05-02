# AGENTS.md

LocalStack Pro pub/sub: API Gateway → Producer Lambda → EventBridge → Consumer Lambda → Redis (SET NX dedup). Python 3.14 runtime, Terraform IaC, ZIP-only packaging (no Docker images).

## Stack

- **Runtime**: Python 3.14 (executes), labeled `python3.13` in Terraform (provider compat)
- **IaC**: Terraform via `tflocal` wrapper (terraform-local pip pkg) → LocalStack Pro 4.0
- **Deps**: `boto3`, `pydantic>=2`, `redis` (runtime); `pytest`, `moto[events]>=5`, `fakeredis`, `mypy`, `ruff`, `bandit`, `pip-audit` (dev)
- **Local infra**: docker-compose (`localstack/localstack-pro:4.0`), requires `LOCALSTACK_AUTH_TOKEN`

## Layout

```
src/{producer,consumer,shared}/  Python lambdas + shared event/redis code
terraform/                       Root TF + 5 modules (lambda, eventbridge, api-gateway, iam, elasticache)
tests/{unit,integration,e2e}/    Pyramid: 18 + 13 + 4 = 35 tests
.github/workflows/ci.yml         CI on Py3.14
.pre-commit-config.yaml          Fast hooks pre-commit, slow hooks pre-push
```

## NEVER (project-specific)

- **NEVER set TF `lambda_runtime = "python3.14"`** — AWS provider v5.x rejects it. Use `python3.13`. LocalStack still runs 3.14 code.
- **NEVER set ruff `target-version` or mypy `python_version` to `py314`/`3.14`** — tooling unsupported. Keep `py313`/`3.13` (deliberate mismatch with `requires-python = ">=3.14"`).
- **NEVER `import boto3`/`pydantic`/`redis` in handler code without bundling via `terraform/modules/lambda/build_zips.sh`** — Lambda has no auto deps; the `null_resource` in TF lambda module pip-installs into ZIP staging.
- **NEVER `git push --no-verify`** — pre-push hooks (mypy, bandit, gitleaks, pip-audit, pytest unit) are mandatory. Fix the issue, don't bypass.
- **NEVER add integration/e2e tests to pre-push** — they need live LocalStack + deployed stack. Pre-push runs ONLY `tests/unit/` (offline, moto + fakeredis).
- **NEVER commit `terraform/modules/*/.terraform/`** — gitignored; created by per-module `terraform validate` from pre-commit hook.
- **NEVER hard-code TF outputs** (Redis port, invoke URL) — always read via `tflocal output -raw <name>`.
- **NEVER use `as any` / `@ts-ignore` equivalents** — no type-error suppression. Fix root cause.

## Conventions

- **Ruff**: `line-length=78` (NOT 88), `quote-style="double"`, `select=["E","F","I","B","W","UP"]`
- **Pytest**: `--strict-markers`; markers `unit/integration/e2e` auto-applied by `tests/conftest.py::pytest_collection_modifyitems` based on path
- **Pre-commit split**: fast (ruff, terraform fmt, file hygiene) on `pre-commit`; slow (mypy, bandit, gitleaks, pip-audit, pytest unit, terraform validate) on `pre-push`
- **Bandit**: scans `src/` only; excludes `tests`, `.sisyphus`, `terraform`
- **Pip-audit**: scans only `[project].dependencies` (not dev)
- **Mypy**: `strict=false`, `ignore_missing_imports=true`, `files=["src"]`
- **Lambda env**: handlers read `AWS_ENDPOINT_URL` (TF sets `http://localhost.localstack.cloud:4566` for in-Lambda)

## Required env vars

Tests/CI: `CI=true PAGER=cat AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1`
Stack: `LOCALSTACK_AUTH_TOKEN` (docker-compose fail-fasts via `${VAR:?...}` syntax) — copy `.env.example` → `.env`.

## Commands

```bash
make up                # docker compose + wait for LocalStack health
make deploy            # cd terraform && tflocal init -upgrade && tflocal apply -auto-approve
make test-unit         # offline, 18 tests, --cov-fail-under=80
make test-integration  # requires live LocalStack
make test-e2e          # requires deployed stack (--timeout=60)
make test              # all 35
make destroy && make down
make logs              # docker logs -f localstack-pubsub
pre-commit install --hook-type pre-commit --hook-type pre-push  # required setup
```

## Where to look

| Task                      | File                                        |
|---------------------------|---------------------------------------------|
| Producer entry            | `src/producer/handler.py`                   |
| Consumer entry            | `src/consumer/handler.py`                   |
| Event contract            | `src/shared/events.py` (`OrderCreated`)     |
| Redis dedup primitive     | `src/shared/redis_client.py`                |
| TF root composition       | `terraform/main.tf`                         |
| Lambda packaging          | `terraform/modules/lambda/build_zips.sh`    |
| TF outputs (URL, Redis)   | `terraform/outputs.tf`                      |
| Hook config               | `.pre-commit-config.yaml`                   |
| CI                        | `.github/workflows/ci.yml`                  |
