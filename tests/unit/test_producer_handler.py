from __future__ import annotations

import importlib
import json
import os
import uuid
from unittest.mock import MagicMock, patch

import boto3
import pytest
from moto import mock_aws

pytestmark = pytest.mark.unit

# Set required env vars BEFORE importing handler module
os.environ["EVENT_BUS_NAME"] = "test-bus"
os.environ["EVENT_SOURCE"] = "orders.api"
os.environ["EVENT_DETAIL_TYPE"] = "OrderCreated"
os.environ.setdefault("AWS_ACCESS_KEY_ID", "test")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ["AWS_REGION"] = "us-east-1"
# Ensure moto is not bypassed by an endpoint URL
os.environ.pop("AWS_ENDPOINT_URL", None)


def _valid_payload() -> dict:
    return {
        "order_id": "o1",
        "customer_id": "c1",
        "amount": "10.00",
        "currency": "USD",
        "items": [{"sku": "s1", "quantity": 1, "unit_price": "10.00"}],
    }


def _event(body) -> dict:
    if not isinstance(body, str):
        body = json.dumps(body)
    return {"body": body}


@pytest.fixture
def handler_mod():
    with mock_aws():
        boto3.client("events", region_name="us-east-1").create_event_bus(
            Name="test-bus"
        )
        import src.producer.handler as h

        importlib.reload(h)
        yield h


def test_valid_order_returns_202_with_event_id(handler_mod):
    resp = handler_mod.handler(_event(_valid_payload()), None)
    assert resp["statusCode"] == 202
    body = json.loads(resp["body"])
    assert body["order_id"] == "o1"
    # event_id must be a UUID string
    uuid.UUID(body["event_id"])


def test_currency_uppercased(handler_mod):
    payload = _valid_payload()
    payload["currency"] = "usd"
    resp = handler_mod.handler(_event(payload), None)
    assert resp["statusCode"] == 202


def test_invalid_payload_returns_400(handler_mod):
    payload = _valid_payload()
    del payload["order_id"]
    resp = handler_mod.handler(_event(payload), None)
    assert resp["statusCode"] == 400
    assert json.loads(resp["body"])["error"] == "invalid_payload"


def test_negative_amount_returns_400(handler_mod):
    payload = _valid_payload()
    payload["amount"] = "-1"
    resp = handler_mod.handler(_event(payload), None)
    assert resp["statusCode"] == 400
    assert json.loads(resp["body"])["error"] == "invalid_payload"


def test_empty_items_returns_400(handler_mod):
    payload = _valid_payload()
    payload["items"] = []
    resp = handler_mod.handler(_event(payload), None)
    assert resp["statusCode"] == 400
    assert json.loads(resp["body"])["error"] == "invalid_payload"


def test_malformed_json_returns_400(handler_mod):
    resp = handler_mod.handler({"body": "{not json"}, None)
    assert resp["statusCode"] == 400
    assert json.loads(resp["body"])["error"] == "invalid_payload"


def test_eventbridge_failure_returns_502(handler_mod):
    fake = MagicMock()
    fake.put_events.return_value = {
        "FailedEntryCount": 1,
        "Entries": [{"ErrorCode": "InternalFailure"}],
    }
    with patch.object(handler_mod, "_get_events_client", return_value=fake):
        resp = handler_mod.handler(_event(_valid_payload()), None)
    assert resp["statusCode"] == 502
    assert json.loads(resp["body"])["error"] == "publish_failed"


def test_eventbridge_exception_returns_500(handler_mod):
    fake = MagicMock()
    fake.put_events.side_effect = Exception("boom")
    with patch.object(handler_mod, "_get_events_client", return_value=fake):
        resp = handler_mod.handler(_event(_valid_payload()), None)
    assert resp["statusCode"] == 500
    assert json.loads(resp["body"])["error"] == "internal_error"


def test_event_published_with_correct_source_and_detail_type(handler_mod):
    captured = {}
    real_client = handler_mod._get_events_client()
    real_put = real_client.put_events

    def spy(**kwargs):
        captured.update(kwargs)
        return real_put(**kwargs)

    with patch.object(real_client, "put_events", side_effect=spy) as _:
        resp = handler_mod.handler(_event(_valid_payload()), None)

    assert resp["statusCode"] == 202
    entries = captured["Entries"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["Source"] == "orders.api"
    assert entry["DetailType"] == "OrderCreated"
    assert entry["EventBusName"] == "test-bus"
    detail = json.loads(entry["Detail"])
    assert detail["order_id"] == "o1"
