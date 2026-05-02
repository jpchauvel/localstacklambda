# pyright: reportUnknownMemberType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownVariableType=false, reportAny=false, reportUnusedCallResult=false, reportMissingTypeArgument=false
import json
from uuid import UUID, uuid4

import httpx
import pytest
from tenacity import retry, stop_after_delay, wait_fixed

pytestmark = pytest.mark.e2e

REDIS_TTL_SECONDS = 300


def _valid_payload(order_id: str) -> dict[str, object]:
    return {
        "order_id": order_id,
        "customer_id": "cust-e2e-1",
        "amount": "99.50",
        "currency": "USD",
        "items": [
            {
                "sku": "sku-1",
                "quantity": 2,
                "unit_price": "49.75",
            }
        ],
    }


def test_post_order_publishes_event_and_consumer_processes(
    invoke_url: str, redis_client, cleanup_order_keys: set[str]
):
    order_id = f"o-e2e-{uuid4()}"
    response = httpx.post(
        invoke_url, json=_valid_payload(order_id), timeout=10
    )

    assert response.status_code == 202
    body = response.json()

    event_id = body["event_id"]
    _ = UUID(event_id)
    assert body["order_id"] == order_id

    redis_key = f"order:{order_id}"
    cleanup_order_keys.add(redis_key)

    @retry(stop=stop_after_delay(15), wait=wait_fixed(0.5), reraise=True)
    def wait_for_redis_key() -> str:
        value = redis_client.get(redis_key)
        if value is None:
            raise RuntimeError("redis key not present yet")
        return value

    stored_event_id = wait_for_redis_key()
    assert stored_event_id == event_id

    ttl = redis_client.ttl(redis_key)
    assert 1 <= ttl <= REDIS_TTL_SECONDS


def test_invalid_payload_rejected_at_api(
    invoke_url: str, redis_client, cleanup_order_keys: set[str]
):
    order_id = f"o-invalid-{uuid4()}"
    redis_key = f"order:{order_id}"
    cleanup_order_keys.add(redis_key)

    malformed_body = json.dumps({"order_id": order_id, "customer_id": "c1"})[
        :-1
    ]
    response = httpx.post(
        invoke_url,
        content=malformed_body,
        headers={"content-type": "application/json"},
        timeout=10,
    )

    assert 400 <= response.status_code < 500
    assert redis_client.get(redis_key) is None
