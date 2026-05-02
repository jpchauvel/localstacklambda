# tests/ — Test Pyramid

35 tests: **18 unit** + **13 integration** + **4 e2e**. Markers auto-applied by `conftest.py::pytest_collection_modifyitems` from path — DON'T add `@pytest.mark.unit` etc. by hand.

## Tier semantics + isolation guarantees

| Tier | Path | Backends | Pre-push? | Make target |
|---|---|---|---|---|
| `unit` | `tests/unit/` | `moto[events]`, `fakeredis`, in-process handler call | ✅ runs | `make test-unit` |
| `integration` | `tests/integration/` | live LocalStack via `boto3` + real `redis-py` | ❌ excluded | `make test-integration` |
| `e2e` | `tests/e2e/` | deployed TF stack, `tflocal output`, HTTP `requests` to API GW | ❌ excluded | `make test-e2e` |

`make test-unit` enforces `--cov-fail-under=80` (offline only). `make test-e2e` adds `--timeout=60`.

## Fixtures (root `conftest.py`, all session-scoped)

- `localstack_endpoint` — `AWS_ENDPOINT_URL` env or `http://localhost:4566`
- `aws_creds` — sets `AWS_ACCESS_KEY_ID/SECRET/REGION` to `test`/`test`/`us-east-1` if unset
- `events_client`, `lambda_client`, `logs_client`, `apigw_client`, `elasticache_client` — boto3 clients pointed at LocalStack
- `redis_client` — real `redis.Redis`; **skips** if `LOCALSTACK_REDIS_HOST` unset
- `terraform_outputs` — shells out to `tflocal output -json`; **skips** if no `terraform.tfstate`
- `api_endpoint` — derived from `terraform_outputs["invoke_url"]`; **skips** on missing key

Tier-specific fixtures live in `tests/{unit,integration,e2e}/conftest.py`.

## Unit tier rules

- ONLY `moto[events]` for AWS (NEVER `boto3` to LocalStack)
- ONLY `fakeredis.FakeRedis` for Redis (NEVER `redis.Redis` to localhost)
- Call handler functions directly (`from src.producer.handler import handler; handler(event, ctx)`)
- No network, no subprocess, no `tflocal`, no docker

## Integration tier rules

- Requires `make up` running first (LocalStack on `:4566`)
- Use the boto3 fixtures (already endpoint-configured)
- May invoke deployed Lambdas via `lambda_client.invoke(...)` if `make deploy` ran
- Do NOT shell out to `tflocal output` here — that's the e2e tier's job

## E2E tier rules

- Requires `make up && make deploy`
- Uses `api_endpoint` fixture + `requests.post(...)` against real API GW
- Asserts side effects via `redis_client` + `logs_client`
- Tolerate eventual consistency: poll with timeout, don't `time.sleep` once

## Required env vars (all tiers)

```
CI=true PAGER=cat
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1
```

For integration/e2e additionally: `LOCALSTACK_REDIS_HOST` + `LOCALSTACK_REDIS_PORT` (read from `tflocal output -raw redis_endpoint`).

## Forbidden

- **NEVER** add `@pytest.mark.unit/integration/e2e` manually — auto-applied by path; manual + auto = double-marker churn
- **NEVER** put a LocalStack-dependent test under `tests/unit/` — pre-push will run it offline and fail mysteriously
- **NEVER** delete the markers section in `pyproject.toml` — `--strict-markers` is enabled, missing markers will error all collection
- **NEVER** mock at the boto3 client level in unit tests — use `moto`; mocking `boto3.client` hides real API contract drift
