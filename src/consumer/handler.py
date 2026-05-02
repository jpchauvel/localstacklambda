from __future__ import annotations

import logging
import os
from typing import Any

from src.shared.events import OrderCreated
from src.shared.redis_client import claim_idempotency_key, get_redis_client

log = logging.getLogger()
log.setLevel(logging.INFO)

REDIS_TTL_SECONDS = int(os.environ.get("REDIS_TTL_SECONDS", "300"))

_redis = None


def _get_redis():
    global _redis
    if _redis is None:
        _redis = get_redis_client()
    return _redis


def _process(order: OrderCreated) -> None:
    # Domain processing placeholder — log structured success
    log.info(
        "processed order_id=%s customer_id=%s amount=%s currency=%s items=%d",
        order.order_id,
        order.customer_id,
        order.amount,
        order.currency,
        len(order.items),
    )


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    # EventBridge invokes Lambda with single event envelope (NOT batched)
    try:
        detail = event["detail"]
        order = OrderCreated.from_eventbridge_detail(detail)
    except Exception:
        log.exception(
            "invalid_event event_keys=%s",
            list(event.keys()) if isinstance(event, dict) else type(event),
        )
        raise

    try:
        r = _get_redis()
        claimed = claim_idempotency_key(
            r, order.order_id, str(order.event_id), REDIS_TTL_SECONDS
        )
    except Exception:
        log.exception("redis_error order_id=%s", order.order_id)
        raise

    if not claimed:
        log.info(
            "duplicate order_id=%s event_id=%s",
            order.order_id,
            order.event_id,
        )
        return {"status": "duplicate", "order_id": order.order_id}

    _process(order)
    return {
        "status": "processed",
        "order_id": order.order_id,
        "event_id": str(order.event_id),
    }
