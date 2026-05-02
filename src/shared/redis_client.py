from __future__ import annotations

import os

import redis


def get_redis_client(
    host: str | None = None, port: int | None = None
) -> redis.Redis:
    resolved_host: str = host or os.environ.get("REDIS_HOST") or "localhost"
    resolved_port: int = port or int(os.environ.get("REDIS_PORT") or "6379")
    return redis.Redis(
        host=resolved_host,
        port=resolved_port,
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
