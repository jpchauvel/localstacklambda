# src/ — Python Lambda Source

Two Lambda entry packages (`producer/`, `consumer/`) + `shared/` for cross-Lambda code. All ZIP-bundled; runtime deps (`boto3`, `pydantic`, `redis`) pip-installed at TF apply via `terraform/modules/lambda/build_zips.sh`.

## Handler signature (both Lambdas)

```python
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
```

- TF maps `handler = "producer.handler.handler"` and `"consumer.handler.handler"` (NOT `src.producer...`)
- `build_zips.sh` stages BOTH `producer/`+`shared/` at zip root AND mirrors `src/shared/` so `from src.shared.events import ...` ALSO resolves at runtime — keep imports as `from src.shared.X` (matches local pytest layout)

## Per-Lambda env contract

- **Producer**: `EVENT_BUS_NAME` (required), `EVENT_SOURCE`, `EVENT_DETAIL_TYPE`, `AWS_ENDPOINT_URL`, `AWS_REGION`
- **Consumer**: `REDIS_HOST`, `REDIS_PORT`, `REDIS_TTL_SECONDS` (default 300), `AWS_ENDPOINT_URL`
- TF lambda module sets `AWS_ENDPOINT_URL = http://localhost.localstack.cloud:4566` for in-Lambda boto3

## Conventions specific to handlers

- Lazy-init clients into module-level `_events`/`_redis` globals (cold-start optimization)
- Producer returns API Gateway response shape (`{statusCode, headers, body}`); Consumer returns plain dict (EventBridge async invoke ignores it)
- Consumer treats EventBridge envelope as **single event**, NOT batched (`event["detail"]`)
- Producer catches `(json.JSONDecodeError, ValidationError)` → 400; everything else → 500
- Consumer **re-raises** on Redis/parse failure (EventBridge retries); duplicates return `{"status": "duplicate"}` (success, no retry)
- Logger: stdlib `logging.getLogger()` at module top, `setLevel(INFO)` — no print, no structlog

## Adding a new Lambda

1. Create `src/<name>/{__init__.py,handler.py}` with `handler(event, context)`
2. Add `build_zip <name>` line to `build_zips.sh` (or refactor loop)
3. Add `aws_lambda_function.<name>` in `terraform/modules/lambda/main.tf`
4. Wire env vars + IAM role + invoke perms in respective TF modules

## Forbidden

- **NEVER** import a non-bundled package (only `boto3`+`pydantic`+`redis` are pip-installed by `build_zips.sh`)
- **NEVER** read `event["Records"]` — that's SQS/SNS shape; EventBridge uses `event["detail"]`
- **NEVER** call `boto3.client()` at module top — use lazy init for testability + cold-start
