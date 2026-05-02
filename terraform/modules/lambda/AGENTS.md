# terraform/modules/lambda/ — ZIP Packaging Module

Most non-standard module in the repo. Bundles Python source + pip deps into ZIPs at `terraform apply` time using `null_resource` + bash, because `archive_file` cannot pip-install.

## Files

- `main.tf` — `null_resource.build_zips` + 2× `aws_lambda_function` + 2× CloudWatch log groups
- `build_zips.sh` — bash that stages source, pip-installs into staging, zips per-Lambda
- `variables.tf` — runtime, memory, timeout, env-var inputs, `source_root` (typically `${path.module}/..`)
- `outputs.tf` — function ARNs/names/invoke ARNs (consumed by eventbridge + api-gateway modules)
- `build/` — generated `producer.zip` + `consumer.zip` (gitignored)

## Build trigger contract

```hcl
triggers = {
  src_hash = sha256(join("", [
    for f in fileset("${var.source_root}/src", "**/*.py") :
    filesha256("${var.source_root}/src/${f}")
  ]))
}
```

Any `.py` change under `src/` invalidates the trigger → bash re-runs → ZIPs rebuilt → `source_code_hash` shifts → `aws_lambda_function` re-deploys. **TF/dep version changes do NOT trigger rebuild** — bump a Python file or `taint null_resource.build_zips` to force.

## build_zips.sh layout (per Lambda)

Staging dir contains:
```
<lambda_name>/handler.py     ← matches handler = "<name>.handler.handler"
shared/{events,redis_client}.py
src/shared/{events,redis_client}.py   ← duplicate, makes `from src.shared.X` work in-Lambda
__init__.py + src/__init__.py
<pip deps: pydantic/, redis/, ...>
```

The double-stage of `shared/` (top-level + under `src/`) is intentional — Lambda handler resolution wants top-level package; runtime imports written as `from src.shared.X` to match local pytest layout.

## Runtime deps (hard-coded)

```bash
python3 -m pip install --target "${stage_dir}" --quiet pydantic redis
```

`boto3` is NOT installed — Lambda runtime provides it. To add a new dep, edit this line (no requirements.txt indirection by design — keeps the deviation visible).

## Forbidden

- **NEVER** swap `null_resource` for `archive_file` — `archive_file` cannot pip-install (the whole reason this module exists)
- **NEVER** add `boto3` to the pip line — bloats ZIP, conflicts with runtime-provided version
- **NEVER** rename a Lambda dir (`producer`/`consumer`) without updating `build_zip <name>` calls AND `handler = "<name>.handler.handler"` in `main.tf`
- **NEVER** commit `build/` — gitignored; regenerated every apply
- **NEVER** rely on `${path.cwd}` in `local-exec` — use `${path.module}` (run from `terraform/`, but module path is module-relative)
