# src/shared/ — Cross-Lambda Code

Two modules. Both load-bearing — every behavior change here ripples to producer + consumer.

## events.py — Pydantic v2 contracts

- `OrderCreated` is the canonical event; `OrderItem` is nested
- `event_id: UUID` auto-generated via `default_factory=uuid4` — used as the dedup token
- `timestamp: datetime` UTC-aware via `default_factory=lambda: datetime.now(UTC)`
- `currency` validator UPPERCASES — incoming `"usd"` becomes `"USD"` (tested invariant)
- Serialize for EventBridge: `order.to_eventbridge_detail()` → JSON string (Pydantic handles `Decimal`/`UUID`/`datetime`)
- Deserialize in consumer: `OrderCreated.from_eventbridge_detail(event["detail"])` — accepts `dict` OR `str`

## redis_client.py — SET NX dedup primitive

- `claim_idempotency_key(client, order_id, event_id, ttl_seconds) -> bool`
- Uses `client.set(key, value, nx=True, ex=ttl_seconds)` — **single atomic round-trip**, no GET-then-SET race
- Key format: `f"order:{order_id}"` — order_id is the dedup unit (NOT event_id; same order republished = duplicate)
- Returns `True` only on first claim (`set` returns `True` when NX succeeds, `None` otherwise)
- Connection: `decode_responses=True`, `socket_timeout=2`, `socket_connect_timeout=2` — fail fast on Redis unreachable
- Host/port from args > `REDIS_HOST`/`REDIS_PORT` env > `localhost:6379`

## Forbidden

- **NEVER** swap `nx=True, ex=...` for separate `EXISTS`+`SET` — kills atomicity
- **NEVER** add Pydantic `model_config` with `frozen=True` — events serialize through `model_dump_json()`; freezing isn't needed and breaks future mutation in tests
- **NEVER** widen `from_eventbridge_detail` to accept `bytes` — EventBridge always delivers `dict` post-Lambda parse
- **NEVER** drop `socket_timeout` — test for Redis-down hangs the consumer Lambda otherwise

## When changing schema

- Bump field constraints together with tests in `tests/unit/test_events.py`
- New required field = breaking; producer + consumer + fixtures must change in same commit
- Adding optional field with default = safe; old events still validate
