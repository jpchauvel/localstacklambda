# pyright: reportUnknownMemberType=false, reportUnknownParameterType=false, reportMissingParameterType=false, reportUnknownVariableType=false, reportAny=false, reportUnusedCallResult=false, reportMissingTypeArgument=false
import time
from uuid import UUID, uuid4

import httpx
import pytest
from tenacity import retry, stop_after_delay, wait_fixed

pytestmark = pytest.mark.e2e


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


def test_duplicate_order_id_processed_once(
    invoke_url: str, redis_client, cleanup_order_keys: set[str]
):
    order_id = f"o-idem-{uuid4()}"
    redis_key = f"order:{order_id}"
    cleanup_order_keys.add(redis_key)
    payload = _valid_payload(order_id)

    response_1 = httpx.post(invoke_url, json=payload, timeout=10)
    response_2 = httpx.post(invoke_url, json=payload, timeout=10)

    assert response_1.status_code == 202
    assert response_2.status_code == 202

    body_1 = response_1.json()
    body_2 = response_2.json()

    event_id_1 = body_1["event_id"]
    event_id_2 = body_2["event_id"]
    _ = UUID(event_id_1)
    _ = UUID(event_id_2)
    assert body_1["order_id"] == order_id
    assert body_2["order_id"] == order_id
    assert event_id_1 != event_id_2

    @retry(stop=stop_after_delay(15), wait=wait_fixed(0.5), reraise=True)
    def wait_for_first_redis_value() -> str:
        value = redis_client.get(redis_key)
        if value is None:
            raise RuntimeError("redis key not present yet")
        return value

    stored_value_1 = wait_for_first_redis_value()
    time.sleep(5)
    stored_value_2 = redis_client.get(redis_key)

    assert stored_value_1 == stored_value_2


def test_distinct_orders_both_processed(
    invoke_url: str, redis_client, cleanup_order_keys: set[str]
):
    order_id_1 = f"o-idem-a-{uuid4()}"
    order_id_2 = f"o-idem-b-{uuid4()}"
    redis_key_1 = f"order:{order_id_1}"
    redis_key_2 = f"order:{order_id_2}"
    cleanup_order_keys.add(redis_key_1)
    cleanup_order_keys.add(redis_key_2)

    response_1 = httpx.post(
        invoke_url, json=_valid_payload(order_id_1), timeout=10
    )
    response_2 = httpx.post(
        invoke_url, json=_valid_payload(order_id_2), timeout=10
    )

    assert response_1.status_code == 202
    assert response_2.status_code == 202

    event_id_1 = response_1.json()["event_id"]
    event_id_2 = response_2.json()["event_id"]
    _ = UUID(event_id_1)
    _ = UUID(event_id_2)

    @retry(stop=stop_after_delay(15), wait=wait_fixed(0.5), reraise=True)
    def wait_for_both_values() -> tuple[str, str]:
        value_1 = redis_client.get(redis_key_1)
        value_2 = redis_client.get(redis_key_2)
        if value_1 is None or value_2 is None:
            raise RuntimeError("redis key not present yet")
        return value_1, value_2

    stored_value_1, stored_value_2 = wait_for_both_values()
    assert stored_value_1 == event_id_1
    assert stored_value_2 == event_id_2
