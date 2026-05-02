# terraform/ — IaC Root

Composition layer. 5 module calls in `main.tf`; root-level `.tf` files configure providers, variables, outputs. Driven by `tflocal` (terraform-local pip pkg), NOT vanilla `terraform`.

## Files

- `main.tf` — 5 module calls (elasticache → iam → lambda → eventbridge → api_gateway). Order matters: lambda needs IAM roles + Redis endpoint; eventbridge needs lambda ARN.
- `variables.tf` — `lambda_runtime` defaults to `"python3.13"` (provider enum), `event_bus_name`, `redis_ttl_seconds`, etc.
- `outputs.tf` — `invoke_url`, `redis_endpoint` — read via `tflocal output -raw <name>` (do NOT hard-code anywhere)
- `providers.tf` — AWS provider pinned to dummy creds for LocalStack (`access_key=test`, `secret_key=test`, `region=us-east-1`); endpoint overrides applied by tflocal
- `versions.tf` — `terraform >=1.9`, `aws ~> 5.x` (5.x rejects `python3.14` runtime string — keep `python3.13`)
- `locals.tf` — `common_tags` merged into every module
- `terraform.tfstate` / `.tfstate.backup` — **committed by design** for LocalStack ephemerality + reproducibility (NOT a remote-backend setup)

## Module map

| Module | Responsibility |
|---|---|
| `modules/elasticache/` | Single-node Redis cluster; outputs `redis_endpoint`, `redis_port` |
| `modules/iam/` | Producer + consumer execution roles; `events:PutEvents` for producer |
| `modules/lambda/` | Both Lambda functions + ZIP packaging via `build_zips.sh` (see its AGENTS.md) |
| `modules/eventbridge/` | Custom bus `orders-bus`, rule on `orders.api`/`OrderCreated`, lambda target + invoke permission |
| `modules/api-gateway/` | HTTP API v2 + `POST /orders` route + Lambda integration + invoke permission |

## Commands (always tflocal, never terraform)

```bash
tflocal init -upgrade
tflocal apply -auto-approve
tflocal output -raw invoke_url
tflocal destroy -auto-approve
```

`make deploy` / `make destroy` wrap these.

## Forbidden

- **NEVER** set `lambda_runtime = "python3.14"` — AWS provider v5.x enum rejects it. Use `"python3.13"`; LocalStack still executes 3.14 bytecode.
- **NEVER** run vanilla `terraform apply` here — endpoints won't redirect to LocalStack
- **NEVER** delete `terraform.tfstate*` to "clean" — run `make destroy` instead (graceful resource teardown)
- **NEVER** add a remote backend (`backend "s3"` etc.) — local state is intentional for this project
- **NEVER** hard-code `invoke_url`/`redis_endpoint` in tests — use the conftest fixtures that shell out to `tflocal output -json`
