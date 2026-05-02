from __future__ import annotations

import importlib
from unittest.mock import patch

import fakeredis
import pytest

pytestmark = pytest.mark.unit


VALID_DETAIL = {
    "event_id": "11111111-1111-1111-1111-111111111111",
    "order_id": "o1",
    "customer_id": "c1",
    "amount": "10.00",
    "currency": "USD",
    "items": [{"sku": "s1", "quantity": 1, "unit_price": "10.00"}],
    "timestamp": "2026-05-01T00:00:00Z",
}


def _detail(
    order_id: str = "o1",
    event_id: str = "11111111-1111-1111-1111-111111111111",
) -> dict:
    d = dict(VALID_DETAIL)
    d["order_id"] = order_id
    d["event_id"] = event_id
    return d


def _event(detail) -> dict:
    return {
        "source": "orders.api",
        "detail-type": "OrderCreated",
        "detail": detail,
    }


@pytest.fixture
def fake_redis(monkeypatch):
    from src.consumer import handler as h

    fr = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(h, "_redis", fr)
    return fr


def test_first_event_is_processed(fake_redis):
    from src.consumer import handler as h

    result = h.handler(_event(_detail("o1")), None)
    assert result["status"] == "processed"
    assert result["order_id"] == "o1"
    assert result["event_id"] == "11111111-1111-1111-1111-111111111111"


def test_duplicate_event_within_ttl_is_skipped(fake_redis):
    from src.consumer import handler as h

    with patch("src.consumer.handler._process") as spy:
        first = h.handler(_event(_detail("o2")), None)
        second = h.handler(
            _event(_detail("o2", "22222222-2222-2222-2222-222222222222")),
            None,
        )

    assert first["status"] == "processed"
    assert second == {"status": "duplicate", "order_id": "o2"}
    assert spy.call_count == 1


def test_different_order_ids_both_processed(fake_redis):
    from src.consumer import handler as h

    r1 = h.handler(_event(_detail("oA")), None)
    r2 = h.handler(
        _event(_detail("oB", "33333333-3333-3333-3333-333333333333")), None
    )
    assert r1["status"] == "processed"
    assert r2["status"] == "processed"


def test_redis_key_format(fake_redis):
    from src.consumer import handler as h

    h.handler(_event(_detail("oKey")), None)
    assert fake_redis.exists("order:oKey") == 1


def test_redis_value_is_event_id(fake_redis):
    from src.consumer import handler as h

    eid = "44444444-4444-4444-4444-444444444444"
    h.handler(_event(_detail("oVal", eid)), None)
    assert fake_redis.get("order:oVal") == eid


def test_invalid_detail_raises(fake_redis):
    from src.consumer import handler as h

    bad_detail = {"order_id": "x"}
    with pytest.raises(Exception):  # noqa: B017
        h.handler(_event(bad_detail), None)


def test_redis_failure_raises(monkeypatch):
    from src.consumer import handler as h

    class BoomRedis:
        def set(self, *a, **kw):
            raise RuntimeError("redis down")

    monkeypatch.setattr(h, "_redis", BoomRedis())
    with pytest.raises(RuntimeError, match="redis down"):
        h.handler(_event(_detail("oFail")), None)


def test_detail_can_be_dict(fake_redis):
    from src.consumer import handler as h

    result = h.handler(_event(_detail("oDict")), None)
    assert result["status"] == "processed"


def test_ttl_respects_env_var(monkeypatch):
    monkeypatch.setenv("REDIS_TTL_SECONDS", "60")
    # Reload module so REDIS_TTL_SECONDS is re-read at import time
    import src.consumer.handler as h

    importlib.reload(h)

    fr = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(h, "_redis", fr)

    h.handler(_event(_detail("oTTL")), None)
    ttl = fr.ttl("order:oTTL")
    assert 0 < ttl <= 60

    # Reload back to default to avoid leaking state
    monkeypatch.delenv("REDIS_TTL_SECONDS", raising=False)
    importlib.reload(h)
