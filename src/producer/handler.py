from __future__ import annotations

import json
import logging
import os
from typing import Any

import boto3
from pydantic import ValidationError

from src.shared.events import OrderCreated

log = logging.getLogger()
log.setLevel(logging.INFO)

EVENT_BUS_NAME = os.environ["EVENT_BUS_NAME"]
EVENT_SOURCE = os.environ.get("EVENT_SOURCE", "orders.api")
EVENT_DETAIL_TYPE = os.environ.get("EVENT_DETAIL_TYPE", "OrderCreated")

_events = None


def _get_events_client():
    global _events
    if _events is None:
        _events = boto3.client(
            "events",
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
            endpoint_url=os.environ.get("AWS_ENDPOINT_URL"),
        )
    return _events


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        raw = event.get("body") or "{}"
        payload = json.loads(raw) if isinstance(raw, str) else raw
        order = OrderCreated.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as e:
        log.warning("invalid_payload error=%s", e)
        return _response(400, {"error": "invalid_payload", "detail": str(e)})

    try:
        resp = _get_events_client().put_events(
            Entries=[
                {
                    "EventBusName": EVENT_BUS_NAME,
                    "Source": EVENT_SOURCE,
                    "DetailType": EVENT_DETAIL_TYPE,
                    "Detail": order.to_eventbridge_detail(),
                }
            ]
        )
        failed = resp.get("FailedEntryCount", 0)
        if failed:
            log.error("put_events_failed resp=%s", resp)
            return _response(502, {"error": "publish_failed"})
        log.info(
            "published event_id=%s order_id=%s",
            order.event_id,
            order.order_id,
        )
        return _response(
            202, {"event_id": str(order.event_id), "order_id": order.order_id}
        )
    except Exception:
        log.exception("put_events_exception")
        return _response(500, {"error": "internal_error"})
