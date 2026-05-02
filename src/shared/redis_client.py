from __future__ import annotations

import os

import redis


def get_redis_client(
    host: str | None = None, port: int | None = None
) -> redis.Redis:
    host = host or os.environ.get("REDIS_HOST", "localhost")
    port = port or int(os.environ.get("REDIS_PORT", "6379"))
    return redis.Redis(
        host=host,
        port=port,
        decode_responses=True,
        socket_timeout=2,
        socket_connect_timeout=2,
    )


def claim_idempotency_key(
    client: redis.Redis, order_id: str, event_id: str, ttl_seconds: int
) -> bool:
    """Atomically claim dedup key.

    Returns True if first claim, False if duplicate.
    """
    key = f"order:{order_id}"
    # SET NX EX is atomic — single round-trip dedup primitive
    result = client.set(key, event_id, nx=True, ex=ttl_seconds)
    return result is True
