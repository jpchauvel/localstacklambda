# pyright: reportUnknownMemberType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownVariableType=false, reportAny=false, reportUnusedCallResult=false, reportMissingTypeArgument=false
import subprocess

import pytest
import redis as redis_lib


def _terraform_output(name: str) -> str:
    result = subprocess.run(
        ["tflocal", "output", "-raw", name],
        cwd="terraform",
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise RuntimeError(f"tflocal output -raw {name} failed: {stderr}")
    return result.stdout.strip()


@pytest.fixture(scope="module")
def stack_outputs() -> dict[str, str]:
    try:
        return {
            "invoke_url": _terraform_output("invoke_url"),
            "redis_endpoint": _terraform_output("redis_endpoint"),
            "redis_port": _terraform_output("redis_port"),
        }
    except Exception as exc:
        pytest.skip(f"stack not deployed: {exc}")


@pytest.fixture(scope="module")
def invoke_url(stack_outputs: dict[str, str]) -> str:
    return stack_outputs["invoke_url"]


@pytest.fixture(scope="module")
def redis_client(stack_outputs: dict[str, str]):
    endpoint = stack_outputs["redis_endpoint"]
    port = stack_outputs["redis_port"]
    redis_url = f"redis://{endpoint}:{port}"
    try:
        client = redis_lib.Redis.from_url(
            redis_url, decode_responses=True, socket_connect_timeout=5
        )
        _ = client.ping()
    except Exception as exc:
        pytest.skip(f"Redis unavailable at {redis_url}: {exc}")
    return client


@pytest.fixture
def cleanup_order_keys(redis_client):
    keys: set[str] = set()
    yield keys
    for key in keys:
        redis_client.delete(key)
