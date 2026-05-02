import pytest
import redis as redis_lib

pytestmark = pytest.mark.integration

REDIS_HOST = "localhost.localstack.cloud"
REDIS_PORT = 4510


@pytest.fixture(scope="module")
def r():
    """Real Redis client pointing at LocalStack ElastiCache."""
    try:
        client = redis_lib.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=5,
        )
        client.ping()
    except Exception as e:
        pytest.skip(
            f"LocalStack Redis unavailable at {REDIS_HOST}:{REDIS_PORT}: {e}"
        )
    yield client
    # Cleanup all test keys
    for key in client.keys("order:test-*"):
        client.delete(key)


def _claim(r, order_id, event_id, ttl=60):
    """Thin wrapper matching claim_idempotency_key in shared.redis_client."""
    key = f"order:{order_id}"
    return r.set(key, event_id, nx=True, ex=ttl)


def test_set_nx_first_call_returns_true(r):
    r.delete("order:test-1")
    result = _claim(r, "test-1", "evt-1", 60)
    assert result is True


def test_set_nx_second_call_returns_false(r):
    r.delete("order:test-2")
    _claim(r, "test-2", "evt-2a", 60)
    result = _claim(r, "test-2", "evt-2b", 60)
    assert (
        result is None or result is False
    )  # redis-py returns None on NX failure


def test_ttl_is_set(r):
    r.delete("order:test-3")
    _claim(r, "test-3", "evt-3", 60)
    ttl = r.ttl("order:test-3")
    assert 1 <= ttl <= 60


def test_distinct_keys_independent(r):
    r.delete("order:test-4a")
    r.delete("order:test-4b")
    r1 = _claim(r, "test-4a", "evt-4a", 60)
    r2 = _claim(r, "test-4b", "evt-4b", 60)
    assert r1 is True
    assert r2 is True


def test_value_stored_is_event_id(r):
    r.delete("order:test-5")
    _claim(r, "test-5", "evt-5", 60)
    assert r.get("order:test-5") == "evt-5"
